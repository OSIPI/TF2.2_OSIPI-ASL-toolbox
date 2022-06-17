This repository contains the Python code needed to generating results presented in our JMRI paper titled "Improving Sensitivity of Arterial Spin Labeling Perfusion MRI in Alzheimer's Disease Using Transfer Learning of Deep Learning-Based ASL Denoising" (https://doi.org/10.1002/jmri.27984).
All networks were implemented using the Keras platform with GPU support.
0. "environment_to_yiran.yml" is the conda environment file containing all packages.
1. The “code” folder includes the source code to generate results by using the pre-trained models.
"test_ADNI_w_Direct_FT_0630.py" is used to generate directly transferred (DTF) results.
"test_ADNI_w_ft_0630.py" is used to generate DLASL with fine-tuning (DLASLFT) results.
"Mymodel.py"' includes the network structures.
2. The "data" folder includes two subjects from the ADNI dataset for testing the proposed DL methods.
a."009_S_4543_2016-03-30"
b."011_S_4893_2016-09-22"
There are 3 subfolders within each subject folder.
"ASL" folder contains the asl data and the resulting data will also be saved in this folder.
"ANAT_DL_mask" folder contains binary masks of the gray matter, the white matter, and the cerebrospinal fluid.
"ANAT" folder contains the T1 scan used for normalizing the denoising result into MNI space for further statistical analysis.
3. “models” folder includes pre-trained models.  
"DWAN_native_space_huber_loss_pad_ms_mean10" contains a trained model on healthy subjects.
"DWAN_huber_loss_ft_ADNI_All_0630" includes a model fine-tuned on the ADNI dataset.
