import os
import json
import shutil
import nibabel as nib
import pandas as pd
from pyasl.utils.utils import read_data_description


def check_bids_format(root: str):
    """
    Check if the given rootpath follows the BIDS format.

    Args:
        root (str): Path to the BIDS dataset folder.

    Returns:
        tuple:
            bool: True if the folder follows BIDS format, otherwise False.
            str: Error message.
    """

    img_type = ""
    has_structural = False

    if not os.path.isdir(root):
        return (False, "Directory not found", img_type, has_structural)

    rawdata_path = os.path.join(root, "rawdata")
    if not os.path.isdir(rawdata_path):
        return (False, "No rawdata directory found", img_type, has_structural)

    subjects = [
        d
        for d in os.listdir(rawdata_path)
        if os.path.isdir(os.path.join(rawdata_path, d))
    ]
    if not subjects:
        return (False, "No subject directories found", img_type, has_structural)

    for subject in subjects:
        subject_path = os.path.join(rawdata_path, subject)
        sessions = [
            d
            for d in os.listdir(subject_path)
            if os.path.isdir(os.path.join(subject_path, d))
        ]
        if not sessions:
            return (
                False,
                f"No session directories found for subject {subject}",
                img_type,
                has_structural,
            )

        for session in sessions:
            session_path = os.path.join(subject_path, session)

            modality_folders = [
                d
                for d in os.listdir(session_path)
                if os.path.isdir(os.path.join(session_path, d))
            ]

            num_modality = len(modality_folders)
            if num_modality == 0:
                return (
                    False,
                    f"No image directories found for subject {subject}, session {session}",
                    img_type,
                    has_structural,
                )
            elif num_modality == 1:
                perf_path = os.path.join(session_path, "perf")
                if not os.path.isdir(perf_path):
                    return (
                        False,
                        f"No perf directory found for subject {subject}, session {session}",
                        img_type,
                        has_structural,
                    )
                perf_images = [
                    d for d in os.listdir(perf_path) if d.endswith((".nii", ".img"))
                ]
                if len(perf_images) == 0:
                    return (
                        False,
                        f"No perfusion images found for subject {subject}, session {session}",
                        img_type,
                        has_structural,
                    )
                img_type = os.path.splitext(perf_images[0])[1]
            else:
                has_structural = True
                perf_path = os.path.join(session_path, "perf")
                if not os.path.isdir(perf_path):
                    return (
                        False,
                        f"No perf directory found for subject {subject}, session {session}",
                        img_type,
                        has_structural,
                    )
                perf_images = [
                    d for d in os.listdir(perf_path) if d.endswith((".nii", ".img"))
                ]
                if len(perf_images) == 0:
                    return (
                        False,
                        f"No perfusion images found for subject {subject}, session {session}",
                        img_type,
                        has_structural,
                    )

                anat_path = os.path.join(session_path, "anat")
                if not os.path.isdir(anat_path):
                    return (
                        False,
                        f"No anat directory found for subject {subject}, session {session}",
                        img_type,
                        has_structural,
                    )
                anat_images = [
                    d for d in os.listdir(anat_path) if d.endswith((".nii", ".img"))
                ]
                if len(anat_images) == 0:
                    return (
                        False,
                        f"No anatomy images found for subject {subject}, session {session}",
                        img_type,
                        has_structural,
                    )
                img_type = os.path.splitext(perf_images[0])[1]
    return (True, "", img_type, has_structural)


