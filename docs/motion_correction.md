# Motion Correction

### Function name: `batch_realign.m`
*   **Description:** realigns raw EPI images using SPM realignment tools
*   **Inputs:** 4D NIfTI
*   **Outputs:** This script seems to be one code from a whole pipeline. Therefore, there is dependency on passing the file path and subjects.
*   **Syntax:** DNA

---

### Function name: `ASL_realign.m`
*   **Description:** motion correction
*   **Inputs:** `path_temp`: the path of the ASL image, `name_asl`:name of the ASL image
*   **Outputs:** Generates realigned images from the time series
*   **Syntax:** `P = ASL_realign(path_temp, name_asl)`