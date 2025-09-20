import os
import numpy as np
import logging
logger = logging.getLogger(__name__)

class SaveOutputs():
    """
    Save key processing outputs to disk.

    This class writes selected arrays (e.g., perfusion maps,
    masks) from the pipeline context into `.npy` files in
    the specified `savedir`. Optionally saves a text copy of
    the pipeline configuration.
    """
    def run(self, ctx, **p):
        savedir = ctx.get_required("savedir")
        os.makedirs(savedir, exist_ok=True)
        for k in ("ImageDif","Mat0","relCBF","absCBF","BrainMask"):
            if k in ctx:
                np.save(os.path.join(savedir, f"{k}.npy"), ctx[k])
        if p.get("config_echo"):
            with open(os.path.join(savedir, "config_echo.yaml"), "w") as f:
                f.write(p["config_echo"])
        logger.info(f"[SaveOutputs] Saved to {savedir}")