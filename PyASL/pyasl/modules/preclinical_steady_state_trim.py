import logging
logger = logging.getLogger(__name__)

class SteadyStateTrim():
    """
    Remove initial volumes to reach steady state.

    This class discards the first `n` repetitions from a
    5-D ASL image (X, Y, Z, N_reps, 1) to avoid signal
    instability at the beginning of acquisition.
    """
    def run(self, ctx, **p):
        logger.info("Trimming initial repetitions to ensure steady state ...")
        n = int(p.get("trim", 2))
        img = ctx.get_required("Image")
        if img.shape[3] <= n:
            raise ValueError("Not enough repetitions to trim")
        ctx["Image"] = img[:, :, :, n:, :]