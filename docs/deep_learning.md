# Deep learning-based method (Any application relevant to ASL)

### File name: `test_ADNI_w_ft_0630.py`
*   **Description:** Denoise ASL data in ADNI dataset with fine-tuning model presented in “Improving Sensitivity of Arterial Spin Labeling Perfusion MRI in Alzheimer's Disease Using Transfer Learning of Deep Learning-Based ASL Denoising”.
*   **Inputs:**
    To keep the script easy to run we just hard coded the input within the script. There are three inputs you will need to run the script.
    1.  A “subjectlist_valid.txt” file with subject name.
    2.  A directory containing all the subjects that need to be denoised. Each folder in this directory is one subject. In each subject folder, there are three subfolders i.e., “ASL”, “ANAT”, and “ANAT_DL_mask”. “ASL” folder contains ASL data in native space. “ANAT” folder contains the structural images for preprocessing the data e.g., registration or normalization. “ANAT_DL_mask” contains the gray matter, white matter, and the cerebrospinal fluid.
    3.  A trained deep learning model.
*   **Outputs:** Denoised ASL data in each subject’s “ASL” folder.
*   **Syntax:** `python test_ADNI_w_ft_0630.py`

---

### File name: `test_ADNI_w_Direct_FT_0630.py`
*   **Description:** Denoise ASL data in ADNI dataset with direct transfer learning model presented in “Improving Sensitivity of Arterial Spin Labeling Perfusion MRI in Alzheimer's Disease Using Transfer Learning of Deep Learning-Based ASL Denoising”. The main difference between this script and “test_ADNI_w_ft_0630.py” is that the models used for denoising are different.
*   **Inputs:**
    To keep the script easy to run we just hard coded the input within the script. There are three inputs you will need to run the script.
    1.  A “subjectlist_valid.txt” file with subject name.
    2.  A directory containing all the subjects that need to be denoised. Each folder in this directory is one subject. In each subject folder, there are three subfolders i.e., “ASL”, “ANAT”, and “ANAT_DL_mask”. “ASL” folder contains ASL data in native space. “ANAT” folder contains the structural images for preprocessing the data e.g., registration or normalization. “ANAT_DL_mask” contains the gray matter, white matter, and the cerebrospinal fluid.
    3.  A trained deep learning model.
*   **Outputs:** Denoised ASL data in each subject’s “ASL” folder.
*   **Syntax:** `python test_ADNI_w_Direct_FT_0630.py`

---

### Function name: `read_subject_list`
*   **Description:** This is a helper function used in “test_ADNI_w_Direct_FT_0630.py” and “test_ADNI_w_ft_0630.py”. The function is used to read the subject list in a “.txt” file.
*   **Inputs:** A “.txt” file with each line denotes a subject name.
*   **Outputs:** A list of all subjects.
*   **Syntax:** `content = read_subject_list('subjectlist_valid.txt')`

---

### Function name: `get_subj_c123`
*   **Description:** This is a helper function used in “test_ADNI_w_Direct_FT_0630.py” and “test_ADNI_w_ft_0630.py”. The function is used to get the gray matter, white matter, and the cerebrospinal fluid of each subject.
*   **Inputs:** A subject name and a folder containing the subject name.
*   **Outputs:** A mask with the gray matter, the white matter, and the cerebrospinal fluid.
*   **Syntax:** `mask = get_subj_c123(subject_name, folder_name)`

---

### Function name: `parse_args`
*   **Description:** Parser for command-line options, arguments and sub-commands. The function is used to set up the deep learning model’s folder and name.
*   **Inputs:** A directory of the deep learning model and the model’s file name.
*   **Outputs:** An instance of the parser.
*   **Syntax:** `args = parse_args()`

---

### Function name: `predict_nii_w_masks_rbk`
*   **Description:** The function is used to denoise all the subjects’ ASL data within a folder by using a deep learning model.
*   **Inputs:** A deep learning model, the root folder of all subjects, and the name of the denoised results.
*   **Outputs:** Denoised results.
*   **Syntax:** `predict_nii_w_masks_rbk(model,root_folder,save_name)`