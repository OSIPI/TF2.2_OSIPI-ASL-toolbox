"""
Realign
-------
SPM-based realignment for ASL images.
"""

import os
from nipype.interfaces import spm
import logging

logger = logging.getLogger(__name__)

class Realign:
    """
    SPM-based realignment of ASL images using Nipype.

    Realigns all ASL time series to correct for motion. See `run()` for usage.
    """
    def run(self, data_descrip: dict, config: dict):
        """
        SPM-based realignment for ASL images.

        Args:
            data_descrip (dict): Data description dictionary.
            config (dict): Configuration parameters.

        Returns:
            None
        """
        logger.info("ASLtbx: Realign ASL data...")
        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")
            for asl_file in value["asl"]:
                P = os.path.join(key, "perf", f"{asl_file}.nii")

                realign = spm.Realign()
                realign.inputs.in_files = P
                realign.inputs.quality = config.get("quality", 0.9)
                realign.inputs.fwhm = config.get("fwhm", 5)
                realign.inputs.register_to_mean = config.get("register_to_mean", True)
                realign.inputs.jobtype = config.get("jobtype", "estwrite")
                realign.inputs.interp = config.get("interp", 1)
                realign.inputs.wrap = config.get("wrap", [0, 0, 0])
                realign.inputs.write_mask = config.get("write_mask", True)
                realign.inputs.write_which = config.get("write_which", [2, 1])
                realign.run()