def read_params(params_json: str, has_structural: bool, is_singledelay: bool):
    try:
        with open(params_json, "r") as json_file:
            params = json.load(json_file)
    except FileNotFoundError:
        return (False, f"Cannot read json file: {params_json} not found", {})
    except IOError:
        return (
            False,
            f"Cannot read json file: Error opening or reading the file {params_json}",
            {},
        )
    except json.JSONDecodeError:
        return (
            False,
            f"Cannot read json file: Error decoding JSON from the file {params_json}",
            {},
        )

    # check ASL parameters
    asl_params = params["ASL"]
    required_keys = [
        "Manufacturer",
        "ManufacturersModelName",
        "MagneticFieldStrength",
        "RepetitionTime",
        "EchoTime",
        "FlipAngle",
        "ArterialSpinLabelingType",
        "M0Type",
        "MRAcquisitionType",
        "BackgroundSuppression",
        "LabelingEfficiency",
        "PostLabelingDelay",
    ]

    for key in required_keys:
        if key not in asl_params:
            return (False, f"Missing parameter: {key}", {})

    if (
        asl_params["ArterialSpinLabelingType"] == "PCASL"
        or asl_params["ArterialSpinLabelingType"] == "CASL"
    ):
        required_asl_keys = [
            "LabelingDuration",
        ]
    elif asl_params["ArterialSpinLabelingType"] == "PASL":
        if is_singledelay:
            required_asl_keys = [
                "BolusCutOffDelayTime",
            ]
        else:
            required_asl_keys = ["BolusCutOffDelayTime", "Looklocker"]
        for key in required_asl_keys:
            if key not in asl_params:
                return (False, f"Missing parameter: {key}", {})

    if asl_params["MRAcquisitionType"] == "2D":
        if "SliceDuration" not in asl_params:
            return (False, "Missing parameter: SliceDuration", {})

    if not is_singledelay:
        if not isinstance(asl_params["PostLabelingDelay"], (list)):
            return (
                False,
                f"Invalid PostLabelingDelay: should be an array for multi-delay data",
                {},
            )
    else:
        if asl_params["M0Type"] == "Included":
            if not isinstance(asl_params["PostLabelingDelay"], (list)):
                return (
                    False,
                    f"Invalid PostLabelingDelay: should be an array for single-delay data with included M0",
                    {},
                )
        else:
            if isinstance(asl_params["PostLabelingDelay"], (list)):
                return (
                    False,
                    f"Invalid PostLabelingDelay: should be a value for single-delay data",
                    {},
                )

    if asl_params["M0Type"] == "Included":
        if not (0 in asl_params["PostLabelingDelay"]):
            return (False, f"Invalid PostLabelingDelay: no M0 included", {})

    if asl_params["BackgroundSuppression"]:
        required_bg_keys = [
            "BackgroundSuppressionNumberPulses",
            "BackgroundSuppressionPulseTime",
        ]
        for key in required_bg_keys:
            if key not in asl_params:
                return (False, f"Missing parameter: {key}", {})

    # check structural image parameters
    if has_structural:
        anat_params = params["anat"]
        required_keys = [
            "Manufacturer",
            "ManufacturersModelName",
            "MagneticFieldStrength",
            "RepetitionTime",
            "EchoTime",
            "FlipAngle",
        ]
        for key in required_keys:
            if key not in anat_params:
                return (False, f"Missing parameter: {key}", {})
    else:
        params["anat"] = {}

    # check M0 image parameters
    if asl_params["M0Type"] != "Estimate":
        m0_params = params["M0"]
        required_keys = [
            "Manufacturer",
            "ManufacturersModelName",
            "MagneticFieldStrength",
            "RepetitionTime",
            "EchoTime",
            "FlipAngle",
        ]
        for key in required_keys:
            if key not in m0_params:
                return (False, f"Missing parameter: {key}", {})
    else:
        params["M0"] = {}

    return (True, "", params)


def make_sidecar(
    params: dict, num_volumes: int, is_singledelay: bool, is_labelcontrol: bool
):
    asl_json_data = params["ASL"].copy()
    structural_json_data = params["anat"].copy()
    m0_json_data = params["M0"].copy()

    if params["ASL"]["M0Type"] == "Included":
        asl_json_data["M0"] = params["M0"].copy()

    volume_type = []
    if isinstance(params["ASL"]["PostLabelingDelay"], (list)):
        if is_singledelay:
            asl_json_data["PostLabelingDelay"] = [
                x for x in params["ASL"]["PostLabelingDelay"] if x != 0
            ][0]
        else:
            asl_json_data["PostLabelingDelay"] = [
                x for x in params["ASL"]["PostLabelingDelay"] if x != 0
            ]

        for pld in params["ASL"]["PostLabelingDelay"]:
            if pld == 0:
                volume_type.append("m0scan")
            else:
                if is_labelcontrol:
                    volume_type.append("label")
                    volume_type.append("control")
                else:
                    volume_type.append("control")
                    volume_type.append("label")
    else:
        for i in range(int(num_volumes / 2)):
            if is_labelcontrol:
                volume_type.append("label")
                volume_type.append("control")
            else:
                volume_type.append("control")
                volume_type.append("label")
    tsv_data = {"volume_type": volume_type}
    return asl_json_data, structural_json_data, m0_json_data, tsv_data


