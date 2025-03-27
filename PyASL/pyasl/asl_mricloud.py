import os
import re
import glob
import numpy as np
import nibabel as nib
from nipype.interfaces import spm
from scipy.ndimage import binary_fill_holes, binary_erosion, binary_dilation, label
from skimage.morphology import ball
from scipy.optimize import curve_fit
from pyasl.utils.utils import read_data_description, load_img


def img_rescale(source_path: str, target_path: str):
    img, data = load_img(source_path)
    header = img.header

    slope, _ = header.get_slope_inter()
    ss = slope if slope is not None else 1.0
    data = data / ss / ss

    rescaled_img = nib.Nifti1Image(data, img.affine, img.header)
    rescaled_img.set_data_dtype(np.float32)
    rescaled_img.header["scl_slope"] = 1
    rescaled_img.header["scl_inter"] = 0
    rescaled_img.header["descrip"] = "4D rescaled images"

    rescaled_img.to_filename(target_path)


def mricloud_rescale(data_descrip: dict):
    print("MRICloud: Rescale ASL data...")
    for key, value in data_descrip["Images"].items():
        for asl_file in value["asl"]:
            asl_path = os.path.join(key, "perf", f"{asl_file}.nii")
            asl_der_path = asl_path.replace("rawdata", "derivatives")
            img_rescale(asl_path, asl_der_path)

        if value["M0"]:
            m0_path = os.path.join(key, "perf", f"{value['M0']}.nii")
            m0_der_path = m0_path.replace("rawdata", "derivatives")
            img_rescale(m0_path, m0_der_path)


def mricloud_realign(data_descrip: dict):
    print("MRICloud: Realign ASL data...")

    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")
        for asl_file in value["asl"]:
            P = os.path.join(key, "perf", f"{asl_file}.nii")

            realign = spm.Realign()
            realign.inputs.in_files = P
            realign.inputs.quality = 0.9  # SPM default
            realign.inputs.fwhm = 5
            realign.inputs.register_to_mean = False  # realign to the first timepoint
            realign.inputs.jobtype = "estwrite"
            realign.inputs.interp = 4  # SPM default
            realign.inputs.wrap = [0, 0, 0]  # SPM default
            realign.inputs.write_mask = True
            realign.inputs.write_which = [
                2,
                1,
            ]  # which_writerealign = 2, mean_writerealign = 1
            realign.run()


def mricloud_calculate_diffmap(data_descrip: dict):
    print("MRICloud: Calculate difference volume...")

    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")
        for asl_file in value["asl"]:
            if data_descrip["SingleDelay"]:
                P = os.path.join(key, "perf", f"r{asl_file}.nii")
            else:
                P = os.path.join(key, "perf", f"{asl_file}.nii")
            img, data = load_img(P)
            num_pairs = 0
            ctrl = np.zeros(data.shape[:3])
            labl = np.zeros(data.shape[:3])
            for i, volume_type in enumerate(data_descrip["ASLContext"]):
                if volume_type == "label":
                    labl += data[:, :, :, i]
                    num_pairs += 1
                elif volume_type == "control":
                    ctrl += data[:, :, :, i]
            ctrl /= num_pairs
            labl /= num_pairs
            diff = ctrl - labl

            affine = img.affine
            header = img.header.copy()
            header.set_data_dtype(np.float32)
            header["dim"] = [3] + list(ctrl.shape) + [1] * 4
            header["pixdim"] = list(header["pixdim"][:4]) + [1] * 4
            ctrl_img = nib.Nifti1Image(ctrl, affine, header)
            labl_img = nib.Nifti1Image(labl, affine, header)
            diff_img = nib.Nifti1Image(diff, affine, header)
            ctrl_img.header["descrip"] = "3D control image"
            labl_img.header["descrip"] = "3D label image"
            diff_img.header["descrip"] = "3D difference image"

            ctrl_img.to_filename(os.path.join(key, "perf", f"r{asl_file}_ctrl.nii"))
            labl_img.to_filename(os.path.join(key, "perf", f"r{asl_file}_labl.nii"))
            diff_img.to_filename(os.path.join(key, "perf", f"r{asl_file}_diff.nii"))


def img_coreg(target: str, source: str, other=[]):
    coreg = spm.Coregister()
    coreg.inputs.target = target
    coreg.inputs.source = source
    coreg.inputs.cost_function = "nmi"
    coreg.inputs.separation = [4, 2]
    coreg.inputs.tolerance = [
        0.02,
        0.02,
        0.02,
        0.001,
        0.001,
        0.001,
        0.01,
        0.01,
        0.01,
        0.001,
        0.001,
        0.001,
    ]
    coreg.inputs.fwhm = [7, 7]
    coreg.inputs.write_interp = 1  # trilinear
    coreg.inputs.write_wrap = [0, 0, 0]
    coreg.inputs.write_mask = False
    coreg.inputs.out_prefix = "r"

    if len(other):
        coreg.inputs.apply_to_files = other

    coreg.run()


def mricloud_inbrain(imgvol: np.ndarray, thre: float, ero_lyr: int, dlt_lyr: int):
    lowb = 0.25
    highb = 0.75

    Nx, Ny, Nz = imgvol.shape
    tmpmat = imgvol[
        round(Nx * lowb) : round(Nx * highb),
        round(Ny * lowb) : round(Ny * highb),
        round(Nz * lowb) : round(Nz * highb),
    ]
    tmpvox = tmpmat[tmpmat > 0]
    thre0 = np.mean(tmpvox) * thre

    mask1 = np.zeros_like(imgvol)
    mask1[imgvol > thre0] = 1

    mask2 = np.zeros_like(mask1)
    se = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    for ii in range(Nz):
        slice0 = mask1[:, :, ii]
        slice1 = slice0
        for ie in range(ero_lyr):
            slice1 = binary_erosion(slice1, structure=se)

        labeled_array, num_features = label(slice1, structure=se)
        sizes = np.bincount(labeled_array.ravel())
        sizes[0] = 0
        max_label = sizes.argmax()
        slice2 = np.zeros_like(slice1)
        slice2[labeled_array == max_label] = 1

        slice2 = binary_fill_holes(slice2)
        for id in range(dlt_lyr):
            slice2 = binary_dilation(slice2, structure=se)

        mask2[:, :, ii] = slice2

    brainmask = mask2.astype(np.uint8)
    return brainmask


