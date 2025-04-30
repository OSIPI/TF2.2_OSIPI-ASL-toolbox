from setuptools import setup, find_packages

setup(
    name="pyasl-osipi",
    version="0.1.1",
    description="A composite, open-source Python library for processing human and preclinical ASL MRI data.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OSIPI/TF2.2_OSIPI-ASL-toolbox/tree/main/PyASL",
    author="OSIPI",
    author_email="trico010725@gmail.com",
    license="MIT License",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "pyasl": ["models/*.hdf5", "tpm/*.nii"],
    },
    install_requires=[
        "numpy>=1.20",
        "nibabel>=3.2.0",
        "nipype>=1.5.1",
        "scipy>=1.7.0",
        "scikit-image>=0.19.0",
        "pandas>=1.5.0",
        "tensorflow>=2.10",
        "matplotlib>=3.5",
        "pyyaml>=6.0",
        "fsspec>=2022.5.0",
        "jinja2>=3.0",
        "typing-extensions>=4.8.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
