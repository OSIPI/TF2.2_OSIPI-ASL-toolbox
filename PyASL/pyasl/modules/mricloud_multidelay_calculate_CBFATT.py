"""
MRICloudMultidelayCalculateCBFATT module
----------------------------------------
Calculate CBF and ATT for multidelay ASL data using MRICloud pipeline logic.
"""

import os
import numpy as np
import nibabel as nib
import logging
from scipy.optimize import curve_fit
from pyasl.utils.utils import load_img
from pyasl.utils.mricloud_helpers import (
    mricloud_func_gkm_pcasl_multidelay,
    mricloud_func_gkm_pasl_looklocker,
)

logger = logging.getLogger(__name__)

class MRICloudMultidelayCalculateCBFATT:
    """
    MRICloudMultidelayCalculateCBFATT
    ---------------------------------
    Calculate CBF (Cerebral Blood Flow) and ATT (Arterial Transit Time) for multidelay ASL data using MRICloud pipeline logic.

    This class provides a method to estimate CBF and ATT maps from multidelay ASL acquisitions, supporting both PCASL and PASL types.
    The method expects preprocessed ASL images, M0 maps, and brain masks, and fits a kinetic model voxelwise to the difference images
    across multiple post-labeling delays (PLDs) or inversion times (TIs).

    Methods
    -------
    run(data_descrip: dict, params: dict)
        Calculate CBF and ATT maps for multidelay ASL data using MRICloud pipeline logic.
    """
    def run(self, data_descrip: dict, params: dict):
        """
        Calculate CBF (Cerebral Blood Flow) and ATT (Arterial Transit Time)
        for multidelay ASL data using MRICloud pipeline logic.

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Additional parameters.

        Returns:
            None
        """
        logger.info("MRICloud: Calculate CBF and ATT...")

        t1_blood = params.get("t1_blood", 1650)
        part_coef = params.get("part_coef", 0.9)

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")

            for asl_file in value["asl"]:
                # Load ASL image, M0 map, and brain masks
                V_asl, img_all = load_img(os.path.join(key, "perf", f"{asl_file}.nii"))
                _, m0map = load_img(os.path.join(key, "perf", "M0map.nii"))
                _, brnmsk_dspl = load_img(os.path.join(key, "perf", "brnmsk_dspl.nii"))
                _, brnmsk_clcu = load_img(os.path.join(key, "perf", "brnmsk_clcu.nii"))

                brnmsk_dspl = brnmsk_dspl.astype(bool)
                brnmsk_clcu = brnmsk_clcu.astype(bool)

                # Split control and label images
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

                # Masked difference data
                brnmsk1 = np.tile(brnmsk_dspl[..., np.newaxis], (1, 1, 1, diff.shape[3]))
                m0map1 = np.tile(m0map[..., np.newaxis], (1, 1, 1, diff.shape[3]))
                idx_msk = np.where(brnmsk_dspl)
                idx_msk1 = np.where(brnmsk1)

                ndiff = np.zeros_like(diff)
                ndiff[idx_msk1] = diff[idx_msk1] / m0map1[idx_msk1]
                ndiff = ndiff.reshape(-1, diff.shape[3])

                # PLDs
                plds = []
                for i, volume_type in enumerate(data_descrip["ASLContext"]):
                    if volume_type == "label":
                        plds.append(data_descrip["PLDList"][i] * 1000.0)
                plds = np.array(plds) / 1000  # convert ms to s

                paras = {
                    "labl_eff": data_descrip["LabelingEfficiency"],
                    "t1_blood": t1_blood / 1000,  # convert ms to s
                    "part_coef": part_coef,
                }

                attmap = np.zeros_like(m0map)
                cbfmap = np.zeros_like(m0map)

                # Fit CBF and ATT voxel by voxel
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
                        attmap[ivox] = beta1[1] * 1000  # convert to ms

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
                        attmap[ivox] = beta1[1] * 1000  # convert to ms

                # Normalize relative CBF
                cbf_glo = np.mean(cbfmap[brnmsk_clcu])
                rcbfmap = cbfmap / cbf_glo

                header = V_asl.header.copy()
                affine = V_asl.affine.copy()

                # Save absolute CBF map
                acbf_img = nib.Nifti1Image(cbfmap, affine, header)
                acbf_img.header["descrip"] = b"mricloud_pipeline"
                acbf_img.to_filename(os.path.join(key, "perf", f"{asl_file}_aCBF_native.nii"))

                # Save relative CBF map
                rcbf_img = nib.Nifti1Image(rcbfmap, affine, header)
                rcbf_img.header["descrip"] = b"mricloud_pipeline"
                rcbf_img.to_filename(os.path.join(key, "perf", f"{asl_file}_rCBF_native.nii"))

                # Save ATT map
                att_img = nib.Nifti1Image(attmap, affine, header)
                att_img.header["descrip"] = b"mricloud_pipeline"
                att_img.to_filename(os.path.join(key, "perf", f"{asl_file}_ATT_native.nii"))
