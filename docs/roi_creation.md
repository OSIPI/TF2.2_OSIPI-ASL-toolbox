# Create ROIs

### `roipoly.m`

selects a polygonal region of interest within an image, this function should be similar to MATLAB’s built-in function “roipoly”.

!!! info "Inputs"
    - A 2D image file name

!!! success "Outputs"
    - returns a binary image that can be used as a mask for masked filtering, returns the polygon coordinates

!!! example "Syntax"
    ```matlab
    [BW, xi, yi] = roipoly(‘image.jpeg’);
    ```