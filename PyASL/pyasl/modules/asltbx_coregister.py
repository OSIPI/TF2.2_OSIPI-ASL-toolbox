"""
Coregister
----------
SPM-based coregistration of ASL data.
"""

import os
from nipype.interfaces import spm
import logging
logger = logging.getLogger(__name__)

class Coregister:
    """
    Perform SPM-based coregistration of ASL data.

    This class wraps the SPM `Coregister` interface to align perfusion
    and optional M0 images to the corresponding anatomical reference
    for each subject described in `data_descrip`.

    Use `run()` to iterate through all subjects, construct required paths,
    and execute the coregistration according to the provided `config`.
    """
    def run(self, data_descrip: dict, config: dict):
        """
        Run coregistration for all subjects.

        Parameters
        ----------
        data_descrip : dict
            Metadata describing ASL datasets, including anatomical, perfusion,
            and optional M0 image names.
        config : dict
            Coregistration options (e.g., SPM `jobtype`).

        Returns
        -------
        None
            The function executes SPM Coregister and saves the aligned files.
        """
        logger.info("ASLtbx: Coregister ASL data...")
        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")
            PG = os.path.join(key, "anat", f"{value['anat']}.nii")
            for asl_file in value["asl"]:
                PF = os.path.join(key, "perf", f"mean{asl_file}.nii")
                PO = [PF, os.path.join(key, "perf", f"r{asl_file}.nii")]
                if value["M0"]:
                    PO.append(os.path.join(key, "perf", f"{value['M0']}.nii"))

                coreg = spm.Coregister()
                coreg.inputs.target = PG
                coreg.inputs.source = PF
                coreg.inputs.apply_to_files = PO
                coreg.inputs.jobtype = config.get("jobtype", "estwrite")
                coreg.run()