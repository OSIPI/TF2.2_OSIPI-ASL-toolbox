# Co-registration of ASL images to high resolution T1-weighted, T2-weighted, and/or FLAIR images

### Function name: `ASLtbx_spmcoreg.m`
*   **Description:** using spm for registering source and allimgs to target.
*   **Inputs:** `target`, `source`, `allimgs`
*   **Outputs:** co-registered images
*   **Syntax:** `[output]=ASLtbx_spmcoreg(target, source, allimgs)`

---

### Function name: `ASL_coreg`
*   **Description:** coregister source to target and apply transform matrix to source and varargin
*   **Inputs:** `target`, `source`, `varargin`
*   **Outputs:** co-registered images and transformation matrix
*   **Syntax:** `ASL_coreg(target,source,varargin)`

---

### Function name: `spm_reslice_yli`
*   **Description:** similar to spm_reslice, does co-registration
*   **Inputs:** `P` - matrix or cell array of filenames flags - a structure containing various options.
*   **Outputs:** co-registered image files to the same subdirectory with a prefix.
*   **Syntax:** `spm_reslice_yli(P,flags)`