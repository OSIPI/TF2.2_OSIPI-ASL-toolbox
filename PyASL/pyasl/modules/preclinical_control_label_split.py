"""
PreclinicalControlLabelSplit
----------------------------
Split ASL series into control and label volumes.
"""
import numpy as np
import logging
logger = logging.getLogger(__name__)

class ControlLabelSplit():
    """
    Split Image into control/label series.
    params: control_first (bool)
    writes: ImageCtr, ImageLab, ImageDif
    """
    def run(self, ctx, **p):
        logger.info("Splitting image into control/label series ...")
        control_first = bool(p.get("control_first", True))
        img = ctx.get_required("Image")  # (X,Y,Z,NR,1)
        if control_first:
            ctr = img[:, :, :, 0::2, 0]
            lab = img[:, :, :, 1::2, 0]
        else:
            ctr = img[:, :, :, 1::2, 0]
            lab = img[:, :, :, 0::2, 0]
        ctx["ImageCtr"], ctx["ImageLab"] = ctr, lab
        ctx["ImageDif"] = np.mean(ctr - lab, axis=3)