import os

def test_repository_structure():
    assert os.path.exists("README.md")

def test_docs_folder_exists():
    assert os.path.exists("docs")