def convert2bids(
    root: str,
    params: dict,
    img_type: str,
    has_structural: bool,
    is_singledelay: bool,
    is_labelcontrol: bool,
):
    source_path = os.path.join(root, "rawdata")
    all_session_paths = []
    num_volumes = 0
    subject_paths = [
        os.path.join(source_path, d)
        for d in os.listdir(source_path)
        if os.path.isdir(os.path.join(source_path, d))
    ]
    for subject_path in subject_paths:
        session_paths = [
            os.path.join(subject_path, d)
            for d in os.listdir(subject_path)
            if os.path.isdir(os.path.join(subject_path, d))
        ]
        for session_path in session_paths:
            all_session_paths.append(session_path)
            perf_path = os.path.join(session_path, "perf")
            perf_images = [d for d in os.listdir(perf_path) if d.endswith((img_type))]
            M0_images = [img for img in perf_images if "M0" in img]
            asl_images = [img for img in perf_images if "M0" not in img]

            if params["ASL"]["M0Type"] == "Separate":
                if not M0_images:
                    return False, f"No separate M0 file found in {perf_path}"

            if img_type == ".img":
                analyze_file = nib.load(os.path.join(perf_path, asl_images[0]))
                num_volumes = analyze_file.shape[-1]
            else:
                nii_file = nib.load(os.path.join(perf_path, asl_images[0]))
                nii_image = nii_file.get_fdata()
                num_volumes = nii_image.shape[-1]

            if isinstance(params["ASL"]["PostLabelingDelay"], (list)):
                if num_volumes != (
                    2 * len(params["ASL"]["PostLabelingDelay"])
                    - params["ASL"]["PostLabelingDelay"].count(0)
                ):
                    return (
                        False,
                        f"Number of volumes in ASL image does not match PostLabelingDelay parameter",
                    )

    asl_json_data, structural_json_data, m0_json_data, tsv_data = make_sidecar(
        params, num_volumes, is_singledelay, is_labelcontrol
    )

    sessions_dict = {}

    for i in range(len(all_session_paths)):
        session_dict = {
            "anat": None,
            "asl": [],
            "M0": None,
        }
        perf_path = os.path.join(all_session_paths[i], "perf")
        perf_path_temp = perf_path.replace("rawdata", "rawdata_temp")
        os.makedirs(perf_path_temp)
        perf_images = [d for d in os.listdir(perf_path) if d.endswith((img_type))]
        for perf_image in perf_images:
            if img_type == ".img":
                analyze_img = nib.load(os.path.join(perf_path, perf_image))
                nifti_img = nib.Nifti1Image(
                    analyze_img.get_fdata(), analyze_img.affine, analyze_img.header
                )
                nib.save(
                    nifti_img,
                    os.path.join(
                        perf_path_temp, os.path.splitext(perf_image)[0] + ".nii"
                    ),
                )
            else:
                shutil.copy2(
                    os.path.join(perf_path, perf_image),
                    os.path.join(perf_path_temp, perf_image),
                )

            img_name = os.path.splitext(perf_image)[0]
            json_path = os.path.join(perf_path_temp, img_name + ".json")

            if "M0" not in img_name:
                tsv_path = os.path.join(perf_path_temp, img_name + "_aslcontext.tsv")
                df = pd.DataFrame(tsv_data)
                df.to_csv(tsv_path, sep="\t", index=False)

                session_dict["asl"].append(img_name)

                with open(json_path, "w") as json_file:
                    json.dump(asl_json_data, json_file, indent=4)
            else:
                if params["ASL"]["M0Type"] == "Separate":
                    session_dict["M0"] = img_name
                    with open(json_path, "w") as json_file:
                        json.dump(m0_json_data, json_file, indent=4)

        if has_structural:
            anat_path = os.path.join(all_session_paths[i], "anat")
            anat_path_temp = anat_path.replace("rawdata", "rawdata_temp")
            os.makedirs(anat_path_temp)
            anat_images = [d for d in os.listdir(anat_path) if d.endswith((img_type))]
            for anat_image in anat_images:
                if img_type == ".img":
                    analyze_img = nib.load(os.path.join(anat_path, anat_image))
                    nifti_img = nib.Nifti1Image(
                        analyze_img.get_fdata(), analyze_img.affine, analyze_img.header
                    )
                    nib.save(
                        nifti_img,
                        os.path.join(
                            anat_path_temp, os.path.splitext(anat_image)[0] + ".nii"
                        ),
                    )
                else:
                    shutil.copy2(
                        os.path.join(anat_path, anat_image),
                        os.path.join(anat_path_temp, anat_image),
                    )
                img_name = os.path.splitext(anat_image)[0]
                json_path = os.path.join(anat_path_temp, img_name + ".json")
                with open(json_path, "w") as json_file:
                    json.dump(structural_json_data, json_file, indent=4)
            session_dict["anat"] = img_name

        sessions_dict[all_session_paths[i]] = session_dict.copy()

    os.rename(source_path, os.path.join(root, "rawdata_user"))
    os.rename(os.path.join(root, "rawdata_temp"), source_path)

    data_description_json = asl_json_data.copy()
    if has_structural:
        data_description_json["anat"] = structural_json_data.copy()
    if params["ASL"]["M0Type"] != "Estimate":
        data_description_json["M0"] = m0_json_data.copy()
    data_description_json["SingleDelay"] = is_singledelay
    data_description_json["LabelControl"] = is_labelcontrol
    data_description_json["Images"] = sessions_dict.copy()
    data_description_json["ASLContext"] = tsv_data["volume_type"].copy()
    data_description_json["PLDList"] = []

    if isinstance(params["ASL"]["PostLabelingDelay"], (list)):
        PLD_temp = [pld for pld in params["ASL"]["PostLabelingDelay"] if pld != 0]
        i = 0
        for volume_type in tsv_data["volume_type"]:
            if volume_type == "label":
                data_description_json["PLDList"].append(PLD_temp[i])
                i += 1
            else:
                data_description_json["PLDList"].append(0)
    else:
        for volume_type in tsv_data["volume_type"]:
            if volume_type == "label":
                data_description_json["PLDList"].append(
                    params["ASL"]["PostLabelingDelay"]
                )
            else:
                data_description_json["PLDList"].append(0)

    json_path = os.path.join(root, "data_description.json")
    with open(json_path, "w") as json_file:
        json.dump(data_description_json, json_file, indent=4)
    return (True, "")


