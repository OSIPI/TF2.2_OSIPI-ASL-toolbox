"""
PreclinicalDiffImage
--------------------
Compute control–label difference images.
"""
import numpy as np
import logging
logger = logging.getLogger(__name__)

class DiffImage():
    """
    Compute control–label difference images.
    """
    def run(self, ctx, **p):
        logger.info("Computing mean difference image ...")
        if "ImageDif" not in ctx:
            ctr = ctx.get_required("ImageCtr"); lab = ctx.get_required("ImageLab")
            ctx["ImageDif"] = np.mean(ctr - lab, axis=3)