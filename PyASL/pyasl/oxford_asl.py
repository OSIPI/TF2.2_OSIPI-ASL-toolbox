import subprocess
import os
import numpy as np
import nibabel as nib
from pyasl.utils.utils import read_data_description, load_img


def split_asl_m0(file_path: str, asl_context: list):
    V, data = load_img(file_path)
    asl_indices = [i for i, x in enumerate(asl_context) if x != "m0scan"]
    m0_indices = [i for i, x in enumerate(asl_context) if x == "m0scan"]
    asl_data = data[:, :, :, asl_indices]
    m0_data = data[:, :, :, m0_indices]
    if m0_data.shape[-1] == 1:
        m0_data = np.squeeze(m0_data, axis=-1)

    affine = V.affine.copy()
    asl_header = V.header.copy()
    asl_header.set_data_shape(asl_data.shape)
    Vasl = nib.Nifti1Image(asl_data, affine, asl_header)

    m0_header = V.header.copy()
    m0_header.set_data_shape(m0_data.shape)
    Vm0 = nib.Nifti1Image(m0_data, affine, m0_header)

    path, filename = os.path.split(file_path)
    filename, file_ext = os.path.splitext(filename)
    path = path.replace("rawdata", "derivatives")
    asl_path = os.path.join(path, f"{filename}_asl{file_ext}")
    m0_path = os.path.join(path, f"{filename}_M0{file_ext}")

    Vasl.to_filename(asl_path)
    Vm0.to_filename(m0_path)

    return asl_path, m0_path


def run_oxford_asl(
    root: str,
    useStructural=False,
    useCalibration=False,
    cmethod="voxel",
    wp=False,
    mc=False,
    bat=None,
    t1=None,
    t1b=None,
    sliceband=None,
):
    data_descrip = read_data_description(root)
    cmd = ["oxford_asl"]
    if wp:
        cmd += ["--wp"]
    if mc:
        cmd += ["--mc"]
    if data_descrip["LabelControl"]:
        cmd += ["--iaf", "tc"]
    else:
        cmd += ["--iaf", "ct"]
    if (
        data_descrip["ArterialSpinLabelingType"] == "CASL"
        or data_descrip["ArterialSpinLabelingType"] == "PCASL"
    ):
        cmd += ["--casl"]
        tis = np.array([t for t in data_descrip["PLDList"] if t != 0], dtype=float)
        bolus = data_descrip["LabelingDuration"]
        tis += bolus
    elif data_descrip["ArterialSpinLabelingType"] == "PASL":
        tis = np.array([t for t in data_descrip["PLDList"] if t != 0], dtype=float)
        bolus = data_descrip["BolusCutOffDelayTime"]
        tis += bolus
    tis_str = ",".join(map(str, tis))
    cmd += ["--tis", tis_str]
    cmd += ["--bolus", str(bolus)]
    if "SliceDuration" in data_descrip:
        cmd += ["--slicedt", str(data_descrip["SliceDuration"])]
    if bat is not None:
        cmd += ["--bat", str(bat)]
    if t1 is not None:
        cmd += ["--t1", str(t1)]
    if t1b is not None:
        cmd += ["--t1b", str(t1b)]
    if sliceband is not None:
        cmd += ["--sliceband", str(sliceband)]
    if useCalibration:
        if cmethod == "single" and not useStructural:
            raise ValueError(
                "Must have structural images when using a single M0 value for calibration."
            )
        if data_descrip["M0Type"] == "Estimate":
            raise ValueError("Missing M0 images!")
    cmdroot = cmd

    for key, value in data_descrip["Images"].items():
        cmd = cmdroot
        if useStructural:
            if value["anat"] is None:
                raise ValueError("Missing structural images!")
            else:
                cmd += ["-s", os.path.join(key, "anat", value["anat"])]
        for asl_file in value["asl"]:

            if data_descrip["M0Type"] == "Included":
                asl_path, m0_path = split_asl_m0(
                    os.path.join(key, "perf", asl_file), data_descrip["ASLContext"]
                )
                cmd += ["-i", asl_path]
                if useCalibration:
                    cmd += ["-c", m0_path]
                    cmd += ["--tr", str(data_descrip["M0"]["RepetitionTime"])]
                    cmd += ["--alpha", str(data_descrip["LabelingEfficiency"])]
            else:
                cmd += ["-i", os.path.join(key, "perf", asl_file)]
                if useCalibration:
                    cmd += ["-c", os.path.join(key, "perf", value["M0"])]
                    cmd += ["--tr", str(data_descrip["M0"]["RepetitionTime"])]
                    cmd += ["--alpha", str(data_descrip["LabelingEfficiency"])]

            key_der = key.replace("rawdata", "derivatives")
            cmd += ["-o", key_der]
            subprocess.run(cmd)

            with open(os.path.join(key_der, "config.txt"), "w") as f:
                f.write(
                    f"run_oxford_asl(root='{root}', useStructural={useStructural}, useCalibration={useCalibration}, cmethod='{cmethod}', wp={wp}, mc={mc}, bat={bat}, t1={t1}, t1b={t1b}, sliceband={sliceband})"
                )
    print(f"Please see results under {os.path.join(root,'derivatives')}.")
