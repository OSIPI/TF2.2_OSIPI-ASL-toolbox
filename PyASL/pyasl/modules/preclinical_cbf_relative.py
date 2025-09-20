"""
PreclinicalCBFRelative
----------------------
Voxelwise relative CBF quantification (percentage) for preclinical ASL.
"""



import numpy as np, os
from pyasl.utils.plotting import get_plot_array, plot_save_fig
import logging
logger = logging.getLogger(__name__)

class CBFRelative():
    """Compute relative CBF (%) = |ImageDif|/Mat0*100."""
    def run(self, ctx, **p):
        logger.info("Compute relative CBF...")
        savedir = ctx.get_required("savedir")
        dif = ctx.get_required("ImageDif")
        Mat0 = ctx.get_required("Mat0")
        relCBF = np.abs(dif) / Mat0 * 100.0
        ctx["relCBF"] = relCBF
        vmax = float(p.get("vmax", 10.0))
        Z = relCBF.shape[2]
        cols = int(np.floor(np.sqrt(Z))) or 1
        rows = int(np.ceil(Z / cols))
        plot_save_fig(get_plot_array(relCBF, [cols, rows]), "Relative CBF (%)", os.path.join(savedir, "relCBF.png"), [0, vmax])
        np.save(os.path.join(savedir, "relCBF.npy"), relCBF)