def mricloud_getBrainMask(imgtpm: str, imgfile: str):
    imgpath, filename = os.path.split(imgfile)
    V, imgvol = load_img(imgfile)
    matsiz = imgvol.shape
    voxsiz = np.abs(V.affine.diagonal()[:3])
    fov = np.multiply(matsiz, voxsiz)
    flag_small_fov = (np.sum(fov < 80) > 0) or (np.sum(np.array(matsiz) < 9) > 0)

    brnmsk_realign = np.ones(matsiz) > 0.5
    if not flag_small_fov:
        segment = spm.NewSegment()
        segment.inputs.channel_files = imgfile
        segment.inputs.channel_info = (0.001, 60, (False, False))
        segment.inputs.tissues = [
            ((imgtpm, 1), 1, (True, False), (False, False)),
            ((imgtpm, 2), 1, (True, False), (False, False)),
            ((imgtpm, 3), 2, (True, False), (False, False)),
            ((imgtpm, 4), 3, (False, False), (False, False)),
            ((imgtpm, 5), 4, (False, False), (False, False)),
            ((imgtpm, 6), 2, (False, False), (False, False)),
        ]
        segment.inputs.warping_regularization = [0, 0.001, 0.5, 0.05, 0.2]
        segment.inputs.affine_regularization = "mni"
        segment.inputs.sampling_distance = 3
        segment.inputs.write_deformation_fields = [False, False]

        segment.run()

        P = glob.glob(os.path.join(imgpath, f"c*{filename}"))
        V = [nib.load(p) for p in P[:3]]
        mvol = np.stack([v.get_fdata() for v in V], axis=-1)
        mask = np.sum(mvol, axis=-1)

        mask = mask > 0.5
        for ss in range(mask.shape[2]):
            mask[:, :, ss] = binary_fill_holes(mask[:, :, ss])

        se = ball(1)
        mask1 = binary_erosion(mask, se)
        brnmsk_clcu = mask1 & brnmsk_realign
        brnmsk_dspl = mask & brnmsk_realign
    else:
        thre = 0.5
        mask1 = mricloud_inbrain(imgvol, thre, 2, 1)
        mask2 = mricloud_inbrain(imgvol, thre, 2, 2)
        brnmsk_clcu = mask1 & brnmsk_realign
        brnmsk_dspl = mask2 & brnmsk_realign

    return brnmsk_dspl, brnmsk_clcu


def mricloud_bgs_factor(
    mz0: float, t1_tissue: float, flip: list, timing: list, inv_eff: float
):
    mz = mz0
    for ii in range(len(flip) - 1):
        slot = np.arange(1, timing[ii + 1] - timing[ii] + 1)
        if abs(flip[ii] - np.pi) < 1e-6:
            ff = 2 * inv_eff - 1
        else:
            ff = 1

        mztmp = 1 + (mz * np.cos(flip[ii]) * ff - 1) * np.exp(-slot / t1_tissue)
        mz = mztmp[-1]

    return mz


