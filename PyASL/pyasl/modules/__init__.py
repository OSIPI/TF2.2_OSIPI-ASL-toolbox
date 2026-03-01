"""
ASL Processing Modules
======================

This package contains processing modules for Arterial Spin Labeling (ASL) MRI data.

The modules are organized by their source pipeline:

**ASLtbx** - SPM-based ASL processing pipeline
    Includes coregister, create_mask, perfusion_quantify, realign, 
    reset_orientation, and smooth modules.

**DL-ASL** - Deep learning-based ASL processing
    Provides build_mask and denoise_cbf for AI-powered processing.

**MRICloud** - Cloud-based ASL quantification pipeline
    Offers comprehensive quantification tools including calculate_CBF, calculate_M0,
    calculate_diffmap, coreg_mpr, multidelay variants, read_mpr, rescale,
    and t1roi_CBFaverage.

**Oxford ASL** - BASIL-based ASL analysis
    Features asl_run and asl_split_m0 for model-based analysis.

**Preclinical** - Modules for preclinical ASL data
    A complete suite for animal imaging including abs_t1fit, brain_mask,
    cbf_relative, compute_m0, control_label_split, diff_image, loader functions
    for Bruker and NIfTI formats, motion_check, slice_pld_adjust, and 
    steady_state_trim.

**Utilities**
    Common functionality like save_outputs.

Each module can be used independently or combined to build custom processing
pipelines tailored to your specific ASL acquisition and analysis needs.

Example Usage
-------------
You can import specific modules as needed:

    from pyasl.modules import asltbx_coregister
    from pyasl.modules import mricloud_calculate_CBF

See Also
--------
pyasl.pipelines : Ready-to-use processing pipelines
pyasl.utils : Data handling utilities
"""