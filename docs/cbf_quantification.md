# Cerebral Blood Flow (CBF) quantification

### `asl_perf_subtract.m` / `asl_perf_subtractMB.m`

For CASL and PASL, generate the difference and calculate the perfusion images from control/label and M0 images

!!! info "Inputs"
    - Please see the description in the MATLAB code for detailed information.

!!! success "Outputs"
    - Will output CBF maps into the path you defined

!!! example "Syntax"
    ```matlab
    One example for PASL quantification. Both P and M0img are paths for control/label and M0 images: FAIR='C:\Users\...\FAIR_CL.nii'.
    perfnum =  asl_perf_subtract(FAIR,1, 0, 0, [0 0 1 0 0 1 0 1 0 0], ...
                                 0.5, 0, 0.9, 1, 2, 0.8, 45, 20, M0img);
    perfnum =  asl_perf_subtractMB(FAIR,1, 0, 0, [0 0 1 0 0 1 0 1 0 0], ...
                                 0.5, 0, 0.9, 1, 2, 0.8, 45, 20, M0img);
    ```

---
### `ASLQuantificationPCASL.m`

For pCASL, calculate the perfusion maps with difference images, M0 and related parameters according to the 2015 ASL white paper

!!! info "Inputs"
    - data, M0 and mask should be the matrix for pCASL difference, proton density and brain mask images

!!! success "Outputs"
    - Will generate CBF maps in MATLAB workspace

!!! warning "Notes"
    - This script needs small modification as shown in the script.

!!! example "Syntax"
    ```matlab
    [output, output_nantmean, NANCOUNTMASK] = ASLQuantificationPCASL(data, M0, 1.8, 1.8,1.6, 0.9, 0.6,'no','',14, 1, mask, 'yes', 'yesfigure');
    ```

---
### `batch_calc_rcbf.m`

Calculate the normalized perfusion maps divided by the mean flow

!!! info "Inputs"
    - Choose perfusion maps and mask in the pop out windows

!!! success "Outputs"
    - Will generate normalized CBF maps in same path as original CBF maps

!!! warning "Notes"
    - This script seems to be one code from a whole pipeline. Therefore, there is dependency on passing the file path and subjects with spm batch system. But can use the core code lines as a separate function.

!!! example "Syntax"
    - Just run the whole script, no function to call.

---
### `ASLDeltaM.m`

Calculate the difference images from the control and label images

!!! info "Inputs"
    - CTRL and TAG are matrix values from the control and label images of ASL images, method can be any value as shown in the script

!!! success "Outputs"
    - Output will be a matrix for difference images in MATLAB workspace

!!! example "Syntax"
    ```matlab
    Output=ASLDeltaM(CTRL,TAG,'PairWise');
    ```

---
### `batch_perf_subtract.m`

batch file for the same function as asl_perf_subtract.m

---
### `ASL_calculateCBFmap.m`

This function obtains CBF value in the unit of ml/100g/min

!!! info "Inputs"
    - path_temp: the paths of the ASL images, asl_paras: the parameters of the ASL images

!!! success "Outputs"
    - a CBF map in .img format is created in the specified path

!!! warning "Notes"
    - the images are in .img format, instead of dicom or nifti

!!! example "Syntax"
    ```matlab
    ASL_calculateCBFmap(path_temp,asl_paras)
    ```