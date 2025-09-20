"""
PreclinicalAbsT1Fit
-------------------
Voxelwise absolute CBF quantification via T1 fitting (MTI-PASL style).
"""

from __future__ import annotations

import os
import logging
from typing import Dict, Any, Optional

import numpy as np
import matplotlib.pyplot as plt

from pyasl.utils.t1fit import T1fit, T1fit_function

logger = logging.getLogger(__name__)


class AbsCBF_T1Fit:
    """
    Preclinical absolute CBF via voxelwise T1 fitting (MTI-PASL style).

    This module computes an absolute CBF map using two series (global/non-selective
    and selective) and a set of inversion times (TIs). For each voxel, it fits
    T1 from the global and selective signals and applies the standard formula:

        CBF[i,j] = 4980 * (T1_glo / 2250) * (1000/T1_sel - 1000/T1_glo)

    where T1_* are in milliseconds. Optionally, a 2D mask can be applied.

    Expected Context (read/write)
    -----------------------------
    ctx["AbsData"] : np.ndarray, optional
        Input image stack shaped either (X, Y, N) or (X, Y, ..., N) where the last
        dimension enumerates frames used by sel/global indices. If not present,
        the module loads data from `params["data_path"]`.
    ctx["savedir"] : str, optional
        Output directory for saved products; defaults to current directory ".".
    ctx["absCBF"] : np.ndarray (X, Y), set by this module
        The computed absolute CBF map (milliliters/100g/min; units per your convention).

    Parameters (kwargs)
    -------------------
    data_path : str, optional
        Path to a .npy or .npz array when ctx["AbsData"] is not set.
    data_key : str, optional
        Key name inside the .npz file; if omitted, the first array is used.
    TI_list : list[float]
        Inversion times (ms) corresponding to the frames used in fitting.
    sel_index : list[int]
        Frame indices for the selective series.
    glo_index : list[int]
        Frame indices for the global (non-selective) series.
    mask_path : str, optional
        Path to a 2D numpy mask (.npy) of shape (X, Y). If provided, the
        computation is restricted to masked voxels.
    save_curves_every : int, optional, default=200
        Approximate downsampling factor to limit how many voxel curves
        are visualized in the diagnostic plot.

    Outputs (filesystem)
    --------------------
    <savedir>/curvefit.png
        A diagnostic figure with sampled voxelwise fits overlaid on data points.
    <savedir>/absCBF.npy
        The computed CBF map (X, Y).

    Logging
    -------
    INFO  : start/end, input shapes, output locations.
    DEBUG : parameters, reshaping details, sampling interval.
    ERROR : invalid shapes/indices, missing inputs, load failures.
    """

    def run(self, ctx: Dict[str, Any], **params: Any) -> None:
        # Resolve output directory
        savedir: str = ctx.get("savedir", ".")
        os.makedirs(savedir, exist_ok=True)

        # ---- Resolve input data ----
        if "AbsData" in ctx:
            data = ctx["AbsData"]
            logger.debug("Using AbsData from context with shape %s", getattr(data, "shape", None))
        else:
            data_path: Optional[str] = params.get("data_path")
            data_key: Optional[str] = params.get("data_key")
            if not data_path:
                logger.error("data_path is required when ctx['AbsData'] is not provided.")
                raise ValueError("PreclinicalAbsCBF_T1Fit requires data_path or ctx['AbsData'].")

            logger.debug("Loading data from %s (key=%s)", data_path, data_key)
            if data_path.endswith(".npz"):
                with np.load(data_path) as z:
                    data = z[data_key] if data_key else list(z.values())[0]
            else:
                data = np.load(data_path)

        if not isinstance(data, np.ndarray):
            logger.error("Loaded data is not a numpy array.")
            raise TypeError("Input data must be a numpy array.")

        # ---- Normalize to (X, Y, N) ----
        if data.ndim == 4:
            X, Y = data.shape[:2]
            N = int(np.prod(data.shape[2:]))
            data = data.reshape(X, Y, N)
            logger.debug("Reshaped 4D input to (X, Y, N) = (%d, %d, %d)", X, Y, N)
        elif data.ndim == 3:
            X, Y, N = data.shape
        else:
            logger.error("Unsupported input ndim=%d; expected 3 or 4.", data.ndim)
            raise ValueError("data must be (X, Y, N) or a higher-dim array that can be flattened.")

        # ---- Indices and TI list ----
        try:
            sel_index = np.asarray(params["sel_index"], dtype=int)
            glo_index = np.asarray(params["glo_index"], dtype=int)
            TI_list = np.asarray(params["TI_list"], dtype=float)
        except KeyError as e:
            logger.error("Missing required parameter: %s", e)
            raise

        if sel_index.ndim != 1 or glo_index.ndim != 1:
            logger.error("sel_index and glo_index must be 1D lists/arrays.")
            raise ValueError("sel_index and glo_index must be 1D lists/arrays.")
        if TI_list.ndim != 1:
            logger.error("TI_list must be 1D.")
            raise ValueError("TI_list must be 1D.")
        if not (len(sel_index) == len(glo_index) == len(TI_list)):
            logger.error("Length mismatch among sel_index (%d), glo_index (%d), TI_list (%d).",
                         len(sel_index), len(glo_index), len(TI_list))
            raise ValueError("sel_index, glo_index, and TI_list must have the same length.")

        # ---- Slice into selective / global series ----
        try:
            sel = data[:, :, sel_index]
            glo = data[:, :, glo_index]
        except Exception as e:
            logger.error("Failed to slice data with provided indices: %s", e)
            raise

        # ---- Optional mask ----
        mask_path = params.get("mask_path")
        if mask_path:
            logger.debug("Applying mask from %s", mask_path)
            mask = np.load(mask_path)
            if mask.shape != (X, Y):
                logger.error("Mask shape %s does not match image XY (%d, %d).", mask.shape, X, Y)
                raise ValueError("mask shape must match the input spatial shape (X, Y).")
            sel = sel * mask[:, :, None]
            glo = glo * mask[:, :, None]

        logger.info("Starting absolute CBF T1-fit on data (X=%d, Y=%d, N=%d).", X, Y, N)

        # ---- Voxelwise T1 fitting ----
        CBF = np.zeros((X, Y), dtype=float)
        total_voxels = X * Y
        sample_every = max(1, total_voxels // int(params.get("save_curves_every", 200)))
        logger.debug("Sampling interval for curve plot: every %d voxels (total=%d).",
                     sample_every, total_voxels)

        plt.figure()
        plotted = 0

        for i in range(X):
            for j in range(Y):
                # Skip background/empty voxels based on the first global TI
                if glo[i, j, 0] == 0:
                    continue

                # Fit T1 for global and selective signals at this voxel
                xa = T1fit(TI_list, glo[i, j])
                xb = T1fit(TI_list, sel[i, j])
                T1_glo, T1_sel = xa[1], xb[1]  # assuming T1 is the 2nd parameter

                # Optionally scatter/plot a subset for diagnostics
                idx = i * Y + j
                if (idx % sample_every) == 0:
                    plt.scatter(TI_list, glo[i, j])
                    plt.plot(TI_list, np.abs(T1fit_function(TI_list, *xa)), linewidth=0.5)
                    plt.scatter(TI_list, sel[i, j])
                    plt.plot(TI_list, np.abs(T1fit_function(TI_list, *xb)), linewidth=0.5)
                    plotted += 1

                # Apply absolute CBF formula (units depend on your T1 convention)
                CBF[i, j] = 4980.0 * (T1_glo / 2250.0) * (1000.0 / T1_sel - 1000.0 / T1_glo)

        # ---- Save outputs ----
        curve_png = os.path.join(savedir, "curvefit.png")
        cbf_npy = os.path.join(savedir, "absCBF.npy")

        plt.savefig(curve_png)
        plt.close()
        np.save(cbf_npy, CBF)

        # ---- Update context & log ----
        ctx["absCBF"] = CBF
        logger.info("Absolute CBF computed. Saved map to %s; diagnostic plot to %s. Sampled %d voxels.",
                    cbf_npy, curve_png, plotted)
