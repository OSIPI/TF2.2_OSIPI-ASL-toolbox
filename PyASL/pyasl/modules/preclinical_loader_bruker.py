"""
PreclinicalLoaderBruker
------------------------
Load BRUKER 2dseq pCASL dataset and basic metadata.
"""
import os
import numpy as np
from pyasl.utils.bruker_io import read_2dseq_v3
from pyasl.utils.imgpara_abs import W_ImgParaAbs
import logging
logger = logging.getLogger(__name__)

class BrukerLoader():
    """
    Load BRUKER 2dseq pCASL dataset and basic metadata.
    params:
      root: directory containing BRUKER study
      expno: (int) exp number; if omitted, choose the latest automatically
      savedir: optional output dir; default Results_<rootname>/<expno>
      procno: default 1
    writes: Image (X,Y,Z,NR,1), Para, savedir, meta
    """
    def run(self, ctx, **p):
        logger.info("Loading BRUKER 2dseq pCASL dataset ...")
        root   = p["root"]
        expno  = p.get("expno")
        procno = int(p.get("procno", 1))
        if expno is None:
            nums = sorted([int(x) for x in os.listdir(root) if x.isdigit()])
            if not nums:
                raise ValueError("No numeric expno found under root")
            expno = nums[-1]
        img, NX, NY, NI, NR, ch = read_2dseq_v3(root, int(expno), procno)
        filename = os.path.join(root, str(expno))
        Para = W_ImgParaAbs(filename); Para["expno"] = expno

        # savedir
        parent, name = os.path.split(root.rstrip(os.sep))
        out_parent = os.path.join(root, "results")
        os.makedirs(out_parent, exist_ok=True)
        savedir = p.get("savedir", os.path.join(out_parent, str(expno)))
        if os.path.exists(savedir):
            base = savedir; k=1
            while os.path.exists(savedir):
                savedir = f"{base}_{k}"; k+=1
        os.makedirs(savedir, exist_ok=True)

        ctx.update({
            "Image": img,
            "Para": Para,
            "savedir": savedir,
            "meta": {"NX": NX, "NY": NY, "NI": NI, "NR": NR, "channels": ch},
        })