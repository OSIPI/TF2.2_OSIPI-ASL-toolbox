"""
MRICloud ASL modular pipeline runner.

This pipeline executes a series of MRICloud-specific ASL processing steps
defined in a YAML config. The YAML must contain a top-level `steps:` list
with items in the form:
  - name: <ModuleName>
    params: { ... }            # optional per-step parameters

Inputs
------
root : str
    Dataset root directory where `data_description.json` (or equivalent)
    can be found and outputs will be written under `derivatives/`.
config_path : str
    Path to a YAML configuration file.

Behavior
--------
- Loads a data description from `root`.
- Iterates `steps` in order and calls each module's `.run(data_descrip, params)`.
- Writes module results below `root/derivatives` (module-dependent).

Logging
-------
INFO:  pipeline start/end, per-step start.
DEBUG: resolved parameters.
ERROR: unknown step or runtime failures.
"""

from __future__ import annotations
import os
import yaml
import logging

from pyasl.modules.mricloud_rescale import MRICloudRescale
from pyasl.modules.asltbx_realign import Realign
from pyasl.modules.mricloud_calculate_diffmap import MRICloudCalculateDiffmap
from pyasl.modules.mricloud_calculate_M0 import MRICloudCalculateM0
from pyasl.modules.mricloud_calculate_CBF import MRICloudCalculateCBF
from pyasl.modules.mricloud_multidelay_calculate_M0 import MRICloudMultidelayCalculateM0
from pyasl.modules.mricloud_multidelay_calculate_CBFATT import MRICloudMultidelayCalculateCBFATT
from pyasl.modules.mricloud_read_mpr import MRICloudReadMPR
from pyasl.modules.mricloud_coreg_mpr import MRICloudCoregMPR
from pyasl.modules.mricloud_t1roi_CBFaverage import MRICloudT1ROICBFAverage
from pyasl.utils.utils import read_data_description

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    """Load YAML configuration from `path`."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


MRI_CLOUD_MODULE_MAP = {
    "MRICloudRescale": MRICloudRescale(),
    "Realign": Realign(),  # reuse SPM Realign module
    "MRICloudCalculateDiffmap": MRICloudCalculateDiffmap(),
    "MRICloudCalculateM0": MRICloudCalculateM0(),
    "MRICloudCalculateCBF": MRICloudCalculateCBF(),
    "MRICloudMultidelayCalculateM0": MRICloudMultidelayCalculateM0(),
    "MRICloudMultidelayCalculateCBFATT": MRICloudMultidelayCalculateCBFATT(),
    "MRICloudReadMPR": MRICloudReadMPR(),
    "MRICloudCoregMPR": MRICloudCoregMPR(),
    "MRICloudT1ROICBFAverage": MRICloudT1ROICBFAverage(),
}


def run_mricloud_pipeline(root: str, config_path: str) -> None:
    """
    Run the MRICloud ASL pipeline using the module map and a YAML config.

    Parameters
    ----------
    root : str
        Dataset root directory.
    config_path : str
        Path to YAML config containing a `steps` list.
    """
    logger.info("Starting modular MRICloud ASL pipeline...")
    data_descrip = read_data_description(root)
    config = load_config(config_path)
    steps = config.get("steps", [])
    if not steps:
        logger.error("Config has no `steps`.")
        raise ValueError("Config must include a top-level `steps` list.")

    for step in steps:
        name = step.get("name")
        params = step.get("params", {}) or {}
        logger.info(">>> Running step: %s", name)
        logger.debug("Step params: %s", params)

        mod = MRI_CLOUD_MODULE_MAP.get(name)
        if mod is None:
            logger.error("Unknown step: %s", name)
            raise ValueError(f"Unknown step: {name}")

        mod.run(data_descrip, params)

    outdir = os.path.join(root, "derivatives")
    logger.info("MRICloud modular pipeline completed.")
    logger.info("See results under %s", outdir)
