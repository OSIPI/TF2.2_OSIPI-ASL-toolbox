"""
PerfusionQuantify
-----------------
Calculate CBF maps and related perfusion metrics using ASLtbx logic.
"""


import os
import numpy as np
import nibabel as nib
from pyasl.utils.utils import load_img
import logging
logger = logging.getLogger(__name__)

class PerfusionQuantify:
    """
    PerfusionQuantify
    ----------------
    This class provides methods to calculate cerebral blood flow (CBF) maps and related perfusion metrics
    from ASL (Arterial Spin Labeling) MRI data using ASLtbx-inspired logic.

    Methods
    -------
    run(data_descrip: dict, config: dict)
        Main entry point to perform CBF quantification for all subjects/images described in the dataset.

    asltbx_sinc_interpVec(x: np.ndarray, u: float)
        Perform vectorized sinc interpolation, used for time-shifting ASL time series.

    asltbx_perf_subtract(...)
        Perform pairwise subtraction of label/control images and quantification of perfusion metrics.
    """
    
    def run(self, data_descrip: dict, config: dict):
        """
        Run CBF quantification for all subjects/images.

        Iterates over ASL images in `data_descrip` and computes CBF maps and related metrics
        using parameters from `config`.

        Parameters
        ----------
        data_descrip : dict
            Dataset description with ASL image locations.
        config : dict
            Configuration options for quantification.
        """
        logger.info("ASLtbx: Calculate CBF maps...")

        QuantFlag = config.get("QuantFlag", 1)
        M0wmcsf = config.get("M0wmcsf")
        MaskFlag = config.get("MaskFlag", True)
        MeanFlag = config.get("MeanFlag", True)
        BOLDFlag = config.get("BOLDFlag", False)
        PerfFlag = config.get("PerfFlag", False)
        SubtractionType = config.get("SubtractionType", 0)
        SubtrationOrder = config.get("SubtrationOrder", 1)
        Timeshift = config.get("Timeshift", 0.5)

        self.asltbx_perf_subtract(
            data_descrip,
            QuantFlag,
            M0wmcsf,
            MaskFlag,
            MeanFlag,
            BOLDFlag,
            PerfFlag,
            SubtractionType,
            SubtrationOrder,
            Timeshift,
        )
    
    def asltbx_sinc_interpVec(self, x: np.ndarray, u: float):
        """
        Sinc interpolation of each row in x at position u.

        Parameters
        ----------
        x : np.ndarray
            2D array (dim, lenx) to interpolate.
        u : float
            Interpolation position.

        Returns
        -------
        y : np.ndarray
            Interpolated values for each row.
        """
        dim, lenx = x.shape
        u = np.tile(u, (dim, 1))
        m = np.tile(np.arange(lenx), (dim, 1))
        weight = np.sinc(m - np.tile(u, (1, lenx)))
        swei = np.sum(weight, axis=1)
        if np.abs(swei[0] - 1) > 0.1:
            weight /= np.tile(swei.reshape(dim, 1), (1, lenx))

        y = np.sum(x * weight, axis=1)

        return y

    def asltbx_perf_subtract(
        self,
        data_descrip: dict,
        QuantFlag,
        M0wmcsf,
        MaskFlag,
        MeanFlag,
        BOLDFlag,
        PerfFlag,
        SubtractionType,
        SubtrationOrder,
        Timeshift,
    ):
        """
        Subtracts label and control images to compute perfusion-weighted images.

        Parameters
        ----------
        data_descrip : dict
            Dataset description.
        QuantFlag, M0wmcsf, MaskFlag, MeanFlag, BOLDFlag, PerfFlag, SubtractionType, SubtrationOrder, Timeshift : various
            Processing and quantification options.

        Returns
        -------
        None
        """
        qTI = 0.85
        Rwm = 1.19  # 1.06 in Wong 97. 1.19 in Cavosuglu 09, Proton density ratio between blood and WM;
        # needed only for AslType=0 (PASL) with QuantFlag=1 (unique M0 based quantification)
        Rcsf = 0.87  # both Rwm and Rcsf are for 3T only, you need to change them for other field strength.
        lmbda = 0.9  # 0.9 mL/g

        Delaytime = list([x * 1000.0 for x in data_descrip["PLDList"] if x != 0])[0]

        if data_descrip["MagneticFieldStrength"] == 1.5:
            T2wm = 55
            T2b = 100
            BloodT1 = 1200
        elif data_descrip["MagneticFieldStrength"] == 3:
            T2wm = 44.7
            T2b = 43.6
            T2csf = 74.9
            BloodT1 = 1664
        else:
            T2wm = 30
            T2b = 60
            BloodT1 = 1810
        r1a = 1 / BloodT1

        labeff = data_descrip["LabelingEfficiency"]

        useM0 = False
        if QuantFlag != 0:
            if not M0wmcsf:
                raise ValueError(
                    "Missing M0 value of WM or CSF for unique M0 based quantification"
                )
            if QuantFlag == 1:
                M0b = (
                    M0wmcsf
                    * Rcsf
                    * np.exp((1 / T2csf - 1 / T2b) * data_descrip["M0"]["EchoTime"] * 1000)
                )
            else:
                M0b = (
                    M0wmcsf
                    * Rwm
                    * np.exp((1 / T2wm - 1 / T2b) * data_descrip["M0"]["EchoTime"] * 1000)
                )
        else:
            if data_descrip["M0Type"] == "Estimate":
                useM0 = False
            else:
                useM0 = True

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")
            if QuantFlag == 0:
                if data_descrip["M0Type"] == "Separate":
                    P_m0 = os.path.join(key, "perf", f"sr{value['M0']}.nii")
                    V_m0, m0all = load_img(P_m0)
                    if m0all.ndim == 4:
                        M0 = np.mean(m0all, axis=3)
                    else:
                        M0 = m0all
                elif data_descrip["M0Type"] == "Included":
                    P = os.path.join(key, "perf", f"srr{value['asl'][0]}.nii")
                    V, data = load_img(P)
                    num_m0 = 0
                    M0 = np.zeros(data.shape[:3])
                    for i, volume_type in enumerate(data_descrip["ASLContext"]):
                        if volume_type == "m0scan":
                            M0 += data[:, :, :, i]
                            num_m0 += 1
                    M0 /= num_m0

            for asl_file in value["asl"]:
                Pmask = os.path.join(key, "perf", f"{asl_file}_mask_perf_cbf.nii")
                Vmask, maskdat = load_img(Pmask)
                Pall = os.path.join(key, "perf", f"srr{asl_file}.nii")
                Vall, alldat = load_img(Pall)
                if QuantFlag == 0 and useM0:
                    if not np.array_equal(M0.shape, alldat.shape[:3]):
                        raise ValueError(
                            "M0 image size is different from the perfusion images"
                        )

                brain_ind = np.flatnonzero(maskdat)

                if MaskFlag:
                    vxidx = brain_ind
                else:
                    vxidx = np.ravel_multi_index((np.where(maskdat > -1)), maskdat.shape)

                conidx = []
                labidx = []
                for i, volume_type in enumerate(data_descrip["ASLContext"]):
                    if volume_type == "control":
                        conidx.append(i)
                    elif volume_type == "label":
                        labidx.append(i)

                perfno = len(labidx)
                BOLDimg4D = np.zeros(
                    (alldat.shape[0], alldat.shape[1], alldat.shape[2], perfno)
                )
                CBFimg4D = np.zeros_like(BOLDimg4D)
                perfimg4D = np.zeros_like(BOLDimg4D)
                gs = np.zeros((perfno, 4))
                for p in range(perfno):
                    Vlabimg = alldat[:, :, :, labidx[p]]

                    if SubtractionType == 0:
                        Vconimg = alldat[:, :, :, conidx[p]]
                    elif SubtractionType == 1:
                        Vconimg = alldat[:, :, :, conidx[p]]
                        if data_descrip["LabelControl"]:
                            if p > 0:
                                Vconimg = (Vconimg + alldat[:, :, :, conidx[p - 1]]) / 2
                        else:
                            if p < perfno - 1:
                                Vconimg = (Vconimg + alldat[:, :, :, conidx[p + 1]]) / 2
                    else:
                        if data_descrip["LabelControl"]:
                            idx = p + np.array([-4, -3, -2, -1, 0, 1])
                            normloc = 3 - Timeshift
                        else:
                            idx = p + np.array([-3, -2, -1, 0, 1, 2])
                            normloc = 2 + Timeshift
                        idx[idx < 0] = 0
                        idx[idx > perfno - 1] = perfno - 1
                        idx_arr = np.array(idx).astype(int)
                        conidx_arr = np.array(conidx).astype(int)
                        nimg = alldat[:, :, :, conidx_arr[idx_arr]]
                        nimg = np.reshape(nimg, (-1, nimg.shape[3]))
                        tmpimg = self.asltbx_sinc_interpVec(nimg[brain_ind, :], normloc)
                        Vconimg = np.zeros(nimg.shape[0])
                        Vconimg[brain_ind] = tmpimg
                        Vconimg = np.reshape(Vconimg, alldat.shape[:3])

                    perfimg = Vconimg - Vlabimg
                    if SubtrationOrder == 0:
                        perfimg = -1.0 * perfimg

                    if MaskFlag:
                        perfimg = perfimg * maskdat

                    slicetimearray = np.ones(
                        (alldat.shape[0] * alldat.shape[1], alldat.shape[2])
                    )
                    Slicetime = 0
                    if "SliceDuration" in data_descrip:
                        Slicetime = data_descrip["SliceDuration"] * 1000
                    for sss in range(alldat.shape[2]):
                        slicetimearray[:, sss] = slicetimearray[:, sss] * sss * Slicetime
                    slicetimearray = slicetimearray.ravel()
                    slicetimearray = slicetimearray[vxidx]

                    BOLDimg = (Vconimg + Vlabimg) / 2
                    meanbold = BOLDimg
                    BOLDimg4D[:, :, :, p] = BOLDimg

                    cbfimg = np.zeros(perfimg.shape)
                    if data_descrip["ArterialSpinLabelingType"] == "PASL":
                        TI = Delaytime + slicetimearray
                        tperf = perfimg.flat[vxidx]
                        tmpsig = meanbold.flat[vxidx]
                        tcbf = np.zeros_like(vxidx)
                        effidx = np.where(abs(tmpsig) > 1e-3 * np.mean(tmpsig))
                        effidx = np.ravel_multi_index(effidx, tmpsig.shape)
                        efftperf = tperf[effidx]
                        TI = TI.flat[effidx]
                        if QuantFlag:
                            tcbf[effidx] = (
                                efftperf
                                * 6000
                                * 1000
                                / (
                                    2
                                    * M0b
                                    * np.exp(-TI / BloodT1)
                                    * data_descrip["BolusCutOffDelayTime"]
                                    * 1000
                                    * labeff
                                    * qTI
                                )
                            )
                        else:
                            if useM0:
                                eM0 = M0.flat[vxidx]
                            else:
                                eM0 = Vconimg.flat[vxidx]
                            effM0 = eM0[effidx]
                            tcbf[effidx] = (
                                lmbda
                                * efftperf
                                * 6000
                                * 1000
                                / (
                                    2
                                    * effM0
                                    * np.exp(-TI / BloodT1)
                                    * data_descrip["BolusCutOffDelayTime"]
                                    * 1000
                                    * labeff
                                    * qTI
                                )
                            )
                        multi_idx = np.unravel_index(vxidx, cbfimg.shape)
                        cbfimg[multi_idx] = tcbf

                    elif (
                        data_descrip["ArterialSpinLabelingType"] == "CASL"
                        or data_descrip["ArterialSpinLabelingType"] == "PCASL"
                    ):
                        omega = Delaytime + slicetimearray
                        locMask = Vconimg.flat[vxidx]
                        tperf = perfimg.flat[vxidx]
                        tcbf = np.zeros_like(vxidx)
                        effidx = np.where(abs(locMask) > 1e-3 * np.mean(locMask))
                        effidx = np.ravel_multi_index(effidx, locMask.shape)
                        omega = omega.flat[effidx]
                        efftperf = tperf[effidx]
                        if QuantFlag:
                            efftcbf = efftperf / M0b
                        else:
                            if useM0:
                                eM0 = M0.flat[vxidx]
                            else:
                                eM0 = Vconimg.flat[vxidx]
                            effM0 = eM0[effidx]
                            efftcbf = efftperf / effM0
                        efftcbf = (
                            6000
                            * 1000
                            * lmbda
                            * efftcbf
                            * r1a
                            / (
                                2
                                * labeff
                                * (
                                    np.exp(-omega * r1a)
                                    - np.exp(
                                        -1
                                        * (data_descrip["LabelingDuration"] * 1000 + omega)
                                        * r1a
                                    )
                                )
                            )
                        )
                        tcbf[effidx] = efftcbf
                        multi_idx = np.unravel_index(vxidx, cbfimg.shape)
                        cbfimg[multi_idx] = tcbf

                    CBFimg4D[:, :, :, p] = cbfimg
                    perfimg4D[:, :, :, p] = perfimg

                    nanmask = np.isnan(cbfimg)
                    outliermask = (cbfimg < -40) | (cbfimg > 150)
                    maskdat = maskdat.astype(bool)
                    sigmask = maskdat & (~outliermask) & (~nanmask)
                    wholemask = maskdat & (~nanmask)
                    outliercleaned_maskind = np.where(sigmask)
                    whole_ind = np.where(wholemask)

                    gs[p, 1] = np.mean(cbfimg[outliercleaned_maskind])
                    gs[p, 3] = np.mean(cbfimg[whole_ind])
                    gs[p, 0] = np.mean(perfimg[outliercleaned_maskind])
                    gs[p, 2] = np.mean(perfimg[whole_ind])

                np.savetxt(
                    os.path.join(key, "perf", f"{asl_file}_globalsg.txt"),
                    gs,
                    fmt="%0.5f",
                    header="Perf_outliercleaned,CBF_outliercleaned,Perf_whole,CBF_whole",
                )

                header = Vall.header.copy()
                affine = Vall.affine.copy()
                header.set_data_shape(CBFimg4D.shape)
                VCBFimg = nib.Nifti1Image(CBFimg4D, affine, header)
                VCBFimg.header["descrip"] = b"asltbx_pipeline"
                VCBFimg.to_filename(os.path.join(key, "perf", f"{asl_file}_CBF.nii"))

                if BOLDFlag:
                    VBOLDimg = nib.Nifti1Image(BOLDimg4D, affine, header)
                    VBOLDimg.header["descrip"] = b"asltbx_pipeline"
                    VBOLDimg.to_filename(os.path.join(key, "perf", f"{asl_file}_BOLD.nii"))

                if PerfFlag:
                    Vperfimg = nib.Nifti1Image(perfimg4D, affine, header)
                    Vperfimg.header["descrip"] = b"asltbx_pipeline"
                    Vperfimg.to_filename(os.path.join(key, "perf", f"{asl_file}_PERF.nii"))

                if MeanFlag:
                    header = Vmask.header.copy()
                    affine = Vmask.affine.copy()
                    header.set_data_dtype(np.float32)
                    mCBFimg = np.mean(CBFimg4D, axis=3)
                    VmCBFimg = nib.Nifti1Image(mCBFimg, affine, header)
                    VmCBFimg.header["descrip"] = b"asltbx_pipeline"
                    VmCBFimg.to_filename(os.path.join(key, "perf", f"{asl_file}_mCBF.nii"))
                    if PerfFlag:
                        mPERFimg = np.mean(perfimg4D, axis=3)
                        VmPERFimg = nib.Nifti1Image(mPERFimg, affine, header)
                        VmPERFimg.header["descrip"] = b"asltbx_pipeline"
                        VmPERFimg.to_filename(
                            os.path.join(key, "perf", f"{asl_file}_mPERF.nii")
                        )
                    if BOLDFlag:
                        mBOLDimg = np.mean(BOLDimg4D, axis=3)
                        VmBOLDimg = nib.Nifti1Image(mBOLDimg, affine, header)
                        VmBOLDimg.header["descrip"] = b"asltbx_pipeline"
                        VmBOLDimg.to_filename(
                            os.path.join(key, "perf", f"{asl_file}_mBOLD.nii")
                        )
    
    