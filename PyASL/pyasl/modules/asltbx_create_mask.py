"""
CreateMask
----------
Create a brain mask from ASL perfusion images.
"""

import os
import numpy as np
import nibabel as nib
from pyasl.utils.utils import load_img
import logging
logger = logging.getLogger(__name__)

class CreateMask:
    """
    CreateMask generates brain masks from ASL perfusion images using intensity thresholding.

    For each ASL image, a binary mask is created by thresholding at a configurable fraction
    (default: 0.1, set via 'thres' in config) of the image's maximum intensity. The resulting
    mask is saved as a NIfTI file in the derivatives/perf directory with the suffix
    '_mask_perf_cbf.nii'. This is useful for downstream ASL analysis and preprocessing.

    Method
    ------
    run(data_descrip: dict, config: dict)
        For each ASL image in data_descrip, generate and save a brain mask.
    """
    def run(self, data_descrip: dict, config: dict):
        """
        Generate and save brain masks for all ASL images in the dataset.

        For each ASL image listed in `data_descrip`, this method creates a binary mask
        by thresholding at a fraction (`thres`, default 0.1) of the image's maximum intensity.
        The resulting mask is saved as a NIfTI file in the derivatives/perf directory.

        Parameters
        ----------
        data_descrip : dict
            Dataset description with ASL image file locations.
        config : dict
            Configuration dictionary. May include 'thres' (float, default 0.1).
        """
        logger.info("ASLtbx: Create brain mask...")
        thres = config.get("thres", 0.1)

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")
            for asl_file in value["asl"]:
                PF = os.path.join(key, "perf", f"srmean{asl_file}.nii")
                V, data = load_img(PF)
                mask = data > thres * np.max(data)
                header = V.header.copy()
                header.set_data_dtype(np.int16)
                mask_img = nib.Nifti1Image(mask, V.affine, header)
                mask_img.header["descrip"] = b"asltbx_pipeline"
                mask_img.to_filename(
                    os.path.join(key, "perf", f"{asl_file}_mask_perf_cbf.nii")
                )
