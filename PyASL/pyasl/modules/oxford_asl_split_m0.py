"""
OxfordASLSplitM0 module
----------------------
Split ASL and M0 images using OxfordASL pipeline logic.
"""

import os, json
import numpy as np
import nibabel as nib
from pyasl.utils.utils import load_img

import logging
logger = logging.getLogger(__name__)

def _first_images_entry(dd):
    if "Images" not in dd or not isinstance(dd["Images"], dict) or not dd["Images"]:
        raise ValueError("data_descrip['Images'] is empty or malformed.")
    base = next(iter(dd["Images"].keys()))
    entry = dd["Images"][base]
    return base, entry

def _deriv_dir(base_dir):
    return base_dir.replace("rawdata", "derivatives")

def _guess_path(base_dir, subdir, name):
    p = os.path.join(base_dir, subdir, name)
    if os.path.exists(p): return p
    for ext in (".nii.gz", ".nii", ".NII.GZ", ".NII"):
        q = p + ext
        if os.path.exists(q): return q
    return p

class OxfordASLSplitM0:
    """
    Class for splitting ASL and M0 images using OxfordASL pipeline logic.
    
    This class provides a method to separate ASL and M0 volumes when the ASLContext
    includes "m0scan" entries. If no "m0scan" is present, it passes through the
    original ASL and a separate M0 (looked up from data_descrip.Images[base]['M0'])
    and returns both paths.
    """
    
    def run(self, data_descrip: dict, params: dict):
        """
        Split ASL and M0 images using OxfordASL pipeline logic.

        Args:
            data_descrip (dict): Data description dictionary.
            params (dict): Additional parameters.

        Returns:
            dict: Paths to split ASL and M0 images.
        """
        base_dir, entry = _first_images_entry(data_descrip)

        in_asl = params.get("in_asl")
        if not in_asl:
            asl_name = entry["asl"][0]
            in_asl = _guess_path(base_dir, "perf", asl_name)

        if "ASLContext" in data_descrip and data_descrip["ASLContext"]:
            asl_context = data_descrip["ASLContext"]
        elif "asl_context" in params:
            asl_context = params["asl_context"]
        else:
            asl_context_json = params.get("asl_context_json", os.path.join(base_dir, "perf", "aslcontext.json"))
            with open(asl_context_json, "r") as f:
                meta = json.load(f)
            asl_context = meta.get("ASLContext") or meta.get("AslContext")

        has_m0scan = any(x == "m0scan" for x in asl_context)
        if not has_m0scan:
            m0_name = entry.get("M0")
            m0_path = _guess_path(base_dir, "perf", m0_name) if m0_name else None
            if not m0_path or not os.path.exists(m0_path):
                raise ValueError("ASLContext has no 'm0scan' and no separate M0 found in data_descrip['Images'][base]['M0'].")

            logger.info(f"[OxfordASL::SplitM0] No 'm0scan' found; pass-through. asl={in_asl} m0={m0_path}")
            return {"asl_path": in_asl, "m0_path": m0_path}

        der_dir = _deriv_dir(base_dir)
        out_asl = params.get("out_asl", os.path.join(der_dir, "perf", "asl_only.nii.gz"))
        out_m0  = params.get("out_m0",  os.path.join(der_dir, "perf", "m0.nii.gz"))
        os.makedirs(os.path.dirname(out_asl), exist_ok=True)
        os.makedirs(os.path.dirname(out_m0),  exist_ok=True)

        V, data = load_img(in_asl)
        asl_idx = [i for i, x in enumerate(asl_context) if x != "m0scan"]
        m0_idx  = [i for i, x in enumerate(asl_context) if x == "m0scan"]

        asl_data = data[..., asl_idx]
        m0_data  = data[..., m0_idx]
        if m0_data.ndim == 4 and m0_data.shape[-1] == 1:
            m0_data = np.squeeze(m0_data, axis=-1)

        nib.Nifti1Image(asl_data, V.affine, V.header).to_filename(out_asl)
        nib.Nifti1Image(m0_data,  V.affine, V.header).to_filename(out_m0)

        logger.info(f"[OxfordASL::SplitM0] in={in_asl} -> asl={out_asl}  m0={out_m0}")
        return {"asl_path": out_asl, "m0_path": out_m0}
