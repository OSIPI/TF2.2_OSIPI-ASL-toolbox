# Smoothing

### Function name: `ASLtbx_smoothing`
*   **Description:** smoothes an image, returns the smoothed image
*   **Inputs:** image path, and a kernel size
*   **Outputs:** smoothed image, written as a different file
*   **Syntax:** `ASLtbx_smoothing(‘image.nii’, 2)`

---

### Function name: `batch_smooth_wconfile` and `batch_smooth`
*   **Description:** A code from pipeline. Needs dependency from the spm batch. It uses spm_smooth to smooth a number of files.
*   **Inputs:** path of the images
*   **Outputs:** smoothed images
*   **Syntax:** As this is part of the pipeline, just run the script, no function to call