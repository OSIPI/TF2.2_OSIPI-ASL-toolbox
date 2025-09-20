"""
MRICloudRescale module
----------------------
Rescale ASL images using MRICloud pipeline logic.
"""

import os
import nibabel as nib
import numpy as np
import logging
from pyasl.utils.utils import load_img

logger = logging.getLogger(__name__)

class MRICloudRescale:

    def run(self, data_descrip: dict, params: dict):
        """
        Rescale ASL images.

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Additional parameters.

        Returns:
            None
        """
        logger.info("MRICloud: Rescale ASL data...")
        for key, value in data_descrip["Images"].items():
            for asl_file in value["asl"]:
                asl_path = os.path.join(key, "perf", f"{asl_file}.nii")
                asl_der_path = asl_path.replace("rawdata", "derivatives")
                self.img_rescale(asl_path, asl_der_path)

            if value["M0"]:
                m0_path = os.path.join(key, "perf", f"{value['M0']}.nii")
                m0_der_path = m0_path.replace("rawdata", "derivatives")
                self.img_rescale(m0_path, m0_der_path)

    def img_rescale(self, source_path: str, target_path: str):
        """
        Rescale image data and save to target path.

        Args:
            source_path (str): Source image path.
            target_path (str): Target image path.

        Returns:
            None
        """
        img, data = load_img(source_path)
        slope, _ = img.header.get_slope_inter()
        ss = slope if slope is not None else 1.0
        data = data / ss / ss
        rescaled_img = nib.Nifti1Image(data, img.affine, img.header)
        rescaled_img.set_data_dtype(np.float32)
        rescaled_img.header["scl_slope"] = 1
        rescaled_img.header["scl_inter"] = 0
        rescaled_img.header["descrip"] = "4D rescaled images"
        rescaled_img.to_filename(target_path)