def mricloud_calculate_M0(data_descrip: dict, t1_tissue: float, bgs_eff):
    print("MRICloud: Calculate M0...")

    current_dir = os.path.dirname(__file__)
    imgtpm = os.path.join(current_dir, "tpm", "TPM.nii")

    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")

        asl_file = value["asl"][0]
        P_ctrl = os.path.join(key, "perf", f"r{asl_file}_ctrl.nii")
        V_ctrl, ctrlvol = load_img(P_ctrl)
        ctrlsiz = ctrlvol.shape

        if data_descrip["M0Type"] != "Estimate":
            if value["M0"]:
                P_m0 = os.path.join(key, "perf", f"{value['M0']}.nii")
                V_m0, m0all = load_img(P_m0)
                if m0all.ndim == 4:
                    m0map = np.mean(m0all, axis=3)
                else:
                    m0map = m0all
                header = V_m0.header.copy()
                header.set_data_dtype(np.float32)
                header["dim"] = [3] + list(m0map.shape) + [1] * 4
                header["pixdim"] = list(header["pixdim"][:4]) + [1] * 4
                m0map_img = nib.Nifti1Image(m0map, V_m0.affine, header)
                m0siz = m0map.shape
                m0path = os.path.join(key, "perf", "M0ave.nii")
                m0map_img.to_filename(m0path)

            else:
                P = os.path.join(key, "perf", f"{value['asl'][0]}.nii")
                V, data = load_img(P)
                num_m0 = 0
                m0map = np.zeros(data.shape[:3])
                for i, volume_type in enumerate(data_descrip["ASLContext"]):
                    if volume_type == "m0scan":
                        m0map += data[:, :, :, i]
                        num_m0 += 1
                m0map /= num_m0
                header = V.header.copy()
                header.set_data_dtype(np.float32)
                header["dim"] = [3] + list(m0map.shape) + [1] * 4
                header["pixdim"] = list(header["pixdim"][:4]) + [1] * 4
                m0map_img = nib.Nifti1Image(m0map, V.affine, header)

                m0siz = m0map.shape
                m0path = os.path.join(key, "perf", "M0ave.nii")
                m0map_img.to_filename(m0path)

            if np.array_equal(ctrlsiz, m0siz):
                target = os.path.join(key, "perf", f"mean{asl_file}.nii")
                img_coreg(target, m0path)

                P_rm0 = os.path.join(key, "perf", "rM0ave.nii")
                V_rm0, rm0vol = load_img(P_rm0)

                brnmsk_dspl, brnmsk_clcu = mricloud_getBrainMask(imgtpm, P_rm0)
                m0map_final = rm0vol * brnmsk_dspl.astype(float)

            else:
                _, brnmsk1_clcu = mricloud_getBrainMask(imgtpm, m0path)
                brnmsk_dspl, brnmsk_clcu = mricloud_getBrainMask(imgtpm, P_ctrl)
                m0_glo = np.mean(m0map[brnmsk1_clcu])
                m0map_final = brnmsk_dspl.astype(float) * m0_glo
        else:
            m0tmp = np.zeros_like(ctrlvol)
            nslice = ctrlvol.shape[2]
            if data_descrip["ArterialSpinLabelingType"] == "PCASL":
                totdur = (
                    data_descrip["LabelingDuration"] * 1000
                    + list(
                        set([x * 1000.0 for x in data_descrip["PLDList"] if x != 0])
                    )[0]
                )
            elif data_descrip["ArterialSpinLabelingType"] == "PASL":
                totdur = (
                    data_descrip["BolusCutOffDelayTime"] * 1000
                    + list(
                        set([x * 1000.0 for x in data_descrip["PLDList"] if x != 0])
                    )[0]
                )
            for kk in range(nslice):
                if not data_descrip["BackgroundSuppression"]:
                    if data_descrip["MRAcquisitionType"] == "2D":
                        timing = [
                            0,
                            totdur + data_descrip["SliceDuration"] * 1000 * (kk - 1),
                        ]
                    else:
                        timing = [0, totdur]
                    flip = [0, 0]
                    bgs_f = mricloud_bgs_factor(0.0, t1_tissue, flip, timing, 1)
                else:
                    if data_descrip["MRAcquisitionType"] == "2D":
                        timing = (
                            [0]
                            + [
                                x * 1000
                                for x in data_descrip["BackgroundSuppressionPulseTime"][
                                    :-1
                                ]
                            ]
                            + [
                                data_descrip["BackgroundSuppressionPulseTime"][-1]
                                * 1000
                                + data_descrip["SliceDuration"] * 1000 * (kk - 1)
                            ]
                        )
                    else:
                        timing = (
                            [0]
                            + [
                                x * 1000
                                for x in data_descrip["BackgroundSuppressionPulseTime"][
                                    :-1
                                ]
                            ]
                            + [
                                data_descrip["BackgroundSuppressionPulseTime"][-1]
                                * 1000
                            ]
                        )
                    flip = (
                        [0]
                        + [np.pi]
                        * (len(data_descrip["BackgroundSuppressionPulseTime"]) - 1)
                        + [0]
                    )
                    bgs_f = mricloud_bgs_factor(
                        0.0,
                        t1_tissue,
                        flip,
                        timing,
                        bgs_eff,
                    )
                m0tmp[:, :, kk] = ctrlvol[:, :, kk] / bgs_f

            brnmsk_dspl, brnmsk_clcu = mricloud_getBrainMask(imgtpm, P_ctrl)
            m0_glo = np.mean(m0tmp[brnmsk_clcu])
            m0map_final = brnmsk_dspl.astype(float) * m0_glo

        header = V_ctrl.header.copy()
        header.set_data_dtype(np.float32)
        m0map_final_img = nib.Nifti1Image(m0map_final, V_ctrl.affine, header)
        m0map_final_img.header["descrip"] = b"mricloud_pipeline"
        m0map_final_img.to_filename(os.path.join(key, "perf", "M0map.nii"))
        header.set_data_dtype(np.int16)
        brnmsk_dspl_img = nib.Nifti1Image(brnmsk_dspl, V_ctrl.affine, header)
        brnmsk_dspl_img.header["descrip"] = b"mricloud_pipeline"
        brnmsk_dspl_img.to_filename(os.path.join(key, "perf", "brnmsk_dspl.nii"))
        brnmsk_clcu_img = nib.Nifti1Image(brnmsk_clcu, V_ctrl.affine, header)
        brnmsk_clcu_img.header["descrip"] = b"mricloud_pipeline"
        brnmsk_clcu_img.to_filename(os.path.join(key, "perf", "brnmsk_clcu.nii"))


