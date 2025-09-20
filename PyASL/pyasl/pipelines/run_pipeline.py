"""
Unified pipeline runner.

This script provides a single entry point to launch different ASL
processing pipelines based on a YAML configuration.

Example (Python)
----------------
    from pyasl.pipelines.run_pipeline import run_pipeline
    run_pipeline("pyasl/data/human_single_delay", "pyasl/configs/unified.yaml")

Example (CLI)
-------------
    python -m pyasl.pipelines.run_pipeline \
        --input pyasl/data/human_single_delay \
        --config pyasl/configs/unified.yaml

YAML example
------------
    type: asltbx
    steps:
      - name: ResetOrientation
      - name: Realign
      - name: Coregister
      - name: Smooth
        params: { fwhm: [6, 6, 6] }
      - name: CreateMask
        params: { thres: 0.05 }
      - name: PerfusionQuantify
        params:
          QuantFlag: 0
          M0wmcsf: null
          MaskFlag: true
          MeanFlag: true
          BOLDFlag: false
          PerfFlag: false
          SubtractionType: 0
          SubtrationOrder: 1
          Timeshift: 0.5
"""
from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _fmt = logging.Formatter("[%(levelname)s] %(message)s")
    _h.setFormatter(_fmt)
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

# Explicit registry mapping `type` in YAML -> (module_path, function_name)
_PIPELINE_REGISTRY: Dict[str, Tuple[str, str]] = {
    "mricloud": ("pyasl.pipelines.asl_mricloud_pipeline", "run_mricloud_pipeline"),
    "asltbx": ("pyasl.pipelines.asltbx_pipeline", "run_pipeline"),
    "oxford_asl": ("pyasl.pipelines.oxford_asl_pipeline", "run_oxford_asl_pipeline"),
    "mti": ("pyasl.pipelines.preclinical_mti_pipeline", "run_preclinical_mti_pipeline"),
    "pcasl": ("pyasl.pipelines.preclinical_pcasl_pipeline", "run_preclinical_pcasl_pipeline"),
    "dlasl": ("pyasl.pipelines.dlasl_pipeline", "run_dlasl_pipeline"),
    "custom": ("pyasl.pipelines.custom_pipeline", "run_custom_pipeline"),
}


def _convention_candidates(pkey: str) -> Tuple[str, Tuple[str, ...]]:
    """
    Return fallback (module, candidate functions) for a given key.

    If a type is not in the registry, we try:
      module = pyasl.pipelines.<type>_pipeline
      function = run_<type>_pipeline or run_pipeline
    """
    base = f"pyasl.pipelines.{pkey}_pipeline"
    return base, (f"run_{pkey}_pipeline", "run_pipeline")


def _load_yaml(config_path: Path) -> dict:
    """Load YAML configuration and ensure it is a mapping."""
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a YAML mapping, got {type(data)}")
    return data


def _resolve_runner(pipeline_type: str) -> Callable[[str, str], object]:
    """
    Find the correct runner(data_dir, config_path) for a pipeline type.

    Search order:
      1. Explicit registry.
      2. Convention-based lookup.
    """
    key = pipeline_type.strip().lower()

    # Check registry first
    if key in _PIPELINE_REGISTRY:
        mod_name, func_name = _PIPELINE_REGISTRY[key]
        logger.info(f"Using registry: {key} -> {mod_name}.{func_name}()")
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, func_name, None)
        if not callable(fn):
            raise AttributeError(f"{mod_name}.{func_name} not found or not callable")
        return fn

    # Fallback: convention
    mod_name, func_candidates = _convention_candidates(key)
    logger.info(f"Trying convention: module={mod_name}, funcs={func_candidates}")
    try:
        mod = importlib.import_module(mod_name)
    except ModuleNotFoundError:
        mod = None

    if mod:
        for fname in func_candidates:
            fn = getattr(mod, fname, None)
            if callable(fn):
                logger.info(f"Resolved by convention: {mod_name}.{fname}()")
                return fn

    # Nothing worked
    available = ", ".join(sorted(_PIPELINE_REGISTRY.keys()))
    raise ValueError(
        f"Unknown pipeline type '{pipeline_type}'. "
        f"Available types: {available}. "
        f"Or provide a module '{mod_name}' with a callable in {func_candidates}."
    )


def run_pipeline(input_dir: str, config_path: str) -> object:
    """
    Main entry point.

    Read the YAML `type`, resolve its runner, and forward
    (input_dir, config_path) to the target pipeline.
    """
    input_p = Path(input_dir)
    cfg_p = Path(config_path)

    if not input_p.exists():
        raise FileNotFoundError(f"Input dir not found: {input_p}")
    if not cfg_p.exists():
        raise FileNotFoundError(f"Config not found: {cfg_p}")

    cfg = _load_yaml(cfg_p)
    ptype = cfg.get("type")
    if not ptype:
        raise KeyError("Config YAML must include a top-level 'type' field.")

    logger.info(f"Pipeline type: {ptype}")
    runner = _resolve_runner(ptype)

    # Forward arguments as-is
    logger.info(f"Dispatching to runner with input='{input_p}', config='{cfg_p}'")
    return runner(str(input_p), str(cfg_p))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Unified ASL pipeline runner")
    parser.add_argument("--input", required=True, help="Input data directory")
    parser.add_argument("--config", required=True, help="YAML config path")
    args = parser.parse_args()

    _ = run_pipeline(args.input, args.config)
