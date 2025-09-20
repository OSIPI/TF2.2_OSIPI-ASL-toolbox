"""
MRICloudCalculateCBF
--------------------
Calculate CBF (Cerebral Blood Flow) using MRICloud pipeline logic.
"""
import os
import numpy as np
import nibabel as nib
from pyasl.utils.utils import load_img
import logging
logger = logging.getLogger(__name__)


class MRICloudCalculateCBF:
    def run(self, data_descrip: dict, params: dict):
        """
        Calculate CBF (Cerebral Blood Flow) using MRICloud pipeline logic.

        Parameters can include:
        - t1_blood: T1 relaxation time of blood (default: 1650 ms)
        - part_coef: Partition coefficient (default: 0.9)
        - bgs_eff: Background suppression efficiency (default: 0.93)
        """
        logger.info("MRICloud: Calculate CBF...")

        t1_blood = params.get("t1_blood", 1650)
        part_coef = params.get("part_coef", 0.9)
        bgs_eff = params.get("bgs_eff", 0.93)

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")
            for asl_file in value["asl"]:
                # Load difference map, M0 map, and brain masks
                V_diff, diff = load_img(os.path.join(key, "perf", f"r{asl_file}_diff.nii"))
                _, m0map = load_img(os.path.join(key, "perf", "M0map.nii"))
                _, brnmsk_dspl = load_img(os.path.join(key, "perf", "brnmsk_dspl.nii"))
                _, brnmsk_clcu = load_img(os.path.join(key, "perf", "brnmsk_clcu.nii"))

                brnmsk_dspl = brnmsk_dspl.astype(bool)
                brnmsk_clcu = brnmsk_clcu.astype(bool)

                tmpcbf = np.zeros_like(diff)
                nslice = tmpcbf.shape[2]

                for kk in range(nslice):
                    if data_descrip["ArterialSpinLabelingType"] == "PCASL":
                        # For PCASL
                        casl_pld = list(
                            set([x * 1000.0 for x in data_descrip["PLDList"] if x != 0])
                        )[0]
                        if data_descrip["MRAcquisitionType"] == "3D":
                            spld = casl_pld
                        else:
                            spld = casl_pld + data_descrip["SliceDuration"] * 1000 * (kk - 1)
                        tmpcbf[:, :, kk] = (
                            diff[:, :, kk]
                            * np.exp(spld / t1_blood)
                            / (1 - np.exp(-data_descrip["LabelingDuration"] * 1000 / t1_blood))
                            / t1_blood
                        )

                    elif data_descrip["ArterialSpinLabelingType"] == "PASL":
                        # For PASL
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
                            diff[:, :, kk] * np.exp(sti / t1_blood) / (data_descrip["BolusCutOffDelayTime"] * 1000)
                        )

                # Avoid division by zero in M0 map
                m0map[np.abs(m0map) < 1e-6] = np.mean(m0map[brnmsk_clcu])
                m0vol = m0map.astype(np.float32)
                brvol = brnmsk_dspl.astype(np.float32)

                # Compute scaling factor alpha
                if data_descrip["BackgroundSuppression"]:
                    alpha = (bgs_eff ** data_descrip["BackgroundSuppressionNumberPulses"]) * data_descrip["LabelingEfficiency"]
                else:
                    alpha = data_descrip["LabelingEfficiency"]

                # Compute absolute and relative CBF
                cbf = tmpcbf / m0vol * brvol * part_coef / 2 / alpha * 60 * 100 * 1000
                cbf_thr = np.clip(cbf, 0, 200)
                cbf_glo = np.mean(cbf_thr[brnmsk_clcu])
                rcbf_thr = cbf_thr / cbf_glo

                header = V_diff.header.copy()

                # Save absolute CBF map
                acbf_img = nib.Nifti1Image(cbf_thr, V_diff.affine, header)
                acbf_img.header["descrip"] = b"mricloud_pipeline"
                acbf_img.to_filename(os.path.join(key, "perf", f"{asl_file}_aCBF_native.nii"))

                # Save relative CBF map
                rcbf_img = nib.Nifti1Image(rcbf_thr, V_diff.affine, header)
                rcbf_img.header["descrip"] = b"mricloud_pipeline"
                rcbf_img.to_filename(os.path.join(key, "perf", f"{asl_file}_rCBF_native.nii"))