def mricloud_calculate_CBF(
    data_descrip: dict, t1_blood: float, part_coef: float, bgs_eff
):
    print("MRICloud: Calculate CBF...")

    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")
        for asl_file in value["asl"]:
            V_diff, diff = load_img(os.path.join(key, "perf", f"r{asl_file}_diff.nii"))
            V_m0map, m0map = load_img(os.path.join(key, "perf", "M0map.nii"))
            V_brnmsk_dspl, brnmsk_dspl = load_img(
                os.path.join(key, "perf", "brnmsk_dspl.nii")
            )
            V_brnmsk_clcu, brnmsk_clcu = load_img(
                os.path.join(key, "perf", "brnmsk_clcu.nii")
            )
            brnmsk_dspl = brnmsk_dspl.astype(bool)
            brnmsk_clcu = brnmsk_clcu.astype(bool)

            tmpcbf = np.zeros_like(diff)
            nslice = tmpcbf.shape[2]

            for kk in range(nslice):
                if data_descrip["ArterialSpinLabelingType"] == "PCASL":
                    casl_pld = list(
                        set([x * 1000.0 for x in data_descrip["PLDList"] if x != 0])
                    )[0]
                    if data_descrip["MRAcquisitionType"] == "3D":
                        spld = casl_pld
                    else:
                        spld = casl_pld + data_descrip["SliceDuration"] * 1000 * (
                            kk - 1
                        )
                    tmpcbf[:, :, kk] = (
                        diff[:, :, kk]
                        * np.exp(spld / t1_blood)
                        / (
                            1
                            - np.exp(
                                -data_descrip["LabelingDuration"] * 1000 / t1_blood
                            )
                        )
                        / t1_blood
                    )

                elif data_descrip["ArterialSpinLabelingType"] == "PASL":
                    pasl_ti = (
                        list(
                            set([x * 1000.0 for x in data_descrip["PLDList"] if x != 0])
                        )[0]
                        + data_descrip["BolusCutOffDelayTime"] * 1000
                    )
                    if data_descrip["MRAcquisitionType"] == "3D":
                        sti = pasl_ti
                    else:
                        sti = pasl_ti + data_descrip["SliceDuration"] * 1000 * (kk - 1)
                    tmpcbf[:, :, kk] = (
                        diff[:, :, kk]
                        * np.exp(sti / t1_blood)
                        / (data_descrip["BolusCutOffDelayTime"] * 1000)
                    )

            m0map[np.abs(m0map) < 1e-6] = np.mean(m0map[brnmsk_clcu])
            m0vol = m0map.astype(np.float32)
            brvol = brnmsk_dspl.astype(np.float32)
            if data_descrip["BackgroundSuppression"]:
                alpha = (
                    bgs_eff ** data_descrip["BackgroundSuppressionNumberPulses"]
                ) * data_descrip["LabelingEfficiency"]
            else:
                alpha = data_descrip["LabelingEfficiency"]
            cbf = tmpcbf / m0vol * brvol * part_coef / 2 / alpha * 60 * 100 * 1000
            cbf_thr = np.clip(cbf, 0, 200)
            cbf_glo = np.mean(cbf_thr[brnmsk_clcu])
            rcbf_thr = cbf_thr / cbf_glo

            header = V_diff.header.copy()
            acbf_img = nib.Nifti1Image(cbf_thr, V_diff.affine, header)
            acbf_img.header["descrip"] = b"mricloud_pipeline"
            acbf_img.to_filename(
                os.path.join(key, "perf", f"{asl_file}_aCBF_native.nii")
            )
            rcbf_img = nib.Nifti1Image(rcbf_thr, V_diff.affine, header)
            rcbf_img.header["descrip"] = b"mricloud_pipeline"
            rcbf_img.to_filename(
                os.path.join(key, "perf", f"{asl_file}_rCBF_native.nii")
            )


def mricloud_func_recover(
    m0: float, t1: float, tp: np.ndarray, flip_angle=None, m_init=None
):
    if flip_angle is not None and m_init is not None:
        # Look-Locker T1 recovery model
        tis_tmp = np.unique(tp)
        ti_intvl = np.mean(tis_tmp[1:] - tis_tmp[:-1])
        flip_angle = flip_angle / 180 * np.pi
        r1_eff = 1 / t1 - np.log(np.cos(flip_angle)) / ti_intvl
        mss = (
            m0
            * (1 - np.exp(-ti_intvl / t1))
            / (1 - np.exp(-ti_intvl / t1) * np.cos(flip_angle))
        )

        mm = mss * (1 - np.exp(-tp * r1_eff)) * np.sin(flip_angle)

    elif flip_angle is None and m_init is None:
        # Multi-delay T1 recovery model
        mm = m0 * (1 - np.exp(-tp / t1))

    return mm