def read_asl_bids(root: str, img_type: str, has_structural: bool):
    data_description_json = {}
    read_tsv_flag = False

    source_path = os.path.join(root, "rawdata")
    all_session_paths = []
    subject_paths = [
        os.path.join(source_path, d)
        for d in os.listdir(source_path)
        if os.path.isdir(os.path.join(source_path, d))
    ]
    for subject_path in subject_paths:
        session_paths = [
            os.path.join(subject_path, d)
            for d in os.listdir(subject_path)
            if os.path.isdir(os.path.join(subject_path, d))
        ]
        for session_path in session_paths:
            all_session_paths.append(session_path)

    sessions_dict = {}
    for i in range(len(all_session_paths)):
        session_dict = {
            "anat": None,
            "asl": [],
            "M0": None,
        }
        perf_path = os.path.join(all_session_paths[i], "perf")
        perf_images = [d for d in os.listdir(perf_path) if d.endswith((img_type))]

        if not data_description_json:
            perf_names = [os.path.splitext(img)[0] for img in perf_images]
            asl_names = [name for name in perf_names if "M0" not in name]
            json_path = os.path.join(perf_path, asl_names[0] + ".json")
            with open(json_path, "r") as json_file:
                json_info = json.load(json_file)
                data_description_json = json_info.copy()

        for perf_image in perf_images:
            img_name = os.path.splitext(perf_image)[0]

            if "M0" not in img_name:
                session_dict["asl"].append(img_name)
                if not read_tsv_flag:
                    df = pd.read_csv(
                        os.path.join(perf_path, img_name + "_aslcontext.tsv"), sep="\t"
                    )
                    volume_type = df["volume_type"].tolist()
                    data_description_json["ASLContext"] = volume_type.copy()
                    for item in volume_type:
                        if item == "label":
                            data_description_json["LabelControl"] = True
                            break
                        elif item == "control":
                            data_description_json["LabelControl"] = False
                            break
                    data_description_json["PLDList"] = []
                    if isinstance(data_description_json["PostLabelingDelay"], (list)):
                        PLD_unique = list(
                            set(data_description_json["PostLabelingDelay"])
                        )
                        if len(PLD_unique) == 1:
                            data_description_json["SingleDelay"] = True
                        else:
                            data_description_json["SingleDelay"] = False
                        j = 0
                        for item in volume_type:
                            if item == "label":
                                data_description_json["PLDList"].append(
                                    data_description_json["PostLabelingDelay"][j]
                                )
                                j += 1
                            else:
                                data_description_json["PLDList"].append(0)
                    else:
                        data_description_json["SingleDelay"] = True
                        for item in volume_type:
                            if item == "label":
                                data_description_json["PLDList"].append(
                                    data_description_json["PostLabelingDelay"]
                                )
                            else:
                                data_description_json["PLDList"].append(0)
                    read_tsv_flag = True
            else:
                session_dict["M0"] = img_name
                json_path = os.path.join(perf_path, img_name + ".json")
                with open(json_path, "r") as json_file:
                    json_info = json.load(json_file)
                    data_description_json["M0"] = json_info.copy()

        if has_structural:
            anat_path = os.path.join(all_session_paths[i], "anat")
            anat_images = [d for d in os.listdir(anat_path) if d.endswith((img_type))]
            anat_image = anat_images[0]
            img_name = os.path.splitext(anat_image)[0]
            session_dict["anat"] = img_name
            json_path = os.path.join(anat_path, img_name + ".json")
            with open(json_path, "r") as json_file:
                json_info = json.load(json_file)
                data_description_json["anat"] = json_info.copy()

        sessions_dict[all_session_paths[i]] = session_dict.copy()

    data_description_json["Images"] = sessions_dict.copy()

    json_path = os.path.join(root, "data_description.json")
    with open(json_path, "w") as json_file:
        json.dump(data_description_json, json_file, indent=4)


