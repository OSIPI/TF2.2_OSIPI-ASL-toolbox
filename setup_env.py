import os
import subprocess
import sys
import shutil

ENV_NAME = "venv"
REQUIREMENTS_FILE = "requirements.txt"
TEMP_DIR = "temp_dir"

def create_virtualenv():
    if not os.path.exists(ENV_NAME):
        print(f"Creating virtual environment '{ENV_NAME}'...")
        subprocess.run([sys.executable, "-m", "venv", ENV_NAME])
    else:
        print(f"Virtual environment '{ENV_NAME}' already exists.")

def install_requirements():
    pip_path = os.path.join(ENV_NAME, "Scripts" if os.name == "nt" else "bin", "pip")
    if os.path.exists(REQUIREMENTS_FILE):
        print(f"Installing packages from {REQUIREMENTS_FILE}...")
        subprocess.run([pip_path, "install", "-r", REQUIREMENTS_FILE])
    else:
        print(f"{REQUIREMENTS_FILE} not found. Please create one with your dependencies.")

def print_activation_instructions():
    print("\n✅ Setup complete!")
    print("\nTo activate the virtual environment:")
    if os.name == "nt":
        print(f"  source {ENV_NAME}/Scripts/activate")
    else:
        print(f"  source {ENV_NAME}/bin/activate")

    print("\nTo deactivate:")
    print("  deactivate")

def clean():
    print("Starting cleanup...")
    # Delete the virtual environment folder
    if os.path.isdir(ENV_NAME):
        print(f"Removing virtual environment: {ENV_NAME}...")
        shutil.rmtree(ENV_NAME)
    else:
        print(f"Virtual environment '{ENV_NAME}' not found.")

    # Delete the temp directory
    if os.path.isdir(TEMP_DIR):
        print(f"Removing temporary directory: {TEMP_DIR}...")
        shutil.rmtree(TEMP_DIR)
    else:
        print(f"Temporary directory '{TEMP_DIR}' not found.")

    print("Cleanup complete.")

def initialize_setup():
    clean()
    create_virtualenv()
    install_requirements()
    print_activation_instructions()

if __name__ == "__main__":
    import sys
    if "clean" in sys.argv:
        clean()
    if "initialize" in sys.argv:
        initialize_setup()
