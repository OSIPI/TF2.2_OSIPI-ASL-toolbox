# Segmentation of high-resolution images (Grey Matter and White Matter)

### `ASLtbx_spmnsegment`

Probabilistically segment the high resolution T1 images

!!! info "Inputs"
    - High resolution T1 image

!!! success "Outputs"
    - Probabilistic segmentations of GM, WM and CSF (file names starting with c1, c2 and c3)

!!! example "Syntax"
    ```matlab
    ASLtbx_spmnsegment(full_path_of_T1_Image)
    ```