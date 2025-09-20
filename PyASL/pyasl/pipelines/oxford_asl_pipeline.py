"""
OxfordASL modular pipeline runner.

This orchestrates a two-step OxfordASL flow as configured in YAML:
  - name: OxfordASLSplitM0
    params: { ... }
  - name: OxfordASLRun
    params: { useStructural: true, useCalibration: false, ... }

Environment
-----------
The runner provides a minimal/robust env for CLI tools:
- disables color, fixes TERM/locale, and sets a temp dir.
Users may extend/override via `params["env"]` (merged).

Logging
-------
INFO:  pipeline start/end, per-step start, OxfordASLRun summary.
DEBUG: merged env, resolved params.
ERROR: unknown step or runtime failures.
"""

from __future__ import annotations
import os
import yaml
import logging
from typing import Dict, Optional

from pyasl.utils.utils import read_data_description
from pyasl.modules.oxford_asl_split_m0 import OxfordASLSplitM0
from pyasl.modules.oxford_asl_run import OxfordASLRun

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    """Load YAML configuration from `path`."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


OXFORD_ASL_MODULE_MAP = {
    "OxfordASLSplitM0": OxfordASLSplitM0(),
    "OxfordASLRun": OxfordASLRun(),
}


def _default_env() -> Dict[str, str]:
    """Return a robust, non-colored CLI environment with a dedicated TMPDIR."""
    return {
        "TMPDIR": os.path.expanduser("~/tmp_oxasl"),
        "NO_COLOR": "1",
        "CLICOLOR": "0",
        "CLICOLOR_FORCE": "0",
        "TERM": "dumb",
        "LC_ALL": "C",
        "LANG": "C",
    }


def _merge_env(user_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Merge user-provided env with defaults and ensure TMPDIR exists."""
    env = _default_env()
    if user_env:
        env.update(user_env)
    os.makedirs(env["TMPDIR"], exist_ok=True)
    logger.debug("Merged environment: %s", env)
    return env


def run_oxford_asl_pipeline(root: str, config_path: str) -> None:
    """
    Run the OxfordASL pipeline defined by a YAML `steps` list.

    Parameters
    ----------
    root : str
        Dataset root directory.
    config_path : str
        Path to YAML config.
    """
    logger.info("Starting modular OxfordASL pipeline...")
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

        # Stabilize defaults specifically for OxfordASLRun
        if name == "OxfordASLRun":
            params.setdefault("useStructural", True)
            params.setdefault("useCalibration", False)
            params.setdefault("ibf", "rpt")
            params.setdefault("debug", True)
            params["env"] = _merge_env(params.get("env"))

        logger.info(">>> Running step: %s", name)
        logger.debug("Step params: %s", params)

        mod = OXFORD_ASL_MODULE_MAP.get(name)
        if mod is None:
            logger.error("Unknown step: %s", name)
            raise ValueError(f"Unknown step: {name}")

        ret = mod.run(data_descrip, params)

        # Friendly summary for OxfordASLRun salvage info (if provided)
        if name == "OxfordASLRun" and isinstance(ret, dict):
            outdir = ret.get("oxford_asl_out")
            created = ret.get("created") or []
            used = ret.get("salvaged_from")
            logger.info("[OxfordASLRun] outdir: %s", outdir)
            if created:
                logger.info("[OxfordASLRun] salvaged %d files", len(created))
                for p in created:
                    logger.debug("  salvaged: %s", p)
                if used:
                    logger.info("[OxfordASLRun] from: %s", used)
            else:
                logger.info("[OxfordASLRun] no salvage needed (final files written normally)")

    outdir = os.path.join(root, "derivatives")
    logger.info("OxfordASL modular pipeline completed.")
    logger.info("See results under %s", outdir)
