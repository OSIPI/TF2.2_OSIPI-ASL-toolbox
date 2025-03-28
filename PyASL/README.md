# PyASL: Composite Python Library for ASL Image Processing

**PyASL** is an open-source Python library for processing arterial spin labeling (ASL) MRI data, developed under the [Google Summer of Code (GSoC)](https://summerofcode.withgoogle.com/) program for the [ISMRM OSIPI Task Force 2.2](https://osipi.ismrm.org/task-forces/task-force-2-2/).

It integrates multiple community-validated ASL tools, originally in MATLAB, and supports both human and preclinical pipelines. PyASL includes modules for ASL-MRICloud, ASLtbx, DL-ASL, Oxford ASL, preclinical multi-TI PASL, and preclinical pCASL, harmonized with ASL-BIDS input format.



## Features

- 🧠 Human and 🐭 preclinical ASL support
- 📂 ASL-BIDS format compatibility
- 📘 [Tutorials and Documentation](https://github.com/Trico01/pyasl/wiki/Tutorials)



## Installation
You can install PyASL using pip:

```bash
pip install pyasl-osipi
```



## Quick Start
```python
import pyasl
pyasl.load_data("/path/to/data", "/path/to/parameters.json", convert=True, is_singledelay=True, is_labelcontrol=False)
pyasl.mricloud_pipeline("/path/to/data", flag_t1=False, t1_tissue=1165, t1_blood=1650, part_coef=0.9)
```



## Citation

This library is part of the ISMRM 2025 submission:
*ISMRM Open Science Initiative for Perfusion Imaging (OSIPI): Composite Python Library for ASL Image Processing*



## License
This project is licensed under the MIT License – see the [LICENSE](https://github.com/OSIPI/TF2.2_OSIPI-ASL-toolbox/blob/main/PyASL/LICENSE) file for details.
Original repository: https://github.com/Trico01/PyASL