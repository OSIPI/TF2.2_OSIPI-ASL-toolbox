"""
MRICloudCalculateM0 module
-------------------------
Calculate M0 map using MRICloud pipeline logic.
"""

import os
import numpy as np
import nibabel as nib
import logging
from pyasl.utils.utils import load_img
from pyasl.utils.mricloud_helpers import img_coreg, mricloud_getBrainMask, mricloud_bgs_factor

logger = logging.getLogger(__name__)

class MRICloudCalculateM0:
    def run(self, data_descrip: dict, params: dict):
        """
        Calculate M0 map using MRICloud pipeline logic.
        Parameters can include:
        - t1_tissue: T1 relaxation time for tissue (default: 1165 ms)
        - bgs_eff: Background suppression efficiency (default: 0.93)

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Additional parameters.

        Returns:
            None
        """
        logger.info("MRICloud: Calculate M0...")

        t1_tissue = params.get("t1_tissue", 1165)
        bgs_eff = params.get("bgs_eff", 0.93)

        current_dir = os.path.dirname(__file__)
        imgtpm = os.path.join(current_dir, "..", "tpm", "TPM.nii")

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")

            asl_file = value["asl"][0]
            P_ctrl = os.path.join(key, "perf", f"r{asl_file}_ctrl.nii")
            V_ctrl, ctrlvol = load_img(P_ctrl)
            ctrlsiz = ctrlvol.shape

            if data_descrip["M0Type"] != "Estimate":
                # --- Case 1: Direct M0 provided or derived from ASLContext ---
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
                # --- Case 2: Estimate M0 from control images ---
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
                            timing = [0, totdur + data_descrip["SliceDuration"] * 1000 * (kk - 1)]
                        else:
                            timing = [0, totdur]
                        flip = [0, 0]
                        bgs_f = mricloud_bgs_factor(0.0, t1_tissue, flip, timing, 1)
                    else:
                        if data_descrip["MRAcquisitionType"] == "2D":
                            timing = (
                                [0]
                                + [x * 1000 for x in data_descrip["BackgroundSuppressionPulseTime"][:-1]]
                                + [data_descrip["BackgroundSuppressionPulseTime"][-1] * 1000
                                   + data_descrip["SliceDuration"] * 1000 * (kk - 1)]
                            )
                        else:
                            timing = (
                                [0]
                                + [x * 1000 for x in data_descrip["BackgroundSuppressionPulseTime"][:-1]]
                                + [data_descrip["BackgroundSuppressionPulseTime"][-1] * 1000]
                            )
                        flip = [0] + [np.pi] * (len(data_descrip["BackgroundSuppressionPulseTime"]) - 1) + [0]
                        bgs_f = mricloud_bgs_factor(0.0, t1_tissue, flip, timing, bgs_eff)

                    m0tmp[:, :, kk] = ctrlvol[:, :, kk] / bgs_f

                brnmsk_dspl, brnmsk_clcu = mricloud_getBrainMask(imgtpm, P_ctrl)
                m0_glo = np.mean(m0tmp[brnmsk_clcu])
                m0map_final = brnmsk_dspl.astype(float) * m0_glo

            # --- Save final results ---
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
