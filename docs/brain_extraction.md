# Brain extraction/skull stripping

### `ASLtbx_createbrainmask.m`

use a single threshold to extract the brain, can manually change the threshold by the user

!!! info "Inputs"
    - full path to the input image as P='C:\Users\...\M02.nii';

!!! success "Outputs"
    - a brain mask file named 'brainmask.nii' with the same path as input

!!! warning "Notes"
    - This file needs modification: It seems spm_write_vol cannot write the mask well when the mask is only 0 and 1. Added several lines for modification

!!! example "Syntax"
    ```matlab
    maskimg=ASLtbx_createbrainmask(P)
    ```

---
### `batch_create_mask.m`

Use a single threshold to extract the brain region, can manually change the threshold by the user

!!! info "Inputs"
    - full path to the input image as PF='C:\Users\...\M02.nii';

!!! success "Outputs"
    - a brain mask file named 'mask_perf_cbf.img' with the same path as input

!!! warning "Notes"
    - This script seems to be one code from a whole pipeline. Therefore, there is dependency on passing the file path and subjects. But if we only took the core code for the test, this function is the same as the previous function . And need the same modification as in previous script

!!! example "Syntax"
    - 

---
### `ASL_getBrainMask.m`

motion correction

!!! info "Inputs"
    - imgtpm,imgfile,flag_addrealignmsk

!!! success "Outputs"
    - two masks are generated: brnmsk_dspl (datatype, logical), used for cbf map display;brnmsk_clcu (datatype, logical), used for glo_cbf calculation.

!!! example "Syntax"
    ```matlab
    [brnmsk_dspl, brnmsk_clcu] = ASL_getBrainMask(imgtpm,imgfile,flag_addrealignmsk)
    ```