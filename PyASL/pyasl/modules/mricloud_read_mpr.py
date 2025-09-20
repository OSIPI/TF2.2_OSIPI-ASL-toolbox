"""
MRICloudReadMPR
---------------
Read the MPR image from the structural image using MRICloud pipeline logic.
"""
import os
import re
import logging
logger = logging.getLogger(__name__)

class MRICloudReadMPR:
    """
    MRICloudReadMPR
    ---------------
    Read the MPR image from the structural image using MRICloud pipeline logic.
    """
    def run(self, data_descrip: dict, params: dict):
        """
        Read the MPR image from the structural image using MRICloud pipeline logic.
        """
        logger.info("MRICloud: Read MPR...")
        for key, value in data_descrip["Images"].items():
            key_der = key.replace("rawdata", "derivatives")
            if not value["anat"]:
                raise ValueError("Missing structural images for multi-atlas analysis!")
            anat_path = os.path.join(key_der, "anat")
            entries = os.listdir(anat_path)
            directories = [d for d in entries if os.path.isdir(os.path.join(anat_path, d))]
            mpr_folder = None
            mpr_name = None
            for dir in directories:
                if os.path.exists(os.path.join(anat_path, dir, "mni.imgsize")):
                    mpr_folder = dir
                    regex = re.compile(r"^(?!mni).+\.imgsize$")
                    files = [f for f in os.listdir(os.path.join(anat_path, dir)) if re.match(regex, f)]
                    mpr_file = files[0]
                    mpr_name = mpr_file[:-8]
                    break
            if mpr_folder is None:
                raise ValueError("Missing parcellation folder for multi-atlas analysis!")
            data_descrip["Images"][key]["mpr_folder"] = mpr_folder
            data_descrip["Images"][key]["mpr_name"] = mpr_name
        return data_descrip
