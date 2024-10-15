import os
import json
import numpy as np
import nibabel as nib


def read_data_description(root: str):
    description_file = os.path.join(root, "data_description.json")

    try:
        with open(description_file, "r") as f:
            data_descrip = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"{description_file} not found. Please load data first.")
    except json.JSONDecodeError:
        raise ValueError(f"Failed to decode JSON from {description_file}.")

    return data_descrip


def load_img(P: str):
    V = nib.load(P)
    data = V.get_fdata()
    data = np.nan_to_num(data)

    return V, data
