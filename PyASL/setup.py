from setuptools import setup, find_packages

setup(
    name="pyasl",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "nibabel",
        "nipype",
        "scipy",
        "scikit-image",
        "pandas",
        "tensorflow",
    ],
    author="Trico",
    author_email="trico010725@gmail.com",
)
