# Brain extraction/skull stripping

### Function name: `ASLtbx_createbrainmask.m`
*   **Description:** use a single threshold to extract the brain, can manually change the threshold by the user
*   **Inputs:** full path to the input image as `P='C:\Users\...\M02.nii';`
*   **Outputs:** a brain mask file named 'brainmask.nii' with the same path as input
*   **Syntax:** `maskimg=ASLtbx_createbrainmask(P)`

!!! warning "Notes"
    This file needs modification: It seems `spm_write_vol` cannot write the mask well when the mask is only 0 and 1. Added several lines for modification.

---

### Function name: `batch_create_mask.m`
*   **Description:** Use a single threshold to extract the brain region, can manually change the threshold by the user
*   **Inputs:** full path to the input image as `PF='C:\Users\...\M02.nii';`
*   **Outputs:** a brain mask file named 'mask_perf_cbf.img' with the same path as input
*   **Syntax:**

!!! note "Notes"
    This script seems to be one code from a whole pipeline. Therefore, there is dependency on passing the file path and subjects. But if we only took the core code for the test, this function is the same as the previous function . And need the same modification as in previous script.

---

### Function name: `ASL_getBrainMask.m`
*   **Description:** motion correction
*   **Inputs:** `imgtpm`, `imgfile`, `flag_addrealignmsk`
*   **Outputs:** two masks are generated: `brnmsk_dspl` (datatype, logical), used for cbf map display; `brnmsk_clcu` (datatype, logical), used for glo_cbf calculation.
*   **Syntax:** `[brnmsk_dspl, brnmsk_clcu] = ASL_getBrainMask(imgtpm,imgfile,flag_addrealignmsk)`