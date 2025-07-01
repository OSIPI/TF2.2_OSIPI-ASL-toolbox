# Outlier removal or Denoising

### `ASLtbx_aoc`

It adaptively removes CBF volumes from the CBF time series and averages the remaining volume to obtain the meanCBF map. The removal is based on estimated motion, and correlation between individual CBF volumes and mean CBF map. Algorithm based on https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3777751/

!!! info "Inputs"
    - CBF time series and optionally: text file with the estimated motion parameters realigning the raw ASL time series, brain mask in the ASL space, an algorithm specific threshold parameter (default 0.17) and number of iterations (default 2)

!!! success "Outputs"
    - Outlier volume numbers. Also generates the estimated CBF map obtained after outlier removal.

!!! example "Syntax"
    ```matlab
    ASLtbx_aoc(cbfimgs, motionfile, maskimg, th, iter)
    // See the help section of the code for details. 
    // Use the batch_outlier_clean to call the function
    ```

---
### `ASLtbx_aocSL`

It adaptively removes slices from CBF volumes in the CBF time series and averages the remaining slices and volumes to obtain the mean CBF map. Algorithm is based on https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3777751/

!!! info "Inputs"
    - CBF time series, c1img and c2img (GM and WM tissue probability maps obtained from SPM segmentation of high resolution T1 image, coregistered and downsampled to the ASL space), masking (brain mask in the ASL space), th (a threshold parameter, default =0.17, better to not change), motionfile (test file with the estimated motion parameters realigning the raw ASL time series)

!!! success "Outputs"
    - oidx: identified outliers. Also generates the estimated CBF map obtained after outlier removal.

!!! example "Syntax"
    ```matlab
    ASLtbx_aocSL(cbfimgs, c1img, c2img, maskimg, th, motionfile)
    ```

---
### `batch_SCORE_clean.m`

Calculate

!!! info "Inputs"
    - The path of perfusion maps, GM, WM and CSF Probability maps.

!!! success "Outputs"
    - Will

!!! warning "Notes"
    - This script seems to be one code from a whole pipeline. Therefore, there is dependency on passing the file path and subjects with spm batch system. But can use the core code lines as a separate function.

!!! example "Syntax"
    - Just run the whole script, no function to call. But does need to include the SCORE_denoising.m function.