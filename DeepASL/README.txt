
=============================================================================================
Git repo link: 
		https://github.com/cagdasulas/ASL_CNN	
==============================================================================================

This repository contains the implementation of the DeepASL paper published in MICCAI 2018:

DeepASL: Kinetic Model Incorporated Loss for Denoising Arterial Spin Labeled MRI via Deep Residual Learning

Publication Link: https://link.springer.com/chapter/10.1007/978-3-030-00928-1_4

ArXiv Link: https://arxiv.org/abs/1804.02755

The synthetic ASL data can be downloaded as .mat file from here: https://www.dropbox.com/s/vlmj8ty9oq5naak/synthetic_net_data.mat?dl=0

Put the synthetic data inside the project folder after downloading it.

Some common ASL related variables are stored in 'synthetic_common_vars.mat' and already availble in the repository.

The implementation is based on Keras framework with Tensorflow backend. Please ensure that both Keras and Tensorflow are installed to your machine before running the 'main.py' module.

Please cite the paper if you use this implementation in your work. If you have questions regarding the implementation or want to report any bug, please drop me an email through cagdas.ulas@tum.de