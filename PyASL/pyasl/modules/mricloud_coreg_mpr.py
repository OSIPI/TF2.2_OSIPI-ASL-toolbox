"""
MRICloudCoregMPR
----------------
Coregister ASL data to the structural MPR image using MRICloud pipeline logic.
"""
import os
from pyasl.utils.mricloud_helpers import img_coreg, mricloud_skullstrip
import logging
logger = logging.getLogger(__name__)


class MRICloudCoregMPR:
    """
    MRICloudCoregMPR
    ----------------
    Coregister ASL data to the structural MPR image using MRICloud pipeline logic.

    This class provides a method to coregister ASL perfusion and related images to a subject's
    structural MPR image, following the MRICloud pipeline conventions. It uses skull-stripped
    MPR images as the target for registration and supports both single-delay and multi-delay
    ASL acquisitions. After coregistration, output files are renamed to indicate alignment
    to the MPR space.

    Methods
    -------
    run(data_descrip: dict, params: dict)
        Coregister ASL and related images to the structural MPR image.

    _rename_files(key: str, asl_file: str)
        Rename coregistered files to include '_mpr' suffix.
    """
    def run(self, data_descrip: dict, params: dict):
        """
        Coregister ASL data to the structural MPR image using MRICloud pipeline logic.
        """
        logger.info("MRICloud: Coregister ASL data to structural image...")

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")

            # Create skull-stripped MPR image
            target = mricloud_skullstrip(
                os.path.join(key, "anat", value["mpr_folder"]),
                value["mpr_name"],
            )

            for asl_file in value["asl"]:
                # Source depends on whether M0 is estimated
                if data_descrip["M0Type"] != "Estimate":
                    source = os.path.join(key, "perf", "rM0ave.nii")
                else:
                    source = os.path.join(key, "perf", f"mean{asl_file}.nii")

                # Additional images to coregister
                other_files = [
                    os.path.join(key, "perf", f"{asl_file}_aCBF_native.nii"),
                    os.path.join(key, "perf", f"{asl_file}_rCBF_native.nii"),
                    os.path.join(key, "perf", "brnmsk_clcu.nii"),
                ]

                # Include ATT file if multidelay data
                att_file = os.path.join(key, "perf", f"{asl_file}_ATT_native.nii")
                if not data_descrip["SingleDelay"] and os.path.exists(att_file):
                    other_files.append(att_file)

                # Perform coregistration
                img_coreg(target, source, other_files)

                # Rename output files with _mpr suffix
                self._rename_files(key, asl_file)

    def _rename_files(self, key: str, asl_file: str):
        """Rename coregistered files to include '_mpr' suffix."""
        perf_path = os.path.join(key, "perf")

        # Rename absolute CBF
        src = os.path.join(perf_path, f"r{asl_file}_aCBF_native.nii")
        dst = os.path.join(perf_path, f"{asl_file}_aCBF_mpr.nii")
        if os.path.exists(src):
            os.rename(src, dst)

        # Rename relative CBF
        src = os.path.join(perf_path, f"r{asl_file}_rCBF_native.nii")
        dst = os.path.join(perf_path, f"{asl_file}_rCBF_mpr.nii")
        if os.path.exists(src):
            os.rename(src, dst)

        # Rename brain mask
        src = os.path.join(perf_path, "rbrnmsk_clcu.nii")
        dst = os.path.join(perf_path, "brnmsk_clcu_mpr.nii")
        if os.path.exists(src):
            os.rename(src, dst)

        # Rename ATT map if it exists
        src = os.path.join(perf_path, f"r{asl_file}_ATT_native.nii")
        dst = os.path.join(perf_path, f"{asl_file}_ATT_mpr.nii")
        if os.path.exists(src):
            os.rename(src, dst)
