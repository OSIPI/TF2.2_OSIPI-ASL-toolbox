import numpy as np, os
from pyasl.utils.plotting import get_plot_array, plot_save_fig
import logging
logger = logging.getLogger(__name__)

class MotionCheck():
    """
    Generate a quick mosaic figure to assess subject motion.

    This class averages ASL control/label images over time,
    arranges the slices in a grid, and saves the result as
    `MotionCheck.png` for visual inspection.
    """
    def run(self, ctx, **p):
        logger.info("Generating motion check figure ...")
        savedir = ctx.get_required("savedir")
        ctr = ctx.get_required("ImageCtr")
        Z = ctr.shape[2]
        cols = int(np.floor(np.sqrt(Z))) or 1
        rows = int(np.ceil(Z / cols))
        target = get_plot_array(np.mean(ctr, axis=3), [cols, rows])
        plot_save_fig(target, "Motion Checking", os.path.join(savedir, "MotionCheck.png"))