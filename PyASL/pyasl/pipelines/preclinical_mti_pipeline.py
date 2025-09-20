"""
Preclinical MTI-PASL pipeline (ASLTBX-like executor), unified-entry version.

This runner now takes (data_dir, config_path, ...). Any relative paths found
in step params (e.g., 'path', 'savedir', etc.) will be resolved against
`data_dir`. Absolute paths are left intact.

Example
-------
from pyasl.pipelines.run_pipeline import run_pipeline
run_pipeline("pyasl/data/human_single_delay", "pyasl/configs/testmti.yaml")

YAML
----
type: mti
steps:
  - module: NIfTILoader
    params:
      path: "data/preclinical_MTI_PASL/FAIREPI.img"   # resolved against data_dir
      savedir: "data/preclinical_MTI_PASL/results_mti"
  - module: AbsCBF_T1Fit
    params: { ... }
  - module: SaveOutputs
"""

from __future__ import annotations
import importlib
import logging
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ----------------------------- Context -----------------------------

class Context(dict):
    """Lightweight dict-like context with required-key helper."""
    def get_required(self, key: str):
        if key not in self:
            raise KeyError(f"Context missing required key: {key}")
        return self[key]

# ------------------------------ Steps ------------------------------

from pyasl.modules.preclinical_loader_nifti import NIfTILoader
from pyasl.modules.preclinical_abs_t1fit import AbsCBF_T1Fit
from pyasl.modules.save_outputs import SaveOutputs
# Optional future steps:
# from pyasl.modules.brain_mask import BrainMask
# from pyasl.modules.motion_check import MotionCheck

MODULE_MAP_MTI: Dict[str, Any] = {
    "NIfTILoader": NIfTILoader(),
    "AbsCBF_T1Fit": AbsCBF_T1Fit(),
    "SaveOutputs": SaveOutputs(),
}

# --------------------------- Utilities -----------------------------

def _import_class(fqcn: str):
    """Import a class from a fully-qualified class name string."""
    mod, cls = fqcn.rsplit(".", 1)
    logger.debug("Dynamically importing %s from %s", cls, mod)
    return getattr(importlib.import_module(mod), cls)

def _load_config(path: str) -> dict:
    """Load YAML configuration from `path`."""
    with open(path, "r") as f:
        return yaml.safe_load(f)

# ---- path resolution: resolve relative strings against data_dir ----

_PATHY_KEYS = {
    "path", "paths", "in", "infile", "infiles", "outfile", "out", "dir",
    "savedir", "basedir", "root", "mask", "anat", "asl", "m0", "log", "logdir"
}

def _looks_like_path(s: str) -> bool:
    # A conservative heuristic to avoid touching non-path values
    if any(tok in s for tok in ("/", "\\", ".nii", ".nii.gz", ".img", ".hdr", ".nii.gz")):
        return True
    return False

def _resolve_one(s: str, base: Path) -> str:
    # support {root} / ${root} placeholder
    if "{root}" in s or "${root}" in s:
        s = s.replace("${root}", "{root}").format(root=str(base))
    p = Path(s)
    if p.is_absolute():
        return str(p)
    return str((base / p).resolve())

def _resolve_paths_in_params(obj: Any, base: Path, parent_key: Optional[str] = None) -> Any:
    if isinstance(obj, dict):
        return {k: _resolve_paths_in_params(v, base, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_paths_in_params(v, base, parent_key) for v in obj]
    if isinstance(obj, str):
        if (parent_key and parent_key in _PATHY_KEYS) or _looks_like_path(obj):
            try:
                resolved = _resolve_one(obj, base)
                logger.debug("Resolved path: '%s' -> '%s'", obj, resolved)
                return resolved
            except Exception:
                return obj
        return obj
    return obj

# ------------------------------ Runner -----------------------------

def run_preclinical_mti_pipeline(
    data_dir: str,
    config_path: str,
    ctx: Optional[Context] = None,
    module_map: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
) -> Context:
    """
    Execute the MTI-PASL pipeline with unified entry (data_dir, config_path).

    Parameters
    ----------
    data_dir : str
        Dataset root directory; relative paths in YAML will be resolved against this.
    config_path : str
        Path to YAML config with a top-level `steps` list.
    ctx : Optional[Context]
        Shared context; if None a new one is created. `ctx['root']` will be set.
    module_map : Optional[Dict[str, Any]]
        Override mapping from short names to module instances.
    verbose : bool
        If True, log per-step progress at INFO level.
    """
    module_map = MODULE_MAP_MTI if module_map is None else module_map
    conf = _load_config(config_path)
    steps = conf.get("steps", [])
    if not steps:
        logger.error("Config has no `steps`.")
        raise ValueError("YAML must include a top-level `steps` list.")

    root_path = Path(data_dir).resolve()
    cfg_dir = Path(config_path).resolve().parent

    ctx = Context(ctx or {})
    ctx["root"] = str(root_path)
    ctx.setdefault("config_dir", str(cfg_dir))

    if verbose:
        logger.info("Starting preclinical MTI-PASL modular pipeline...")
        logger.debug("data_dir=%s  config=%s", root_path, config_path)

    for i, step in enumerate(steps, 1):
        name = step.get("name") or step.get("module") or step.get("class")
        params = step.get("params", {}) or {}
        if name is None:
            logger.error("Step #%d missing 'name'/'module'/'class'", i)
            raise ValueError(f"Step #{i} missing 'name'/'module'/'class'")

        # Resolve any relative paths in params against data_dir
        params = _resolve_paths_in_params(params, root_path)

        # Resolve step implementation: short name or fully-qualified class
        if name in module_map:
            mod = module_map[name]
            shown = name
        else:
            if "." not in name:
                available = ", ".join(sorted(module_map.keys()))
                logger.error("Unknown step '%s'. Available: %s", name, available)
                raise ValueError(f"Unknown step '{name}'. Available: {available}")
            cls = _import_class(name)
            mod = cls()
            shown = name

        if verbose:
            logger.info(">>> [%d/%d] Running step: %s", i, len(steps), shown)
        logger.debug("Step params: %s", params)

        # Step convention: run(ctx, **params)
        mod.run(ctx, **params)

    if verbose:
        logger.info("MTI-PASL pipeline completed.")
