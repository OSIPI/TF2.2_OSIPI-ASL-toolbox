"""
DLASLBuildMask
--------------
Build a DLASL mask from C1, C2, and C3 segmentation images.
"""
import os, re, numpy as np, nibabel as nib
from pyasl.utils.utils import load_img
from scipy.ndimage import affine_transform
import logging
logger = logging.getLogger(__name__)

def _first_images_entry(dd):
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

def _deriv_dir(base_dir):          # rawdata → derivatives
    """
    Return the derivatives directory for a given base directory.

    Args:
        base_dir (str): The base directory to convert.

    Returns:
        str: The derivatives directory.
    """
    return base_dir.replace("rawdata", "derivatives")

def resample_64_64_24(img: nib.Nifti1Image) -> nib.Nifti1Image:
    """
    Resample a NIfTI image to 64x64x24.

    Args:
        img (nib.Nifti1Image): The NIfTI image to resample.

    Returns:
        nib.Nifti1Image: The resampled NIfTI image.
    """
    data = np.asarray(img.dataobj)
    original_shape = data.shape
    original_affine = img.affine

    new_shape = (64, 64, 24)
    scale_factors = [o / n for o, n in zip(original_shape, new_shape)]
    new_affine = original_affine.copy()
    new_affine[:3, :3] = original_affine[:3, :3] * np.diag(scale_factors)

    resample_matrix = new_affine[:3, :3] @ np.linalg.inv(original_affine[:3, :3])

    resampled = affine_transform(
        data, matrix=resample_matrix, output_shape=new_shape, order=3
    )

    return nib.Nifti1Image(resampled, new_affine, img.header)


class DLASLBuildMask:
    """
    Build a DLASL mask from C1, C2, and C3 segmentation images.

    Args:
        data_descrip (dict): Data description dictionary.
        params (dict): Parameters dictionary.
    """
    def run(self, data_descrip: dict, params: dict):
        """
        Build a DLASL mask from C1, C2, and C3 segmentation images.

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Parameters dictionary.
        """
        logger.info("DLASL: Build DLASL mask...")
        base_dir, _ = _first_images_entry(data_descrip)
        der_perf = os.path.join(_deriv_dir(base_dir), "perf")
        os.makedirs(der_perf, exist_ok=True)

        files = os.listdir(der_perf)
        def _pick(label):
            rx = re.compile(fr".*{label}.*\.(nii|nii\.gz)$", re.IGNORECASE)
            for f in files:
                if rx.match(f): return os.path.join(der_perf, f)
            raise FileNotFoundError(f"No {label} segmentation nii/nii.gz in {der_perf}")
        c1 = _pick("c1"); c2 = _pick("c2"); c3 = _pick("c3")

        v1, m1 = load_img(c1); _, m2 = load_img(c2); _, m3 = load_img(c3)
        c123 = m1 + m2 + m3
        mask_img = nib.Nifti1Image(c123, v1.affine, v1.header)
        mask_img_r = resample_64_64_24(mask_img)
        mask = (np.asarray(mask_img_r.dataobj) > 0.5).astype(np.uint8)

        out_mask = params.get("out_mask", os.path.join(der_perf, "dlasl_mask.nii.gz"))
        nib.Nifti1Image(mask, mask_img_r.affine, mask_img_r.header).to_filename(out_mask)
        print(f"[DLASLBuildMask] -> {out_mask}")
        return {"dlasl_mask": out_mask}
