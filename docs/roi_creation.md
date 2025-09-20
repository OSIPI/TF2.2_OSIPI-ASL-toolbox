# Create ROIs

### Function name: `roipoly.m`
*   **Description:** selects a polygonal region of interest within an image, this function should be similar to MATLAB’s built-in function “roipoly”.
*   **Inputs:** A 2D image file name
*   **Outputs:** returns a binary image that can be used as a mask for masked filtering, returns the polygon coordinates
*   **Syntax:** `[BW, xi, yi] = roipoly(‘image.jpeg’);`