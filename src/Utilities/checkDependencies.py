import importlib
import subprocess
import sys


class VerifyDependencies:
    def __init__(self, requirements_path="requirements.txt"):
        self.install_from_requirements(requirements_path)

    def install_from_requirements(self, requirements_path="requirements.txt"):
        print(f"Installing dependencies from {requirements_path}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])