"""
MRICloudCalculateDiffmap module
-------------------------------
Calculate difference volume for ASL images using MRICloud pipeline logic.

Author: OSIPI-ASL Toolbox Team
Date: 2025-09-03
"""

import os
import numpy as np
import nibabel as nib
import logging
from pyasl.utils.utils import load_img

logger = logging.getLogger(__name__)

class MRICloudCalculateDiffmap:

    def run(self, data_descrip: dict, params: dict):
        """
        Calculate difference volume for ASL images.

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Additional parameters.

        Returns:
            None
        """
        logger.info("MRICloud: Calculate difference volume...")
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
