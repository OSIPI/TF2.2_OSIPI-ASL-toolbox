"""
DeepASL (DLASL) modular pipeline runner.

Executes DeepASL-related processing steps as defined in a YAML config:
  - name: DLASLBuildMask
    params: { ... }
  - name: DLASLDenoiseCBF
    params: { ... }

Inputs
------
root : str
    Dataset root directory used by steps and for writing `derivatives/`.
config_path : str
    Path to YAML file with a top-level `steps` list.

Notes
-----
Each step is invoked as `module.run(data_descrip, params)`.
`params["root"]` is injected when absent for convenience.

Logging
-------
INFO:  pipeline start/end, per-step start.
DEBUG: resolved parameters.
ERROR: unknown step or missing configuration.
"""

from __future__ import annotations
import os
import yaml
import logging

from pyasl.utils.utils import read_data_description
from pyasl.modules.dlasl_build_mask import DLASLBuildMask
from pyasl.modules.dlasl_denoise_cbf import DLASLDenoiseCBF

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    """Load YAML configuration from `path`."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


DLASL_MODULE_MAP = {
    "DLASLBuildMask": DLASLBuildMask(),
    "DLASLDenoiseCBF": DLASLDenoiseCBF(),
}


def run_dlasl_pipeline(root: str, config_path: str) -> None:
    """
    Run the DeepASL pipeline according to the YAML `steps` list.

    Parameters
    ----------
    root : str
        Dataset root directory.
    config_path : str
        Path to YAML config.
    """
    logger.info("Starting modular DeepASL pipeline...")
    data_descrip = read_data_description(root)
    config = load_config(config_path)
    steps = config.get("steps", [])
    if not steps:
        logger.error("Config has no `steps`.")
        raise ValueError("Config must include a top-level `steps` list.")

    for step in steps:
        name = step.get("name")
        params = step.get("params", {}) or {}
        params.setdefault("root", root)

        logger.info(">>> Running step: %s", name)
        logger.debug("Step params: %s", params)

        mod = DLASL_MODULE_MAP.get(name)
        if mod is None:
            logger.error("Unknown step: %s", name)
            raise ValueError(f"Unknown step: {name}")

        mod.run(data_descrip, params)

    outdir = os.path.join(root, "derivatives")
    logger.info("DeepASL pipeline completed.")
    logger.info("See results under %s", outdir)
