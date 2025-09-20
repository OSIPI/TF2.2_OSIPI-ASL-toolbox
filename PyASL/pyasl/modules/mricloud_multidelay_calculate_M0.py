"""
MRICloudMultidelayCalculateM0 module
------------------------------------
Calculate M0 for multidelay ASL data using MRICloud pipeline logic.
"""

import os
import numpy as np
import nibabel as nib
import logging
from scipy.optimize import curve_fit
from pyasl.utils.utils import load_img
from pyasl.utils.mricloud_helpers import img_coreg, mricloud_getBrainMask, mricloud_func_recover

logger = logging.getLogger(__name__)

class MRICloudMultidelayCalculateM0:
    """
    MRICloudMultidelayCalculateM0
    -----------------------------
    Calculate M0 for multidelay ASL data using MRICloud pipeline logic.

    This class provides a method to estimate M0 maps from multidelay ASL acquisitions, supporting both PCASL and PASL types.
    The method expects preprocessed ASL images, M0 maps, and brain masks, and fits a kinetic model voxelwise to the difference images
    across multiple post-labeling delays (PLDs) or inversion times (TIs).
    """
    def run(self, data_descrip: dict, params: dict):
        """
        Calculate M0 for multidelay ASL data using MRICloud pipeline logic.

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Additional parameters.

        Returns:
            None
        """
        logger.info("MRICloud: Multidelay Calculate M0...")

        current_dir = os.path.dirname(__file__)
        imgtpm = os.path.join(current_dir, "..", "tpm", "TPM.nii")

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")

            asl_file = value["asl"][0]
            fn_asl = os.path.join(key, "perf", f"{asl_file}.nii")
            V_asl, img_all = load_img(fn_asl)
            fn_ctrl = os.path.join(key, "perf", f"r{asl_file}_ctrl.nii")
            V_ctrl = nib.load(fn_ctrl)

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

                # Coregister M0 map to control image
                target = fn_ctrl
                img_coreg(target, m0path)
                P_rm0 = os.path.join(key, "perf", "rM0ave.nii")
                V_rm0, rm0vol = load_img(P_rm0)

                # Apply brain mask
                brnmsk_dspl, brnmsk_clcu = mricloud_getBrainMask(imgtpm, P_rm0)
                m0map_final = rm0vol * brnmsk_dspl.astype(float)

            else:
                # --- Case 2: Estimate M0 from multiple PLDs ---
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

            # --- Save results ---
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
