

=============================================================================================
Git repo link: 
		https://github.com/physimals/oxford_asl	
==============================================================================================


A command line tool for quantification of perfusion from ASL data

oxford_asl is part of the BASIL toolbox within FSL for the analysis of perfusion ASL data. oxford_asl provides a single means to quantify CBF from ASL data, including kinetic-model inversion, absolute quantification via a calibration image and registration of the data. It provides most of the common options that someone who has raw ASL data might like to perform to extract perfusion images and thus is the normal place to begin for most users who want a command line tool.

oxford_asl is the main underlying tool behind the equivalent graphical user interface: Asl_gui. To use oxford_asl you may find you first need to pre-process your data using asl_file (see the tutorial for examples where this is relevant). More advanced users wishing to do customised kinetic analysis might want to use the basil command line tool - this is the very core of oxford_asl and thus the BASIL toolbox overall.

For full documentation on the oxford_asl suite of tools see:

https://asl-docs.readthedocs.io/