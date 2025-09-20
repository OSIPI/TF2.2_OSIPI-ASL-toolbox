"""
PreclinicalBrainMask
--------------------
Create in-brain mask using mricloud_inbrain if available.
"""

import numpy as np, os
from pyasl.utils.plotting import get_plot_array, plot_save_fig
from scipy.ndimage import binary_erosion, binary_dilation, binary_fill_holes, label
import logging
logger = logging.getLogger(__name__)

class BrainMask():
    """
    Preclinical brain mask generation.

    This class provides methods to generate a brain mask from preclinical MRI images,
    using a robust thresholding and morphological approach inspired by mricloud_inbrain.

    Methods
    -------
    mricloud_inbrain(imgvol: np.ndarray, thre: float, ero_lyr: int, dlt_lyr: int) -> np.ndarray
        Generate a brain mask from a 3D image volume using adaptive thresholding and
        morphological operations (erosion, dilation, hole filling, and largest component selection).

    run(ctx, **p)
        Main entry point for mask generation. Expects the context to provide:
            - "savedir": Output directory (required)
            - "ImageCtr": 4D image array (required)
        Optional parameters:
            - thres: Threshold scaling factor (default 0.2)
            - open_iter: Number of erosion iterations (default 2)
            - close_iter: Number of dilation iterations (default 2)
        The resulting mask is stored in ctx["BrainMask"].
    """
    def mricloud_inbrain(self, imgvol: np.ndarray, thre: float, ero_lyr: int, dlt_lyr: int):
        lowb = 0.25
        highb = 0.75

        Nx, Ny, Nz = imgvol.shape
        tmpmat = imgvol[
            round(Nx * lowb) : round(Nx * highb),
            round(Ny * lowb) : round(Ny * highb),
            round(Nz * lowb) : round(Nz * highb),
        ]
        tmpvox = tmpmat[tmpmat > 0]
        thre0 = np.mean(tmpvox) * thre

        mask1 = np.zeros_like(imgvol)
        mask1[imgvol > thre0] = 1

        mask2 = np.zeros_like(mask1)
        se = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        for ii in range(Nz):
            slice0 = mask1[:, :, ii]
            slice1 = slice0
            for ie in range(ero_lyr):
                slice1 = binary_erosion(slice1, structure=se)

            labeled_array, num_features = label(slice1, structure=se)
            sizes = np.bincount(labeled_array.ravel())
            sizes[0] = 0
            max_label = sizes.argmax()
            slice2 = np.zeros_like(slice1)
            slice2[labeled_array == max_label] = 1

            slice2 = binary_fill_holes(slice2)
            for id in range(dlt_lyr):
                slice2 = binary_dilation(slice2, structure=se)

            mask2[:, :, ii] = slice2

        brainmask = mask2.astype(np.uint8)
        return brainmask
    
    def run(self, ctx, **p):
        savedir = ctx.get_required("savedir")
        ctr = ctx.get_required("ImageCtr")
        th = float(p.get("thres", 0.2))
        op = int(p.get("open_iter", 2)); cl = int(p.get("close_iter", 2))
        mask = self.mricloud_inbrain(np.mean(ctr, axis=3), th, op, cl)
        ctx["BrainMask"] = mask
        if "relCBF" in ctx:
            Z = mask.shape[2]
            cols = int(np.floor(np.sqrt(Z))) or 1
            rows = int(np.ceil(Z / cols))
            plot_save_fig(get_plot_array(ctx["relCBF"] * mask, [cols, rows]), "Masked CBF", os.path.join(savedir, "MaskedCBF.png"))