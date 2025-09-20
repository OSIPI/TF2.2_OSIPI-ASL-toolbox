"""
ASLToolbox-style modular pipeline runner.

This pipeline executes classic ASL preprocessing and quantification steps
defined in a YAML config. The YAML must contain `steps:` entries such as:
  - name: ResetOrientation
    params: { ... }

Inputs
------
root : str
    Dataset root directory to read inputs and write outputs under
    `asltbx/derivatives` (module-dependent).
config_path : str
    Path to YAML configuration file.

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

from pyasl.modules.asltbx_reset_orientation import ResetOrientation
from pyasl.modules.asltbx_realign import Realign
from pyasl.modules.asltbx_coregister import Coregister
from pyasl.modules.asltbx_smooth import Smooth
from pyasl.modules.asltbx_create_mask import CreateMask
from pyasl.modules.asltbx_perfusion_quantify import PerfusionQuantify
from pyasl.utils.utils import read_data_description

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    """Load YAML configuration from `path`."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


MODULE_MAP = {
    "ResetOrientation": ResetOrientation(),
    "Realign": Realign(),
    "Coregister": Coregister(),
    "Smooth": Smooth(),
    "CreateMask": CreateMask(),
    "PerfusionQuantify": PerfusionQuantify(),
}


def run_pipeline(root: str, config_path: str) -> None:
    """
    Run the ASLToolbox pipeline in the order specified by the YAML config.

    Parameters
    ----------
    root : str
        Dataset root directory.
    config_path : str
        Path to YAML config containing a `steps` list.
    """
    logger.info("Starting modular ASL pipeline...")
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

        mod = MODULE_MAP.get(name)
        if mod is None:
            logger.error("Unknown step: %s", name)
            raise ValueError(f"Unknown step: {name}")

        mod.run(data_descrip, params)

    outdir = os.path.join(root, "asltbx", "derivatives")
    logger.info("ASL Toolbox pipeline completed.")
    logger.info("See results under %s", outdir)
