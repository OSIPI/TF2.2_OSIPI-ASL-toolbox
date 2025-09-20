"""
PreclinicalLoaderNIfTI
----------------------
Load NIfTI/Analyze image into context.
"""
import os
import numpy as np
import logging
logger = logging.getLogger(__name__)

try:
    import nibabel as nib
except Exception:
    nib = None

class NIfTILoader():
    """
    Load a NIfTI/Analyze image (.nii/.nii.gz or .hdr/.img) into ctx.
    params:
      path: path to image file
      target: "AbsData" (default) or "Image"
      squeeze_last: when target=AbsData and data is 4D+, flatten trailing dims to N
      savedir: output directory to store results
    """
    def run(self, ctx, **p):
        logger.info("Loading NIfTI/Analyze image ...")
        if nib is None:
            raise RuntimeError("NIfTILoader requires nibabel. Please `pip install nibabel`.")
        path = p["path"]
        target = p.get("target", "AbsData")
        squeeze_last = bool(p.get("squeeze_last", True))
        img = nib.load(path)
        data = np.asarray(img.get_fdata(), dtype=float)

        if target == "AbsData":
            if data.ndim == 2:
                data = data[:, :, None]
            elif data.ndim >= 3 and squeeze_last:
                X, Y = data.shape[:2]
                N = int(np.prod(data.shape[2:]))
                data = data.reshape(X, Y, N)
            elif data.ndim != 3:
                raise ValueError("AbsData expects (X,Y,N) after squeeze.")
            ctx["AbsData"] = data
        elif target == "Image":
            if data.ndim == 3:
                X,Y,Z = data.shape
                data = data.reshape(X,Y,Z,1,1)
            elif data.ndim == 4:
                X,Y,Z,NR = data.shape
                data = data.reshape(X,Y,Z,NR,1)
            else:
                raise ValueError("Image expects 3D or 4D input.")
            ctx["Image"] = data
        else:
            raise ValueError("target must be 'AbsData' or 'Image'")

        # manage savedir
        savedir = p.get("savedir", "results")
        os.makedirs(savedir, exist_ok=True)
        ctx["savedir"] = savedir