def mricloud_multidelay_calculate_M0(data_descrip: dict):
    print("MRICloud: Calculate M0...")

    current_dir = os.path.dirname(__file__)
    imgtpm = os.path.join(current_dir, "tpm", "TPM.nii")

    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")

        asl_file = value["asl"][0]
        fn_asl = os.path.join(key, "perf", f"{asl_file}.nii")
        V_asl, img_all = load_img(fn_asl)
        fn_ctrl = os.path.join(key, "perf", f"r{asl_file}_ctrl.nii")
        V_ctrl = nib.load(fn_ctrl)

        if data_descrip["M0Type"] != "Estimate":
            if value["M0"]:
                P_m0 = os.path.join(key, "perf", f"{value['M0']}.nii")
                V_m0, m0all = load_img(P_m0)
                if m0all.ndim == 4:
                    m0map = np.mean(m0all, axis=3)
                else:
                    m0map = m0all
                header = V_m0.header.copy()
                header.set_data_dtype(np.float32)
                header["dim"] = [3] + list(m0map.shape) + [1] * 4
                header["pixdim"] = list(header["pixdim"][:4]) + [1] * 4
                m0map_img = nib.Nifti1Image(m0map, V_m0.affine, header)
                m0path = os.path.join(key, "perf", "M0ave.nii")
                m0map_img.to_filename(m0path)

            else:
                P = os.path.join(key, "perf", f"{value['asl'][0]}.nii")
                V, data = load_img(P)
                num_m0 = 0
                m0map = np.zeros(data.shape[:3])
                for i, volume_type in enumerate(data_descrip["ASLContext"]):
                    if volume_type == "m0scan":
                        m0map += data[:, :, :, i]
                        num_m0 += 1
                m0map /= num_m0
                header = V.header.copy()
                header.set_data_dtype(np.float32)
                header["dim"] = [3] + list(m0map.shape) + [1] * 4
                header["pixdim"] = list(header["pixdim"][:4]) + [1] * 4
                m0map_img = nib.Nifti1Image(m0map, V.affine, header)
                m0path = os.path.join(key, "perf", "M0ave.nii")
                m0map_img.to_filename(m0path)

            target = fn_ctrl
            img_coreg(target, m0path)

            P_rm0 = os.path.join(key, "perf", "rM0ave.nii")
            V_rm0, rm0vol = load_img(P_rm0)

            brnmsk_dspl, brnmsk_clcu = mricloud_getBrainMask(imgtpm, P_rm0)
            m0map_final = rm0vol * brnmsk_dspl.astype(float)
        else:
            brnmsk_dspl, brnmsk_clcu = mricloud_getBrainMask(imgtpm, fn_ctrl)
            ctrl_all_list = []
            plds = []
            for i, volume_type in enumerate(data_descrip["ASLContext"]):
                if volume_type == "label":
                    plds.append(data_descrip["PLDList"][i] * 1000.0)
                elif volume_type == "control":
                    ctrl_all_list.append(img_all[:, :, :, i])
            plds = np.array(plds)
            ctrl_last = ctrl_all_list[-1]
            m0_int = np.mean(ctrl_last[brnmsk_clcu])
            ctrl_all = np.stack(ctrl_all_list, axis=-1)
            ctrl_all = ctrl_all.reshape(-1, ctrl_all.shape[-1])
            idx_msk = np.where(brnmsk_dspl)
            m0_map = np.zeros_like(ctrl_last)

            if data_descrip["ArterialSpinLabelingType"] == "PCASL":
                ff = lambda x, m0, t1: mricloud_func_recover(m0, t1, x)
                beta_init = [m0_int, 1165]
                lowb = [0, 0]
                uppb = [10 * m0_int, 5000]

                for ivox in zip(*idx_msk):
                    islc = ivox[2]
                    if data_descrip["MRAcquisitionType"] == "3D":
                        xdata = plds + data_descrip["LabelingDuration"] * 1000
                    else:
                        xdata = (
                            plds
                            + data_descrip["LabelingDuration"] * 1000
                            + (islc - 1) * data_descrip["SliceDuration"] * 1000
                        )
                    ydata = ctrl_all[np.ravel_multi_index(ivox, brnmsk_dspl.shape), :]
                    beta1, _ = curve_fit(
                        ff, xdata, ydata, p0=beta_init, bounds=(lowb, uppb)
                    )
                    m0_map[ivox] = beta1[0]

            elif data_descrip["ArterialSpinLabelingType"] == "PASL":
                ff = lambda x, m0, t1, m_init: mricloud_func_recover(
                    m0, t1, x, data_descrip["Looklocker"], m_init
                )
                beta_init = [m0_int, 1165, 0]
                lowb = [0, 0, -10 * m0_int]
                uppb = [10 * m0_int, 5000, 5 * m0_int]

                for ivox in zip(*idx_msk):
                    islc = ivox[2]
                    if data_descrip["MRAcquisitionType"] == "3D":
                        xdata = plds + data_descrip["BolusCutOffDelayTime"] * 1000
                    else:
                        xdata = (
                            plds
                            + data_descrip["BolusCutOffDelayTime"] * 1000
                            + (islc - 1) * data_descrip["SliceDuration"] * 1000
                        )
                    ydata = ctrl_all[np.ravel_multi_index(ivox, brnmsk_dspl.shape), :]
                    beta1, _ = curve_fit(
                        ff, xdata, ydata, p0=beta_init, bounds=(lowb, uppb)
                    )
                    m0_map[ivox] = beta1[0]

            m0map_final = m0_map * brnmsk_dspl.astype(float)

        header = V_ctrl.header.copy()
        header.set_data_dtype(np.float32)
        m0map_final_img = nib.Nifti1Image(m0map_final, V_ctrl.affine, header)
        m0map_final_img.header["descrip"] = b"mricloud_pipeline"
        m0map_final_img.to_filename(os.path.join(key, "perf", "M0map.nii"))
        header.set_data_dtype(np.int16)
        brnmsk_dspl_img = nib.Nifti1Image(brnmsk_dspl, V_ctrl.affine, header)
        brnmsk_dspl_img.header["descrip"] = b"mricloud_pipeline"
        brnmsk_dspl_img.to_filename(os.path.join(key, "perf", "brnmsk_dspl.nii"))
        brnmsk_clcu_img = nib.Nifti1Image(brnmsk_clcu, V_ctrl.affine, header)
        brnmsk_clcu_img.header["descrip"] = b"mricloud_pipeline"
        brnmsk_clcu_img.to_filename(os.path.join(key, "perf", "brnmsk_clcu.nii"))


def mricloud_func_gkm_pcasl_multidelay(
    cbf: float, att: float, casl_dur: float, plds: np.ndarray, paras: dict
):
    t1_blood = paras["t1_blood"]
    part_coef = paras["part_coef"]
    labl_eff = paras["labl_eff"]

    t1_app = t1_blood

    const = 2 * labl_eff * cbf * t1_app / part_coef / 6000

    w1 = plds[(plds + casl_dur) < att]
    w2 = plds[((plds + casl_dur) >= att) & (plds < att)]
    w3 = plds[plds >= att]

    m1 = np.zeros_like(w1)
    m2 = np.exp(0 / t1_app) - np.exp((att - casl_dur - w2) / t1_app)
    m3 = np.exp((att - w3) / t1_app) - np.exp((att - casl_dur - w3) / t1_app)

    m2 = const * np.exp(-att / t1_blood) * m2
    m3 = const * np.exp(-att / t1_blood) * m3

    mm = np.concatenate((m1, m2, m3))

    return mm


