# Smoothing

### `ASLtbx_smoothing`

smoothes an image, returns the smoothed image

!!! info "Inputs"
    - image path, and a kernel size

!!! success "Outputs"
    - smoothed image, written as a different file

!!! example "Syntax"
    ```matlab
    ASLtbx_smoothing(‘image.nii’, 2)
    ```

---
### `batch_smooth_wconfile` and `batch_smooth`

A code from pipeline. Needs dependency from the spm batch. It uses spm_smooth to smooth a number of files.

!!! info "Inputs"
    - path of the images

!!! success "Outputs"
    - smoothed images

!!! example "Syntax"
    - As this is part of the pipeline, just run the script, no function to call