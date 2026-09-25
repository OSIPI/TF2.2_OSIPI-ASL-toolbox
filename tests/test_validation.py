import sys
import os
import pytest

# Add root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.validation import validate_file


def test_valid_file(tmp_path):
    file = tmp_path / "test.nii"
    file.write_text("dummy")
    assert validate_file(str(file)) is True


def test_invalid_extension():
    with pytest.raises(ValueError):
        validate_file("file.txt")


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        validate_file("missing.nii")