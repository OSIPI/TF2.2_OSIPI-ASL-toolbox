"""
Smooth module
-------------
SPM-based smoothing for ASL images.
"""

import os
from nipype.interfaces import spm
import logging

logger = logging.getLogger(__name__)

class Smooth:
    def run(self, data_descrip: dict, config: dict):
        """
        SPM-based smoothing for ASL images.

        Args:
            data_descrip (dict): Data description dictionary.
            config (dict): Configuration parameters.

        Returns:
            None
        """
        logger.info("ASLtbx: Smooth ASL data...")
        fwhm = config.get("fwhm", [6, 6, 6])

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")
            P = []

            if value["M0"]:
                P.append(os.path.join(key, "perf", f"r{value['M0']}.nii"))

            for asl_file in value["asl"]:
                P.append(os.path.join(key, "perf", f"rmean{asl_file}.nii"))
                P.append(os.path.join(key, "perf", f"rr{asl_file}.nii"))

            smooth = spm.Smooth()
            smooth.inputs.in_files = P
            smooth.inputs.fwhm = fwhm
            smooth.run()