def mricloud_func_gkm_pasl_looklocker(
    cbf: float,
    att: float,
    pasl_dur: float,
    tis: np.ndarray,
    flip_angle: float,
    paras: dict,
):
    t1_blood = paras["t1_blood"]
    part_coef = paras["part_coef"]
    labl_eff = paras["labl_eff"]

    t_tail = att + pasl_dur
    t1_app = t1_blood

    flip_angle = flip_angle / 180 * np.pi
    tis_tmp = np.unique(tis)
    ti_intvl = np.mean(tis_tmp[1:] - tis_tmp[:-1])

    r1_blood = 1 / t1_blood
    r1_app = 1 / t1_app
    r1_appeff = r1_app - np.log(np.cos(flip_angle)) / ti_intvl
    delta_r = r1_blood - r1_appeff

    const = 2 * labl_eff * cbf / part_coef / 6000 / delta_r

    w1 = tis[tis < att]
    w2 = tis[(tis >= att) & (tis < t_tail)]
    w3 = tis[tis >= t_tail]

    m1 = np.zeros_like(w1)
    m2 = -(1 - np.exp(delta_r * (w2 - att))) * np.exp(-w2 * r1_blood)
    m3 = (
        -(1 - np.exp(delta_r * (w3 - att)))
        * np.exp(-t_tail * r1_blood)
        * np.exp(-r1_appeff * (w3 - t_tail))
    )

    m2 = const * m2 * np.sin(flip_angle)
    m3 = const * m3 * np.sin(flip_angle)

    mm = np.concatenate((m1, m2, m3))

    return mm


def mricloud_multidelay_calculate_CBFATT(
    data_descrip: dict, t1_blood: float, part_coef: float
):
    print("MRICloud: Calculate CBF and ATT...")

    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")
        for asl_file in value["asl"]:
            V_asl, img_all = load_img(os.path.join(key, "perf", f"{asl_file}.nii"))
            V_m0map, m0map = load_img(os.path.join(key, "perf", "M0map.nii"))
            V_dspl, brnmsk_dspl = load_img(os.path.join(key, "perf", "brnmsk_dspl.nii"))
            V_clcu, brnmsk_clcu = load_img(os.path.join(key, "perf", "brnmsk_clcu.nii"))
            brnmsk_dspl = brnmsk_dspl.astype(bool)
            brnmsk_clcu = brnmsk_clcu.astype(bool)

            ctrl = []
            labl = []
            for i, volume_type in enumerate(data_descrip["ASLContext"]):
                if volume_type == "label":
                    labl.append(img_all[:, :, :, i])
                elif volume_type == "control":
                    ctrl.append(img_all[:, :, :, i])
            ctrl = np.stack(ctrl, axis=-1)
            labl = np.stack(labl, axis=-1)
            diff = ctrl - labl

            brnmsk1 = np.tile(brnmsk_dspl[..., np.newaxis], (1, 1, 1, diff.shape[3]))
            m0map1 = np.tile(m0map[..., np.newaxis], (1, 1, 1, diff.shape[3]))
            idx_msk = np.where(brnmsk_dspl)
            idx_msk1 = np.where(brnmsk1)

            ndiff = np.zeros_like(diff)
            ndiff[idx_msk1] = diff[idx_msk1] / m0map1[idx_msk1]
            ndiff = ndiff.reshape(-1, diff.shape[3])

            plds = []
            for i, volume_type in enumerate(data_descrip["ASLContext"]):
                if volume_type == "label":
                    plds.append(data_descrip["PLDList"][i] * 1000.0)
            plds = np.array(plds) / 1000

            paras = {
                "labl_eff": data_descrip["LabelingEfficiency"],
                "t1_blood": t1_blood / 1000,
                "part_coef": part_coef,
            }

            attmap = np.zeros_like(m0map)
            cbfmap = np.zeros_like(m0map)

            if data_descrip["ArterialSpinLabelingType"] == "PCASL":
                ff = lambda x, cbf, att: mricloud_func_gkm_pcasl_multidelay(
                    cbf, att, data_descrip["LabelingDuration"], x, paras
                )
                beta_init = [60, 0.5]
                lowb = [0, 0.1]
                uppb = [200, 3.0]

                for ivox in zip(*idx_msk):
                    islc = ivox[2]
                    if data_descrip["MRAcquisitionType"] == "3D":
                        xdata = plds
                    else:
                        xdata = plds + (islc - 1) * data_descrip["SliceDuration"]
                    ydata = ndiff[np.ravel_multi_index(ivox, brnmsk_dspl.shape), :]
                    beta1, _ = curve_fit(
                        ff,
                        xdata,
                        ydata,
                        p0=beta_init,
                        bounds=(lowb, uppb),
                        maxfev=10000,
                    )
                    cbfmap[ivox] = beta1[0]
                    attmap[ivox] = beta1[1] * 1000

            elif data_descrip["ArterialSpinLabelingType"] == "PASL":
                ff = lambda x, cbf, att: mricloud_func_gkm_pasl_looklocker(
                    cbf,
                    att,
                    data_descrip["BolusCutOffDelayTime"],
                    x,
                    data_descrip["Looklocker"],
                    paras,
                )
                beta_init = [60, 0.5]
                lowb = [0, 0.1]
                uppb = [200, 3.0]

                for ivox in zip(*idx_msk):
                    islc = ivox[2]
                    if data_descrip["MRAcquisitionType"] == "3D":
                        xdata = plds + data_descrip["BolusCutOffDelayTime"]
                    else:
                        xdata = (
                            plds
                            + data_descrip["BolusCutOffDelayTime"]
                            + (islc - 1) * data_descrip["SliceDuration"]
                        )
                    ydata = ndiff[np.ravel_multi_index(ivox, brnmsk_dspl.shape), :]
                    beta1, _ = curve_fit(
                        ff, xdata, ydata, p0=beta_init, bounds=(lowb, uppb)
                    )
                    cbfmap[ivox] = beta1[0]
                    attmap[ivox] = beta1[1] * 1000

            cbf_glo = np.mean(cbfmap[brnmsk_clcu])
            rcbfmap = cbfmap / cbf_glo

            header = V_m0map.header.copy()
            affine = V_m0map.affine.copy()
            acbf_img = nib.Nifti1Image(cbfmap, affine, header)
            acbf_img.header["descrip"] = b"mricloud_pipeline"
            acbf_img.to_filename(
                os.path.join(key, "perf", f"{asl_file}_aCBF_native.nii")
            )
            rcbf_img = nib.Nifti1Image(rcbfmap, affine, header)
            rcbf_img.header["descrip"] = b"mricloud_pipeline"
            rcbf_img.to_filename(
                os.path.join(key, "perf", f"{asl_file}_rCBF_native.nii")
            )
            att_img = nib.Nifti1Image(attmap, affine, header)
            att_img.header["descrip"] = b"mricloud_pipeline"
            att_img.to_filename(os.path.join(key, "perf", f"{asl_file}_ATT_native.nii"))


