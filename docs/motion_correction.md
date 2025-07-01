# Motion Correction

### `batch_realign.m`

realigns raw EPI images using SPM realignment tools

!!! info "Inputs"
    - 4D NIfTI

!!! success "Outputs"
    - This script seems to be one code from a whole pipeline. Therefore, there is dependency on passing the file path and subjects.

!!! example "Syntax"
    `DNA`

---
### `ASL_realign.m`

motion correction

!!! info "Inputs"
    - path_temp: the path of the ASL image, name_asl:name of the ASL image

!!! success "Outputs"
    - Generates realigned images from the time series

!!! example "Syntax"
    ```matlab
    P = ASL_realign(path_temp, name_asl)
    ```