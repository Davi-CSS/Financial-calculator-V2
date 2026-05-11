import subprocess
import sys
import os

# Create virtual environment
subprocess.check_call([sys.executable, "-m", "venv", "venv"])

# Activate virtual environment and install requirements
if os.name == "nt":
	activate_script = ".\\venv\\Scripts\\activate"
	pip_executable = ".\\venv\\Scripts\\pip"
	python_executable = ".\\venv\\Scripts\\python"
else:
	activate_script = "./venv/bin/activate"
	pip_executable = "./venv/bin/pip"
	python_executable = "./venv/bin/python"

subprocess.check_call([pip_executable, "install", "-r", "backend/requirements.txt"])

# Run the Flask app
subprocess.check_call([python_executable, "backend/flask_app.py"])