def mricloud_read_mpr(data_descrip: dict):
    for key, value in data_descrip["Images"].items():
        key_der = key.replace("rawdata", "derivatives")
        if not value["anat"]:
            raise ValueError("Missing structural images for multi-atlas analysis!")
        anat_path = os.path.join(key_der, "anat")
        entries = os.listdir(anat_path)
        directories = [
            entry for entry in entries if os.path.isdir(os.path.join(anat_path, entry))
        ]
        mpr_folder = None
        mpr_name = None
        for dir in directories:
            if os.path.exists(os.path.join(anat_path, dir, "mni.imgsize")):
                mpr_folder = dir
                regex = re.compile(r"^(?!mni).+\.imgsize$")
                files = [
                    f
                    for f in os.listdir(os.path.join(anat_path, dir))
                    if re.match(regex, f)
                ]
                mpr_file = files[0]
                mpr_name = mpr_file[:-8]
                break
        if mpr_folder is None:
            raise ValueError("Missing parcellation folder for multi-atlas analysis!")
        data_descrip["Images"][key]["mpr_folder"] = mpr_folder
        data_descrip["Images"][key]["mpr_name"] = mpr_name

    return data_descrip


def mricloud_read_roi_lookup_table(roi_lookup_file: str):
    with open(roi_lookup_file, "r") as file:
        titles = file.readline()
        data = [line.split() for line in file]
    return data


def mricloud_skullstrip(path_mpr: str, name_mpr: str):
    mVol, mpr = load_img(os.path.join(path_mpr, f"{name_mpr}.img"))
    roi_lookup_all = mricloud_read_roi_lookup_table(
        os.path.join(path_mpr, "multilevel_lookup_table.txt")
    )
    label_num = len(roi_lookup_all)
    regex = re.compile(rf"^{name_mpr}.*{label_num}.*(?<!MNI)\.img$")
    files = [f for f in os.listdir(path_mpr) if re.match(regex, f)]
    roimaskfile = files[0]
    maskvol, allmask = load_img(os.path.join(path_mpr, roimaskfile))
    brainmask = np.zeros_like(allmask)
    for ii in range(label_num):
        if len(roi_lookup_all[ii]) > 4:
            brainmask[allmask == (ii + 1)] = 1
    mpr_brain_data = mpr * brainmask
    mpr_brain_img = nib.Nifti1Image(mpr_brain_data, mVol.affine, mVol.header)
    mpr_brain_img.header["descrip"] = b"mricloud_pipeline"
    mpr_brain_file = os.path.join(path_mpr, f"{name_mpr}_brain.nii")
    mpr_brain_img.to_filename(mpr_brain_file)
    return mpr_brain_file


def mricloud_coreg_mpr(data_descrip: dict):
    print("MRICloud: Coregister ASL data to structural image...")
    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")
        target = mricloud_skullstrip(
            os.path.join(key, "anat", value["mpr_folder"]), value["mpr_name"]
        )
        for asl_file in value["asl"]:
            if data_descrip["M0Type"] != "Estimate":
                source = os.path.join(key, "perf", "rM0ave.nii")
            else:
                source = os.path.join(key, "perf", f"mean{asl_file}.nii")
            other1 = os.path.join(key, "perf", f"{asl_file}_aCBF_native.nii")
            other2 = os.path.join(key, "perf", f"{asl_file}_rCBF_native.nii")
            other3 = os.path.join(key, "perf", "brnmsk_clcu.nii")
            other4 = os.path.join(key, "perf", f"{asl_file}_ATT_native.nii")
            if data_descrip["SingleDelay"]:
                img_coreg(target, source, [other1, other2, other3])
            else:
                img_coreg(target, source, [other1, other2, other3, other4])
            os.rename(
                os.path.join(key, "perf", f"r{asl_file}_aCBF_native.nii"),
                os.path.join(key, "perf", f"{asl_file}_aCBF_mpr.nii"),
            )
            os.rename(
                os.path.join(key, "perf", f"r{asl_file}_rCBF_native.nii"),
                os.path.join(key, "perf", f"{asl_file}_rCBF_mpr.nii"),
            )
            os.rename(
                os.path.join(key, "perf", "rbrnmsk_clcu.nii"),
                os.path.join(key, "perf", "brnmsk_clcu_mpr.nii"),
            )
            if os.path.exists(os.path.join(key, "perf", f"r{asl_file}_ATT_native.nii")):
                os.rename(
                    os.path.join(key, "perf", f"r{asl_file}_ATT_native.nii"),
                    os.path.join(key, "perf", f"{asl_file}_ATT_mpr.nii"),
                )


def mricloud_read_roi_lists_info(roi_stats_file: str, roitypes: list):
    with open(roi_stats_file, "r") as file:
        alllines = file.readlines()
    nline = len(alllines)
    tmpinfo = []
    iline = 0
    while iline < nline:
        splitStr = re.split(r"[ \t\b]+", alllines[iline].strip())
        for roi_type in roitypes:
            if splitStr[0] == roi_type:
                tmpdict = {"type": splitStr[0], "count": 0, "list": []}
                iline += 2
                while iline < nline and re.search(r".img", alllines[iline]):
                    tmpdict["count"] += 1
                    splitStr2 = re.split(r"[ \t]+", alllines[iline].strip())
                    if len(splitStr2) > 1:
                        tmpdict["list"].append(splitStr2[1])
                    iline += 1
                tmpinfo.append(tmpdict)
        iline += 1
    return tmpinfo


