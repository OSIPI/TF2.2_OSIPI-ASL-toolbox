
=============================================================================================
Git repo link: 
		https://github.com/physimals/basil	
==============================================================================================

Arterial Spin Labeling (ASL) MRI is a non-invasive method for the quantification of perfusion.

Analysis of ASL data typically requires the inversion of a kinetic model of label inflow along with a separate calculation of the equilibrium magnetization of arterial blood. The BASIL toolbox provides a means to do this based on Bayeisan inference principles. The method was orginally developed for multi delay (inversion time) data where it can be used to greatest effect, but is also sufficiently fleixble to deal with the widely used single delay form of acquisition.

This project is part of the wider BASIL toolbox, distributed within FSL (www.fmrib.ox.ac.uk/fsl/basil). The basil script provided in this project is a lexible command line interface for use in the quantification of perfusion using ASL kinetic models. It relies in FABBER and specific ASL models implemented within that algorithm. Direct use of the basil script would normally be done only be more advanced users seeking options not available in the high-level tools of the BASIL toolbox. BASIL is used by oxford_asl the main interface for ASL analysis in FSL (and also for the associated GUI).

To use the code in this project you need to ensure you have the appropriate version of FABBER installed with the correct models. A package may be available on the GITlab for this express purpose. Do not assume any given version of basil is directly compatible with the current release of FSL.