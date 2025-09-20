import os
import glob
import numpy as np
import nibabel as nib
from scipy.ndimage import binary_fill_holes, binary_erosion, binary_dilation, label
from skimage.morphology import ball
from nipype.interfaces import spm
from pyasl.utils.utils import load_img

def img_coreg(target: str, source: str, other=[]):
    coreg = spm.Coregister()
    coreg.inputs.target = target
    coreg.inputs.source = source
    coreg.inputs.cost_function = "nmi"
    coreg.inputs.separation = [4, 2]
    coreg.inputs.tolerance = [0.02] * 3 + [0.001] * 3 + [0.01] * 3 + [0.001] * 3
    coreg.inputs.fwhm = [7, 7]
    coreg.inputs.write_interp = 1
    coreg.inputs.write_wrap = [0, 0, 0]
    coreg.inputs.write_mask = False
    coreg.inputs.out_prefix = "r"
    if other:
        coreg.inputs.apply_to_files = other
    coreg.run()

def mricloud_inbrain(imgvol: np.ndarray, thre: float, ero_lyr: int, dlt_lyr: int):
    lowb, highb = 0.25, 0.75
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
        slice1 = mask1[:, :, ii]
        for _ in range(ero_lyr):
            slice1 = binary_erosion(slice1, structure=se)
        labeled_array, _ = label(slice1, structure=se)
        sizes = np.bincount(labeled_array.ravel())
        sizes[0] = 0
        max_label = sizes.argmax()
        slice2 = np.zeros_like(slice1)
        slice2[labeled_array == max_label] = 1
        slice2 = binary_fill_holes(slice2)
        for _ in range(dlt_lyr):
            slice2 = binary_dilation(slice2, structure=se)
        mask2[:, :, ii] = slice2
    return mask2.astype(np.uint8)

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