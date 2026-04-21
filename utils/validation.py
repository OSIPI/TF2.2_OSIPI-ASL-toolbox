import os

def validate_file(path: str) -> bool:

    # FIRST check extension
    if not path.endswith(".nii"):
        raise ValueError("Only .nii files allowed")

    # THEN check existence
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")

    return True