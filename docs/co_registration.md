# Co-registration of ASL images to high resolution T1-weighted, T2-weighted, and/or FLAIR images

### `ASLtbx_spmcoreg.m`

using spm for registering source and allimgs to target.

!!! info "Inputs"
    - target, source, allimgs

!!! success "Outputs"
    - co-registered images

!!! example "Syntax"
    ```matlab
    [output]=ASLtbx_spmcoreg(target, source, allimgs)
    ```

---
### `ASL_coreg`

coregister source to target and apply transform matrix to source and varargin

!!! info "Inputs"
    - target,source,varargin

!!! success "Outputs"
    - co-registered images and transformation matrix

!!! example "Syntax"
    ```matlab
    ASL_coreg(target,source,varargin)
    ```

---
### `spm_reslice_yli`

similar to spm_reslice, does co-registration

!!! info "Inputs"
    - P - matrix or cell array of filenames flags - a structure containing various options.

!!! success "Outputs"
    - co-registered image files to the same subdirectory with a prefix.

!!! example "Syntax"
    ```matlab
    spm_reslice_yli(P,flags)
    ```