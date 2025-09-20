"""
PreclinicalComputeM0
--------------------
Compute M0 from control series; Mat0 = mean(ImageCtr)/ (1-exp(-TR/T1t)).
"""

import numpy as np, os
from pyasl.utils.plotting import get_plot_array, plot_save_fig
import logging
logger = logging.getLogger(__name__)

class ComputeM0():
    """Compute M0 from control series; Mat0 = mean(ImageCtr)/ (1-exp(-TR/T1t))."""
    def run(self, ctx, **p):
        logger.info("Computing M0 from control series ...")
        savedir = ctx.get_required("savedir")
        ctr = ctx.get_required("ImageCtr")
        Para = ctx.get_required("Para")
        T1t = float(p.get("T1t", 1900.0))
        TR  = float(Para["tr"]) if p.get("TR", "from_meta") == "from_meta" else float(p.get("TR"))
        M0Calib = 1 - np.exp(-TR / T1t)
        Mat0 = np.mean(ctr, axis=3) / M0Calib
        ctx["Mat0"] = Mat0
        Z = Mat0.shape[2]
        cols = int(np.floor(np.sqrt(Z))) or 1
        rows = int(np.ceil(Z / cols))
        plot_save_fig(get_plot_array(Mat0, [cols, rows]), "M0 Image", os.path.join(savedir, "M0.png"))
        np.save(os.path.join(savedir, "M0.npy"), Mat0)