def create_derivatives_folders(data_descrip: dict):
    for key, value in data_descrip["Images"].items():
        der_path = key.replace("rawdata", "derivatives")
        try:
            os.makedirs(der_path, exist_ok=True)
        except OSError:
            raise OSError(f"Could not create directories: {der_path}.")

        der_perf_path = os.path.join(der_path, "perf")
        try:
            os.makedirs(der_perf_path, exist_ok=True)
        except OSError:
            raise OSError(f"Could not create directory: {der_perf_path}.")

        if value["anat"]:
            der_anat_path = os.path.join(der_path, "anat")
            try:
                os.makedirs(der_anat_path, exist_ok=True)
            except OSError:
                raise OSError(f"Could not create directory: {der_anat_path}.")


def load_data(
    root: str, params_json="", convert=True, is_singledelay=True, is_labelcontrol=True
):
    root = os.path.abspath(root)
    valid, error, img_type, has_structural = check_bids_format(root)
    if not valid:
        raise ValueError(error)

    if convert:
        valid, error, params = read_params(params_json, has_structural, is_singledelay)
        if not valid:
            raise ValueError(error)
        print("User-input parameters:")
        print(json.dumps(params, indent=4))

        valid, error = convert2bids(
            root, params, img_type, has_structural, is_singledelay, is_labelcontrol
        )
        if not valid:
            raise ValueError(error)
        print("Convert complete!")

    else:
        read_asl_bids(root, img_type, has_structural)
        print("Load compelete!")

    data_descrip = read_data_description(root)
    create_derivatives_folders(data_descrip)

    print(f"Please see data_description.json under {root} for details.")
