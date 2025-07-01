# Deep learning-based method (Any application relevant to ASL)

### `test_ADNI_w_ft_0630.py`

Denoise ASL data in ADNI dataset with fine-tuning model presented in “Improving Sensitivity of Arterial Spin Labeling Perfusion MRI in Alzheimer's Disease Using Transfer Learning of Deep Learning-Based ASL Denoising”.

!!! info "Inputs"
    To keep the script easy to run we just hard coded the input within the script. There are three inputs you will need to run the script.  
    **1**. A “subjectlist_valid.txt” file with subject name.  
    **2**. A directory containing all the subjects that need to be denoised. Each folder in this directory is one subject. In each subject folder, there are three subfolders i.e., “ASL”, “ANAT”, and “ANAT_DL_mask”. “ASL” folder contains ASL data in native space. “ANAT” folder contains the structural images for preprocessing the data e.g., registration or normalization. “ANAT_DL_mask” contains the gray matter, white matter, and the cerebrospinal fluid.  
    **3**. A trained deep learning model.

!!! success "Outputs"
    - Denoised ASL data in each subject’s “ASL” folder.

!!! example "Syntax"
    ```bash
    python test_ADNI_w_ft_0630.py
    ```

---
### `test_ADNI_w_Direct_FT_0630.py`

Denoise ASL data in ADNI dataset with direct transfer learning model presented in “Improving Sensitivity of Arterial Spin Labeling Perfusion MRI in Alzheimer's Disease Using Transfer Learning of Deep Learning-Based ASL Denoising”. The main difference between this script and “test_ADNI_w_ft_0630.py” is that the models used for denoising are different.

!!! info "Inputs"
    To keep the script easy to run we just hard coded the input within the script. There are three inputs you will need to run the script.  
    **1**. A “subjectlist_valid.txt” file with subject name.  
    **2**. A directory containing all the subjects that need to be denoised. Each folder in this directory is one subject. In each subject folder, there are three subfolders i.e., “ASL”, “ANAT”, and “ANAT_DL_mask”. “ASL” folder contains ASL data in native space. “ANAT” folder contains the structural images for preprocessing the data e.g., registration or normalization. “ANAT_DL_mask” contains the gray matter, white matter, and the cerebrospinal fluid.  
    **3**. A trained deep learning model.

!!! success "Outputs"
    - Denoised ASL data in each subject’s “ASL” folder.

!!! example "Syntax"
    ```bash
    python test_ADNI_w_Direct_FT_0630.py
    ```

---
### `read_subject_list`

This is a helper function used in “test_ADNI_w_Direct_FT_0630.py” and “test_ADNI_w_ft_0630.py”. The function is used to read the subject list in a “.txt” file.

!!! info "Inputs"
    - A “.txt” file with each line denotes a subject name.

!!! success "Outputs"
    - A list of all subjects.

!!! example "Syntax"
    ```python
    content = read_subject_list('subjectlist_valid.txt')
    ```

---
### `get_subj_c123`

This is a helper function used in “test_ADNI_w_Direct_FT_0630.py” and “test_ADNI_w_ft_0630.py”. The function is used to get the gray matter, white matter, and the cerebrospinal fluid of each subject.

!!! info "Inputs"
    - A subject name and a folder containing the subject name.

!!! success "Outputs"
    - A mask with the gray matter, the white matter, and the cerebrospinal fluid.

!!! example "Syntax"
    ```python
    mask = get_subj_c123(subject_name, folder_name)
    ```

---
### `parse_args`

Parser for command-line options, arguments and sub-commands. The function is used to set up the deep learning model’s folder and name.

!!! info "Inputs"
    - A directory of the deep learning model and the model’s file name.

!!! success "Outputs"
    - An instance of the parser.

!!! example "Syntax"
    ```python
    args = parse_args()
    ```

---
### `predict_nii_w_masks_rbk`

The function is used to denoise all the subjects’ ASL data within a folder by using a deep learning model.

!!! info "Inputs"
    - A deep learning model, the root folder of all subjects, and the name of the denoised results.

!!! success "Outputs"
    - Denoised results.

!!! example "Syntax"
    ```python
    predict_nii_w_masks_rbk(model,root_folder,save_name)
    ```