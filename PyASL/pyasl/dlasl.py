import os
import re
import numpy as np
import nibabel as nib
from scipy.ndimage import affine_transform
from pyasl.utils.models import dilated_net_wide
from pyasl.utils.utils import read_data_description, load_img


def dlasl_resample(v: nib.Nifti1Image, data: np.ndarray):
    original_shape = data.shape
    original_affine = v.affine

    new_shape = (64, 64, 24)
    scale_factors = [o / n for o, n in zip(original_shape, new_shape)]
    new_affine = np.copy(original_affine)
    new_affine[:3, :3] *= scale_factors

    resample_matrix = new_affine[:3, :3] @ np.linalg.inv(original_affine[:3, :3])

    resampled_data = affine_transform(
        data,
        matrix=resample_matrix,
        output_shape=new_shape,
        order=3,
    )

    resampled_img = nib.Nifti1Image(
        resampled_data,
        new_affine,
    )
    return resampled_img, resampled_data


def dlasl_get_subj_c123(dir: str):
    all_files = os.listdir(dir)
    pattern = re.compile(".*c1.*\.(nii|nii\.gz)$")
    found_files = [f for f in all_files if pattern.match(f)]
    if not found_files:
        raise FileNotFoundError("No c1 segmentation nii/nii.gz files!")
    v, c1 = load_img(os.path.join(dir, found_files[0]))

    pattern = re.compile(".*c2.*\.(nii|nii\.gz)$")
    found_files = [f for f in all_files if pattern.match(f)]
    if not found_files:
        raise FileNotFoundError("No c2 segmentation nii/nii.gz files!")
    v, c2 = load_img(os.path.join(dir, found_files[0]))

    pattern = re.compile(".*c3.*\.(nii|nii\.gz)$")
    found_files = [f for f in all_files if pattern.match(f)]
    if not found_files:
        raise FileNotFoundError("No c3 segmentation nii/nii.gz files!")
    v, c3 = load_img(os.path.join(dir, found_files[0]))

    c123 = c1 + c2 + c3
    return v, c123


def dlasl_pipeline(root: str, model_selection=1, pattern=".*_CBF\.(nii|nii\.gz)$"):
    print("Denoise CBF images using DeepASL...")
    data_descrip = read_data_description(root)
    model = dilated_net_wide(3)
    current_directory = os.path.dirname(__file__)
    if model_selection == 0:
        model_name = "model_068.hdf5"  # trained model on healthy subjects
    else:
        model_name = "model_099.hdf5"  # fine-tuned model on the ADNI dataset
    model.load_weights(os.path.join(current_directory, "models", model_name))
    for key, value in data_descrip["Images"].items():
        key = key.replace("rawdata", "derivatives")
        vmask, mask = dlasl_get_subj_c123(os.path.join(key, "perf"))
        vmask = nib.Nifti1Image(
            mask, affine=vmask.affine.copy(), header=vmask.header.copy()
        )
        vmask, mask = dlasl_resample(vmask, mask)
        mask = (mask > 0.5).astype(np.int32)

        all_files = os.listdir(os.path.join(key, "perf"))
        pttn = re.compile(pattern)
        found_cbf_files = [f for f in all_files if pttn.match(f)]
        if not found_cbf_files:
            raise FileNotFoundError(
                f"No CBF files found matching the pattern: {pattern}"
            )
        for cbf_file in found_cbf_files:
            item_obj, item = load_img(os.path.join(key, "perf", cbf_file))
            if item.ndim == 4:
                item = np.mean(item, axis=3)
                header = item_obj.header.copy()
                header.set_data_shape(item.shape)
                item_obj = nib.Nifti1Image(
                    item, affine=item_obj.affine.copy(), header=header
                )
            vitem, item = dlasl_resample(item_obj, item)

            item[mask[:, :, :] < 0.1] = 2
            y = np.clip(item, 0, 150) / 255.0
            y_ = np.transpose(y, (2, 0, 1))
            y_ = y.reshape((y.shape[0], y.shape[1], y.shape[2], 1))
            x_ = model.predict(y_)
            x_ = np.clip(np.squeeze(x_ * 255.0), 0, 150)
            mask[mask > 0] = 1
            x_ = x_ * mask
            x_nii = nib.Nifti1Image(x_, vitem.affine, vitem.header)
            descrip_str = f"dlasl_pipeline, model_selection={model_selection}"
            x_nii.header["descrip"] = descrip_str.encode()
            x_nii.to_filename(os.path.join(key, "perf", f"denoised_{cbf_file}"))

    print("Processing complete!")
    print(f"Please see results under {os.path.join(root,'derivatives')}.")
