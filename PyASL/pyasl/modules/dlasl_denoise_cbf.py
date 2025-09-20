"""
DLASLDenoiseCBF
---------------
Denoise CBF volumes using a dilated CNN.
"""
from __future__ import annotations
import os, glob, logging
import numpy as np
import nibabel as nib
from typing import Dict, Any, List

from pyasl.utils.models import dilated_net_wide
from pyasl.utils.utils import load_img
from scipy.ndimage import affine_transform

logger = logging.getLogger(__name__)


def _first_images_entry(dd: Dict) -> tuple[str, Dict]:
    """
    Return the (base_dir, entry) tuple for the first subject in the Images dict.

    Args:
        dd (dict): Data description dictionary containing an "Images" key.

    Returns:
        tuple: (base_dir, entry) where base_dir is the key and entry is the value from dd["Images"].
    """
    assert "Images" in dd and isinstance(dd["Images"], dict) and dd["Images"]
    base = next(iter(dd["Images"].keys()))
    entry = dd["Images"][base]
    return base, entry


def _deriv_dir(base_dir: str) -> str:
    """rawdata → derivatives mirror."""
    return base_dir.replace("rawdata", "derivatives")


def resample_64_64_24(img: nib.Nifti1Image) -> nib.Nifti1Image:
    """
    Resample a NIfTI image to (64, 64, 24) with an affine that preserves spacing
    via a simple scaling of the orientation matrix.
    """
    data = np.asarray(img.dataobj)
    original_shape = data.shape
    original_affine = img.affine

    new_shape = (64, 64, 24)
    scale_factors = [o / n for o, n in zip(original_shape, new_shape)]
    new_affine = original_affine.copy()
    new_affine[:3, :3] = original_affine[:3, :3] * np.diag(scale_factors)

    resample_matrix = new_affine[:3, :3] @ np.linalg.inv(original_affine[:3, :3])
    resampled = affine_transform(data, matrix=resample_matrix, output_shape=new_shape, order=3)

    return nib.Nifti1Image(resampled, new_affine, img.header)