def mricloud_t1roi_CBFaverage(data_descrip: dict):
    print("MRICloud: Calculate ROI average CBF...")
    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")
        roi_lookup_file = os.path.join(
            key, "anat", value["mpr_folder"], "multilevel_lookup_table.txt"
        )
        roi_lookup_all = mricloud_read_roi_lookup_table(roi_lookup_file)
        label_num = len(roi_lookup_all)
        regex = re.compile(rf'^{value["mpr_name"]}.*{label_num}.*MNI_stats\.txt$')
        files = [
            f
            for f in os.listdir(os.path.join(key, "anat", value["mpr_folder"]))
            if re.match(regex, f)
        ]
        roi_stats_file = files[0]
        roitypes = ["Type1-L2", "Type1-L3", "Type1-L5"]
        roi_lookup_tbl = [4, 3, 1]
        roi_lists_info = mricloud_read_roi_lists_info(
            os.path.join(key, "anat", value["mpr_folder"], roi_stats_file), roitypes
        )
        roi_lists_info[2]["count"] = label_num
        roi_lists_info[2]["list"] = roi_lookup_all

        regex = re.compile(rf'^{value["mpr_name"]}.*{label_num}.*(?<!MNI)\.img$')
        files = [
            f
            for f in os.listdir(os.path.join(key, "anat", value["mpr_folder"]))
            if re.match(regex, f)
        ]
        roimaskfile = files[0]
        V0, mskv = load_img(os.path.join(key, "anat", value["mpr_folder"], roimaskfile))

        for asl_file in value["asl"]:
            V1, acbf = load_img(os.path.join(key, "perf", f"{asl_file}_aCBF_mpr.nii"))
            V2, rcbf = load_img(os.path.join(key, "perf", f"{asl_file}_rCBF_mpr.nii"))
            V3, msk1 = load_img(os.path.join(key, "perf", "brnmsk_clcu_mpr.nii"))

            fresult = os.path.join(key, "perf", f"{asl_file}_CBF_T1segmented_ROIs.txt")
            with open(fresult, "w") as fid:
                coltitle = "ROI analysis by {} major tissue types\n"
                colnames = "Index\tMask_name\tRegional_CBF(ml/100g/min)\tRegional_relative_CBF\tNumber_of_voxels\n"

                for tt in range(len(roi_lists_info) - 1):
                    roi_tbl = roi_lookup_tbl[tt]
                    roi_lst = roi_lists_info[tt]["list"]
                    seg_num = roi_lists_info[tt]["count"]
                    segmask = np.zeros_like(mskv)

                    for ii in range(seg_num):
                        for kk in range(label_num):
                            if len(roi_lookup_all[kk]) <= roi_tbl:
                                continue
                            if roi_lst[ii] == roi_lookup_all[kk][roi_tbl]:
                                segmask[mskv == (kk + 1)] = ii + 1

                    segmask_img = nib.Nifti1Image(segmask, V0.affine, V0.header)
                    segmask_img.header["descrip"] = b"mricloud_pipeline"
                    segmask_img.header.set_data_dtype(np.int32)
                    segmask_img.to_filename(
                        os.path.join(
                            key,
                            "anat",
                            value["mpr_folder"],
                            f"{value['mpr_name']}_{seg_num}_segments.nii",
                        )
                    )

                    fid.write(coltitle.format(seg_num))
                    fid.write(colnames)
                    for ii in range(seg_num):
                        idxvox_seg = np.squeeze(segmask == (ii + 1)) & (msk1 > 0.5)
                        seg_acbf = np.mean(acbf[idxvox_seg])
                        seg_rcbf = np.mean(rcbf[idxvox_seg])
                        seg_nvox = np.sum(idxvox_seg)
                        seg_name = roi_lst[ii]
                        fid.write(
                            f"{ii+1}\t{seg_name}\t{seg_acbf:.2f}\t{seg_rcbf:.2f}\t{seg_nvox}\n"
                        )
                    fid.write("\n\n")

                fid.write(coltitle.format(label_num))
                fid.write(colnames)
                for ii in range(label_num):
                    idxvox_seg = np.squeeze(mskv == (ii + 1)) & (msk1 > 0.5)
                    seg_acbf = np.mean(acbf[idxvox_seg])
                    seg_rcbf = np.mean(rcbf[idxvox_seg])
                    seg_nvox = np.sum(idxvox_seg)
                    seg_name = roi_lists_info[2]["list"][ii][1]
                    fid.write(
                        f"{ii+1}\t{seg_name}\t{seg_acbf:.2f}\t{seg_rcbf:.2f}\t{seg_nvox}\n"
                    )


def mricloud_pipeline(
    root: str,
    flag_t1: bool,
    t1_tissue: float,
    t1_blood: float,
    part_coef: float,
    bgs_eff=None,
):
    print("Process ASL images using MRICloud...")
    data_descrip = read_data_description(root)
    mricloud_rescale(data_descrip)

    if data_descrip["SingleDelay"]:
        mricloud_realign(data_descrip)
        mricloud_calculate_diffmap(data_descrip)
        mricloud_calculate_M0(data_descrip, t1_tissue, bgs_eff)
        mricloud_calculate_CBF(data_descrip, t1_blood, part_coef, bgs_eff)
    else:
        mricloud_calculate_diffmap(data_descrip)
        mricloud_multidelay_calculate_M0(data_descrip)
        mricloud_multidelay_calculate_CBFATT(data_descrip, t1_blood, part_coef)

    if flag_t1:
        data_descrip = mricloud_read_mpr(data_descrip)
        mricloud_coreg_mpr(data_descrip)
        mricloud_t1roi_CBFaverage(data_descrip)

    print("Processing complete!")
    print(f"Please see results under {os.path.join(root,'derivatives')}.")
