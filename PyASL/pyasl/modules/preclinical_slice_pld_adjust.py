import numpy as np
import logging
logger = logging.getLogger(__name__)

class SlicePLDAdjust():
    """
    Apply across-slice PLD (post-labeling delay) correction
    for multi-slice ASL acquisitions.

    The adjustment compensates for slice-dependent delays
    using a simple exponential factor derived from the gap
    between slices and the T1 of blood.
    """
    def run(self, ctx, **p):
        logger.info("Applying across-slice PLD adjustment ...")
        Para = ctx.get_required("Para")
        Z = int(Para.get("slicenum", ctx.get("ImageDif").shape[2]))
        if Z <= 1:
            return
        SGap = float(p.get("SGap", 31))
        T1blood = float(p.get("T1blood", 2800))
        if Z % 2 == 1:
            AdjList = np.arange(Z + 1).reshape(2, -1).T.ravel()[:-1]
        else:
            AdjList = np.arange(Z).reshape(2, -1).T.ravel()
        AdjList = SGap * AdjList
        AdjF = np.exp(AdjList / T1blood)
        if "relCBF" in ctx:
            arr = ctx["relCBF"]
        else:
            arr = ctx.get_required("ImageDif")
        for z in range(Z):
            arr[:, :, z] = AdjF[z] * arr[:, :, z]
        if "relCBF" in ctx:
            ctx["relCBF"] = arr
        else:
            ctx["ImageDif"] = arr