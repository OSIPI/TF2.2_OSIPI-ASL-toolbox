"""
custom_pipeline.py

Implements a flexible YAML-driven pipeline for ASL data processing.

- Loads a YAML configuration describing ordered processing steps.
- Dynamically resolves each step to a Python class (built-in or user-provided).
- Passes a shared Context object between steps so that results can be reused.
- Supports resolving relative file paths and injecting metadata from Context.
"""

from __future__ import annotations
import importlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

logger = logging.getLogger(__name__)


class Context(dict):
    """
    A lightweight container for pipeline state.

    Behaves like a dict but adds `get_required()` to enforce
    the presence of mandatory keys.
    """

    def get_required(self, key: str):
        """Return value for `key`, or raise if missing."""
        if key not in self:
            raise KeyError(f"Context missing required key: {key}")
        return self[key]


def _load_yaml(path: str) -> dict:
    """Load a YAML configuration file into a dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _fq_import_class(fqcn: str):
    """
    Import a class by fully qualified name.

    Example
    -------
    >>> _fq_import_class("pkg.module.ClassName")
    """
    mod, cls = fqcn.rsplit(".", 1)
    return getattr(importlib.import_module(mod), cls)


def _normkey(s: str) -> str:
    """Normalize a step name to lowercase alphanumeric."""
    return "".join(ch for ch in s.lower() if ch.isalnum())


# Keys that likely refer to paths (used by _resolve_paths)
_PATHY_KEYS = {
    "path", "paths", "in", "infile", "infiles", "outfile", "out", "dir",
    "savedir", "basedir", "root", "mask", "anat", "asl", "m0", "log", "logdir"
}


def _looks_like_path(s: str) -> bool:
    """Heuristically decide if a string looks like a file path."""
    return any(t in s for t in ("/", "\\", ".nii", ".nii.gz", ".img", ".hdr"))


def _resolve_one(s: str, base: Path) -> str:
    """Resolve a single path against a base directory."""
    if "{root}" in s or "${root}" in s:
        s = s.replace("${root}", "{root}").format(root=str(base))
    p = Path(s)
    return str(p if p.is_absolute() else (base / p).resolve())


def _resolve_paths(obj: Any, base: Path, parent: Optional[str] = None) -> Any:
    """
    Recursively resolve paths in a dict/list/str.

    Any value whose key is in `_PATHY_KEYS` or looks like a path
    will be converted to an absolute path.
    """
    if isinstance(obj, dict):
        return {k: _resolve_paths(v, base, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_paths(v, base, parent) for v in obj]
    if isinstance(obj, str):
        if (parent and parent in _PATHY_KEYS) or _looks_like_path(obj):
            try:
                return _resolve_one(obj, base)
            except Exception:
                return obj
    return obj


def _inject_from_meta(obj: Any, ctx: Context, parent: Optional[str] = None) -> Any:
    """
    Replace 'from_meta' tokens in a structure with values from Context.
    """
    if isinstance(obj, dict):
        return {k: _inject_from_meta(v, ctx, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_inject_from_meta(v, ctx, parent) for v in obj]
    if isinstance(obj, str) and obj == "from_meta" and parent:
        return ctx.get(parent, obj)
    return obj


# Mapping of step aliases to (module path, class name, call style, needs_root)
_ALIAS: Dict[str, tuple[str, str, str, bool]] = {
    # --- preclinical modules ---
    _normkey("BrukerLoader"): ("pyasl.modules.preclinical_loader_bruker", "BrukerLoader", "kwargs", True),
    _normkey("NIfTILoader"): ("pyasl.modules.preclinical_loader_nifti", "NIfTILoader", "kwargs", True),
    _normkey("SteadyStateTrim"): ("pyasl.modules.preclinical_steady_state_trim", "SteadyStateTrim", "kwargs", False),
    _normkey("ControlLabelSplit"): ("pyasl.modules.preclinical_control_label_split", "ControlLabelSplit", "kwargs", False),
    _normkey("MotionCheck"): ("pyasl.modules.preclinical_motion_check", "MotionCheck", "kwargs", False),
    _normkey("DiffImage"): ("pyasl.modules.preclinical_diff_image", "DiffImage", "kwargs", False),
    _normkey("ComputeM0"): ("pyasl.modules.preclinical_compute_m0", "ComputeM0", "kwargs", False),
    _normkey("SlicePLDAdjust"): ("pyasl.modules.preclinical_slice_pld_adjust", "SlicePLDAdjust", "kwargs", False),
    _normkey("CBFRelative"): ("pyasl.modules.preclinical_cbf_relative", "CBFRelative", "kwargs", False),
    _normkey("BrainMask"): ("pyasl.modules.preclinical_brain_mask", "BrainMask", "kwargs", False),
    _normkey("AbsCBF_T1Fit"): ("pyasl.modules.preclinical_abs_t1fit", "AbsCBF_T1Fit", "kwargs", False),
    _normkey("SaveOutputs"): ("pyasl.modules.save_outputs", "SaveOutputs", "kwargs", False),

    # --- MRICloud modules ---
    _normkey("MRICloudCalculateCBF"): ("pyasl.modules.mricloud_calculate_cbf", "MRICloudCalculateCBF", "dict", False),
    _normkey("MRICloudCalculateDiffMap"): ("pyasl.modules.mricloud_calculate_diff_map", "MRICloudCalculateDiffMap", "dict", False),
    _normkey("MRICloudCalculateM0"): ("pyasl.modules.mricloud_calculate_M0", "MRICloudCalculateM0", "dict", False),
    _normkey("MRICloudCoregMPR"): ("pyasl.modules.mricloud_coreg_mpr", "MRICloudCoregMPR", "dict", False),
    _normkey("MRICloudMultidelayCalculateCBFATT"): ("pyasl.modules.mricloud_multidelay_calculate_CBFATT", "MRICloudMultidelayCalculateCBFATT", "dict", False),
    _normkey("MRICloudMultidelayCalculateM0"): ("pyasl.modules.mricloud_multidelay_calculate_M0", "MRICloudMultidelayCalculateM0", "dict", False),
    _normkey("MRICloudReadMPR"): ("pyasl.modules.mricloud_read_mpr", "MRICloudReadMPR", "dict", False),
    _normkey("MRICloudRescale"): ("pyasl.modules.mricloud_rescale", "MRICloudRescale", "dict", False),
    _normkey("MRICloudT1ROICBFAverage"): ("pyasl.modules.mricloud_t1roi_CBFaverage", "MRICloudT1ROICBFAverage", "dict", False),

    # --- dlasl ---
    _normkey("DLASLBuildMask"): ("pyasl.modules.dlasl_build_mask", "DLASLBuildMask", "dict", False),
    _normkey("DLASLDenoiseCBF"): ("pyasl.modules.dlasl_denoise_cbf", "DLASLDenoiseCBF", "dict", False),

    # --- asltbx ---
    _normkey("ResetOrientation"): ("pyasl.modules.asltbx_reset_orientation", "ResetOrientation", "dict", False),
    _normkey("Realign"): ("pyasl.modules.asltbx_realign", "Realign", "dict", False),
    _normkey("Coregister"): ("pyasl.modules.asltbx_coregister", "Coregister", "dict", False),
    _normkey("Smooth"): ("pyasl.modules.asltbx_smooth", "Smooth", "dict", False),
    _normkey("CreateMask"): ("pyasl.modules.asltbx_create_mask", "CreateMask", "dict", False),
    _normkey("PerfusionQuantify"): ("pyasl.modules.asltbx_perfusion_quantify", "PerfusionQuantify", "dict", False),

    # --- oxford ---
    _normkey("OxfordASLSplitM0"): ("pyasl.modules.oxford_asl_split_m0", "OxfordASLSplitM0", "dict", False),
    _normkey("OxfordASLRun"): ("pyasl.modules.oxford_asl_run", "OxfordASLRun", "dict", False),
}


def _resolve_impl(step_name: str):
    """
    Turn a step name or fully qualified class into an instance and metadata.

    Returns
    -------
    tuple
        (instance, shown_name, call_style, need_root)
    """
    if "." in step_name:  # direct fully-qualified import
        cls = _fq_import_class(step_name)
        return cls(), step_name, "kwargs", False

    key = _normkey(step_name)
    if key not in _ALIAS:
        raise ValueError(f"Unknown custom module '{step_name}'. "
                         f"Known: {', '.join(sorted(_ALIAS))}")
    mod_path, cls_name, style, need_root = _ALIAS[key]
    cls = getattr(importlib.import_module(mod_path), cls_name)
    return cls(), step_name, style, need_root


def _read_data_description_safe(root: Path):
    """Try to load a data description JSON/YAML if available; ignore errors."""
    try:
        from pyasl.utils.utils import read_data_description
        return read_data_description(str(root))
    except Exception:
        return {}


def run_custom_pipeline(
    data_dir: str,
    config_path: str,
    *,
    ctx: Optional[Context] = None,
    verbose: bool = True,
) -> Context:
    """
    Execute a custom ASL processing pipeline defined in a YAML file.

    Parameters
    ----------
    data_dir : str
        Root directory containing input data; relative paths in
        the YAML will be resolved against this directory.
    config_path : str
        Path to a YAML configuration with a `steps` list.
    ctx : Context, optional
        Existing context to pass through steps (default: new).
    verbose : bool, default=True
        If True, print progress messages.

    Returns
    -------
    Context
        Final pipeline context with all accumulated results.

    Raises
    ------
    ValueError
        If the configuration has no valid steps.

    Notes
    -----
    Each YAML step must specify:
      - `module` / `name` / `class` : class name or FQCN
      - `params` : optional keyword arguments.
    """
    conf = _load_yaml(config_path)
    steps = conf.get("steps") or []
    if not isinstance(steps, list) or not steps:
        raise ValueError("Custom pipeline requires a non-empty 'steps' list.")

    root = Path(data_dir).resolve()
    cfg_dir = Path(config_path).resolve().parent

    C = Context(ctx or {})
    C.setdefault("root", str(root))
    C.setdefault("config_dir", str(cfg_dir))

    if verbose:
        logger.info("Starting CUSTOM pipeline...")
        logger.debug("data_dir=%s  config=%s", root, config_path)

    # Optional: load a data description for modules needing metadata
    data_desc = _read_data_description_safe(root)

    # Iterate over pipeline steps
    for i, step in enumerate(steps, 1):
        name = step.get("module") or step.get("name") or step.get("class")
        if not name:
            raise ValueError(f"Step #{i} missing 'module'/'name'/'class'")

        raw_params = step.get("params", {}) or {}

        # 1) Expand relative paths
        params = _resolve_paths(raw_params, root)
        # 2) Replace "from_meta" tokens with context values
        params = _inject_from_meta(params, C)

        inst, shown, style, need_root = _resolve_impl(name)

        # Some modules require explicit root path
        if style == "kwargs" and need_root and "root" not in params:
            params["root"] = str(root)

        if verbose:
            logger.info(">>> [%d/%d] %s", i, len(steps), shown)
        logger.debug("Step params: %s", params)

        # Call step with appropriate interface style
        if style == "kwargs":
            inst.run(C, **params)
        elif style == "dict":
            # Remove root for dict style
            if isinstance(params, dict) and "root" in params:
                params = {k: v for k, v in params.items() if k != "root"}
            inst.run(data_desc, params)
        else:
            raise RuntimeError(f"Unknown call style: {style}")

    if verbose:
        logger.info("CUSTOM pipeline completed.")
    return C
