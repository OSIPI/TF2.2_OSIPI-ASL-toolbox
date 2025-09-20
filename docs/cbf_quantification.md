# Cerebral Blood Flow (CBF) quantification (please specify the model used)

### Function name: `asl_perf_subtract.m` / `asl_perf_subtractMB.m`
*   **Description:** For CASL and PASL, generate the difference and calculate the perfusion images from control/label and M0 images
*   **Inputs:** Please see the description in the MATLAB code for detailed information.
*   **Outputs:** Will output CBF maps into the path you defined
*   **Syntax:** One example for PASL quantification. Both `P` and `M0img` are paths for control/label and M0 images: `FAIR='C:\Users\...\FAIR_CL.nii'`.
    ```matlab
    perfnum =  asl_perf_subtract(FAIR,1, 0, 0, [0 0 1 0 0 1 0 1 0 0], ...
                                 0.5, 0, 0.9, 1, 2, 0.8, 45, 20, M0img);
    perfnum =  asl_perf_subtractMB(FAIR,1, 0, 0, [0 0 1 0 0 1 0 1 0 0], ...
                                 0.5, 0, 0.9, 1, 2, 0.8, 45, 20, M0img);
    ```

---

### Function name: `ASLQuantificationPCASL.m`
*   **Description:** For pCASL, calculate the perfusion maps with difference images, M0 and related parameters according to the 2015 ASL white paper
*   **Inputs:** `data`, `M0` and `mask` should be the matrix for pCASL difference, proton density and brain mask images
*   **Outputs:** Will generate CBF maps in MATLAB workspace
*   **Syntax:** `[output, output_nantmean, NANCOUNTMASK] = ASLQuantificationPCASL(data, M0, 1.8, 1.8,1.6, 0.9, 0.6,'no','',14, 1, mask, 'yes', 'yesfigure');`

!!! note "Notes"
    This script needs small modification as shown in the script.

---

### Function name: `batch_calc_rcbf.m`
*   **Description:** Calculate the normalized perfusion maps divided by the mean flow
*   **Inputs:** Choose perfusion maps and mask in the pop out windows
*   **Outputs:** Will generate normalized CBF maps in same path as original CBF maps
*   **Syntax:** Just run the whole script, no function to call.

!!! note "Notes"
    This script seems to be one code from a whole pipeline. Therefore, there is dependency on passing the file path and subjects with spm batch system. But can use the core code lines as a separate function.

---

### Function name: `ASLDeltaM.m`
*   **Description:** Calculate the difference images from the control and label images
*   **Inputs:** `CTRL` and `TAG` are matrix values from the control and label images of ASL images, `method` can be any value as shown in the script
*   **Outputs:** Output will be a matrix for difference images in MATLAB workspace
*   **Syntax:** `Output=ASLDeltaM(CTRL,TAG,'PairWise');`

---

### Function name: `batch_perf_subtract.m`
*   **Description:** batch file for the same function as `asl_perf_subtract.m`

---

### Function name: `ASL_calculateCBFmap.m`
*   **Description:** This function obtains CBF value in the unit of ml/100g/min
*   **Inputs:** `path_temp`: the paths of the ASL images, `asl_paras`: the parameters of the ASL images
*   **Outputs:** a CBF map in `.img` format is created in the specified path
*   **Syntax:** `ASL_calculateCBFmap(path_temp,asl_paras)`

!!! note "Notes"
    The images are in `.img` format, instead of dicom or nifti.