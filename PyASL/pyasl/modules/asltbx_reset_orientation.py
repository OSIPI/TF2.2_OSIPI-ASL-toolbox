"""
ResetOrientation
----------------
Reset the orientation of a NIfTI image to axis-aligned (identity rotation) while preserving voxel sizes.
Saves the reoriented image to the specified destination path.
"""

import os
import nibabel as nib
import numpy as np
from typing import Dict, Any
import logging
logger = logging.getLogger(__name__)

class ResetOrientation:
    """
    ASLTBX: reset qform/sform to axis-aligned affine while keeping voxel sizes.
    Writes results under the derivatives mirror of the raw structure.
    """
    def _reset_one(self, src: str, dst: str) -> None:
        """
        Reset the orientation of a NIfTI image to axis-aligned (identity rotation) while preserving voxel sizes.
        Saves the reoriented image to the specified destination path.
        
        Args:
            src (str): Path to the source NIfTI image.
            dst (str): Path to save the reoriented NIfTI image.
        """
        if not os.path.exists(src):
            logger.error("Source not found: %s", src)
            raise FileNotFoundError(src)

        img = nib.load(src)
        M = img.affine

        # voxel size from the columns of 3x3 block
        vox = np.sqrt(np.sum(M[:3, :3] ** 2, axis=0))
        if np.linalg.det(M[:3, :3]) < 0:
            vox[0] = -vox[0]

        # center offset in voxel space
        orig = (np.array(img.shape[:3]) + 1) / 2.0
        off = -vox * orig

        new_affine = np.array([
            [vox[0], 0,       0,       off[0]],
            [0,       vox[1], 0,       off[1]],
            [0,       0,       vox[2], off[2]],
            [0,       0,       0,      1.0   ],
        ])

        img.set_qform(new_affine)
        img.set_sform(new_affine)

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        nib.save(img, dst)
        logger.debug("Reset orientation: %s -> %s", src, dst)

    def run(self, data_descrip: Dict[str, Any], config: Dict[str, Any]) -> None:
        """
        Reset the orientation of all ASL and structural images to axis-aligned while preserving voxel sizes.
        Saves the reoriented images under the derivatives mirror of the raw structure.
        
        Args:
            data_descrip (Dict[str, Any]): Dictionary containing image paths.
            config (Dict[str, Any]): Configuration dictionary (currently unused).
        """
        logger.info("ASLTBX: Reset image orientation...")
        for key, value in data_descrip["Images"].items():
            # ASL series
            for asl_file in value["asl"]:
                src = os.path.join(key, "perf", f"{asl_file}.nii")            # raw
                dst = src.replace("rawdata", "derivatives")                    # derivatives
                self._reset_one(src, dst)

            # M0 (optional)
            if value.get("M0"):
                src = os.path.join(key, "perf", f"{value['M0']}.nii")
                dst = src.replace("rawdata", "derivatives")
                self._reset_one(src, dst)

            # anat (required)
            anat = value.get("anat")
            if not anat:
                raise ValueError("No structural images!")
            src = os.path.join(key, "anat", f"{anat}.nii")
            dst = src.replace("rawdata", "derivatives")
            self._reset_one(src, dst)