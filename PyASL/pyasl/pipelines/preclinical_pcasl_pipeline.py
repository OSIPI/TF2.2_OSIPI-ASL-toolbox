"""
Preclinical PCASL pipeline (ASLTBX-like executor), unified-entry version.

This runner now takes (data_dir, config_path, ...). Any relative paths in step
params (e.g., 'savedir', 'mask', etc.) will be resolved against `data_dir`.
Absolute paths are left intact.

Special handling:
- If a step param contains `root`, it will be overridden to `data_dir`.
- If a param value equals the string "from_meta", we will try to read the same
  key from ctx (e.g., TR: from_meta -> ctx["TR"]).

Example
-------
from pyasl.pipelines.run_pipeline import run_pipeline
run_pipeline("pyasl/data/preclinical_pCASL", "pyasl/configs/testpcasl.yaml")

YAML
----
type: pcasl
steps:
  - module: BrukerLoader
    params: { expno: 18, prono: 1 }  # root 不需要写
  - module: SteadyStateTrim
    params: { trim: 2 }
  - module: ControlLabelSplit
    params: { control_first: true }
  - module: MotionCheck
  - module: DiffImage
  - module: ComputeM0
    params: { TR: from_meta, T1t: 1900 }
  - module: SlicePLDAdjust
    params: { SGap: 31, T1blood: 2800 }
  - module: CBFRelative
    params: { vmax: 10 }
  - module: BrainMask
    params: { thres: 0.2, open_iter: 2, close_iter: 2 }
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

from pyasl.modules.preclinical_loader_bruker import BrukerLoader
from pyasl.modules.preclinical_loader_nifti import NIfTILoader
from pyasl.modules.preclinical_steady_state_trim import SteadyStateTrim
from pyasl.modules.preclinical_control_label_split import ControlLabelSplit
from pyasl.modules.preclinical_motion_check import MotionCheck
from pyasl.modules.preclinical_diff_image import DiffImage
from pyasl.modules.preclinical_compute_m0 import ComputeM0
from pyasl.modules.preclinical_slice_pld_adjust import SlicePLDAdjust
from pyasl.modules.preclinical_cbf_relative import CBFRelative
from pyasl.modules.preclinical_brain_mask import BrainMask
from pyasl.modules.preclinical_abs_t1fit import AbsCBF_T1Fit
from pyasl.modules.save_outputs import SaveOutputs

MODULE_MAP: Dict[str, Any] = {
    "BrukerLoader": BrukerLoader(),
    "NIfTILoader": NIfTILoader(),
    "SteadyStateTrim": SteadyStateTrim(),
    "ControlLabelSplit": ControlLabelSplit(),
    "MotionCheck": MotionCheck(),
    "DiffImage": DiffImage(),
    "ComputeM0": ComputeM0(),
    "SlicePLDAdjust": SlicePLDAdjust(),
    "CBFRelative": CBFRelative(),
    "BrainMask": BrainMask(),
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
    if any(tok in s for tok in ("/", "\\", ".nii", ".nii.gz", ".img", ".hdr")):
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

# ---- from_meta injection: replace "from_meta" with ctx[key] if present ----

def _inject_from_meta(params: Any, ctx: Context, parent_key: Optional[str] = None) -> Any:
    if isinstance(params, dict):
        return {k: _inject_from_meta(v, ctx, k) for k, v in params.items()}
    if isinstance(params, list):
        return [_inject_from_meta(v, ctx, parent_key) for v in params]
    if isinstance(params, str) and params == "from_meta" and parent_key:
        return ctx.get(parent_key, params)
    return params

# ------------------------------ Runner -----------------------------

def run_preclinical_pcasl_pipeline(
    data_dir: str,
    config_path: str,
    ctx: Optional[Context] = None,
    module_map: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
) -> Context:
    """
    Execute the preclinical PCASL pipeline with unified entry (data_dir, config_path).
    """
    module_map = MODULE_MAP if module_map is None else module_map
    conf = _load_config(config_path)
    steps = conf.get("steps", [])
    if not steps:
        logger.error("Config has no `steps`.")
        raise ValueError("YAML must have a top-level `steps` list")

    root_path = Path(data_dir).resolve()
    cfg_dir = Path(config_path).resolve().parent

    ctx = Context(ctx or {})
    ctx["root"] = str(root_path)
    ctx.setdefault("config_dir", str(cfg_dir))

    if verbose:
        logger.info("Starting preclinical ASL modular pipeline...")
        logger.debug("data_dir=%s  config=%s", root_path, config_path)

    for i, step in enumerate(steps, 1):
        name = step.get("name") or step.get("module") or step.get("class")
        params = step.get("params", {}) or {}
        if name is None:
            logger.error("Step #%d missing 'name'/'module'/'class'", i)
            raise ValueError(f"Step #{i} missing 'name'/'module'/'class'")

        if isinstance(params, dict) and "root" in params:
            old = params.get("root")
            if str(old) != str(root_path):
                logger.info("Overriding step '%s' param 'root': %s -> %s", name, old, root_path)
            params["root"] = str(root_path)

        params = _resolve_paths_in_params(params, root_path)

        params = _inject_from_meta(params, ctx)

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
        
        if "root" not in params:
            params["root"] = str(root_path)  # root_path = Path(data_dir).resolve()
            logger.debug("Injected default 'root' for step %s: %s", name, params["root"])

        mod.run(ctx, **params)

    if verbose:
        logger.info("ASL preclinical pipeline completed.")