class DLASLDenoiseCBF:
    """
    Denoise CBF volumes using a dilated CNN.

    Inputs (from data_description)
    ------------------------------
    We infer the subject/session `derivatives/.../perf` directory from the first
    Images entry.

    Params (YAML/kwargs)
    --------------------
    mask_path : str, optional
        Path to a binary mask; defaults to `<der_perf>/dlasl_mask.nii.gz`.
    cbf_file : str, optional
        Explicit file name or absolute path to the CBF volume to denoise.
    glob_patterns : list[str], optional
        Glob patterns searched under `<der_perf>` when cbf_file is not set.
        Default: ["*aCBF*.nii", "*aCBF*.nii.gz", "*CBF*.nii", "*CBF*.nii.gz", "*rCBF*.nii", "*rCBF*.nii.gz"]
    model_selection : int, default 1
        0 -> model_068.hdf5, else model_099.hdf5
    weights_dir : str, optional
        Directory containing model weights; default `.../pyasl/models`.
    out_prefix : str, default "denoised_"
        Output file name prefix.

    Outputs
    -------
    Writes denoised NIfTI(s) into `<der_perf>` and returns {"dlasl_last_output": path}.
    """

    # ---------- utilities ----------
    def _load_model(self, model_selection: int, weights_dir: str):
        model = dilated_net_wide(3)
        fname = "model_068.hdf5" if model_selection == 0 else "model_099.hdf5"
        weight_path = os.path.join(weights_dir, fname)
        if not os.path.isfile(weight_path):
            logger.error("Weights not found: %s", weight_path)
            raise FileNotFoundError(f"Model weights not found: {weight_path}")
        model.load_weights(weight_path)
        logger.info("Loaded weights: %s", weight_path)
        return model

    def _resolve_cbf_list(self, der_perf: str, params: Dict[str, Any]) -> List[str]:
        """
        Resolve the list of CBF files to denoise.

        Args:
            der_perf (str): The derivatives perf directory.
            params (dict): Parameters dictionary.

        Returns:
            list[str]: The list of CBF files to denoise.
        """
        # 1) explicit file
        cbf_file = params.get("cbf_file")
        if cbf_file:
            if not os.path.isabs(cbf_file):
                cbf_file = os.path.join(der_perf, cbf_file)
            if not os.path.isfile(cbf_file):
                raise FileNotFoundError(f"cbf_file not found: {cbf_file}")
            logger.info("Using explicit CBF file: %s", cbf_file)
            return [cbf_file]

        # 2) glob search (order-preserving and deterministic)
        patterns = params.get(
            "glob_patterns",
            ["*aCBF*.nii", "*aCBF*.nii.gz", "*CBF*.nii", "*CBF*.nii.gz", "*rCBF*.nii", "*rCBF*.nii.gz"],
        )
        hits: List[str] = []
        for pat in patterns:
            found = sorted(glob.glob(os.path.join(der_perf, pat)))
            if found:
                logger.info("Pattern '%s' matched %d file(s).", pat, len(found))
                hits.extend(found)
        # de-duplicate while preserving order
        seen = set()
        unique_hits = [h for h in hits if not (h in seen or seen.add(h))]
        if not unique_hits:
            raise FileNotFoundError(f"No CBF files in {der_perf} matching any of {patterns}")
        return unique_hits

    # ---------- main ----------
    def run(self, data_descrip: Dict[str, Any], params: Dict[str, Any]):
        """
        Denoise CBF images.

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Parameters dictionary.
        """
        logger.info("DLASL: Denoise CBF images...")
        base_dir, _ = _first_images_entry(data_descrip)
        der_perf = os.path.join(_deriv_dir(base_dir), "perf")
        if not os.path.isdir(der_perf):
            raise FileNotFoundError(f"perf directory not found: {der_perf}")

        # mask
        mask_path = params.get("mask_path", os.path.join(der_perf, "dlasl_mask.nii.gz"))
        if not os.path.exists(mask_path):
            raise FileNotFoundError(
                f"Mask not found: {mask_path}. Run DLASLBuildMask first, or pass mask_path."
            )
        vmask, mask = load_img(mask_path)
        mask_img_r = resample_64_64_24(nib.Nifti1Image(mask, vmask.affine, vmask.header))
        mask_r = (np.asarray(mask_img_r.dataobj) > 0).astype(np.uint8)
        logger.info("Loaded mask and resampled to 64x64x24.")

        # inputs
        cbf_paths = self._resolve_cbf_list(der_perf, params)

        # model
        weights_dir = params.get(
            "weights_dir",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "models"),
        )
        model = self._load_model(int(params.get("model_selection", 1)), weights_dir)

        # denoise all candidates
        last_out = None
        out_prefix = params.get("out_prefix", "denoised_")

        for in_path in cbf_paths:
            v, vol = load_img(in_path)
            if vol.ndim == 4:
                vol = vol.mean(axis=3)
                hdr = v.header.copy()
                hdr.set_data_shape(vol.shape)
                v = nib.Nifti1Image(vol, v.affine, hdr)

            v_r = resample_64_64_24(v)
            x = np.asarray(v_r.dataobj).astype(np.float32)

            # preprocess
            x[mask_r == 0] = 2.0
            y = np.clip(x, 0, 150) / 255.0
            y_batch = y.transpose(2, 0, 1)[..., None]  # (Z, 64, 64, 1)

            # inference
            y_pred = model.predict(y_batch, verbose=0)  # (Z, 64, 64, 1)
            x_hat = np.squeeze(y_pred).astype(np.float32)  # (Z, 64, 64) or (64, 64)
            if x_hat.ndim == 2:
                x_hat = x_hat[None, ...]
            x_hat = x_hat.transpose(1, 2, 0) * 255.0  # (64, 64, 24)
            x_hat = np.clip(x_hat, 0, 150)
            x_hat *= mask_r

            out_path = os.path.join(der_perf, f"{out_prefix}{os.path.basename(in_path)}")
            nib.Nifti1Image(x_hat, v_r.affine, v_r.header).to_filename(out_path)
            logger.info("DLASLDenoiseCBF: %s -> %s", in_path, out_path)
            last_out = out_path

        return {"dlasl_last_output": last_out}
