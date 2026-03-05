import sys
import os
import subprocess

def setup_and_run_venv():
    # Check if user explicitly wants to use global packages
    if "--use-global" in sys.argv:
        sys.argv.remove("--use-global")
        return

    # Check if already running in a virtual environment
    in_venv = getattr(sys, "base_prefix", sys.prefix) != sys.prefix

    if not in_venv:
        print("Not running in a virtual environment. Initializing one...")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        venv_dir = os.path.join(base_dir, ".venv")
        
        # Create venv if it doesn't exist
        if not os.path.exists(venv_dir):
            print(f"Creating virtual environment in {venv_dir}...")
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        
        # Determine executable paths
        if os.name == 'nt':
            python_exec = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_exec = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_exec = os.path.join(venv_dir, "bin", "python")
            pip_exec = os.path.join(venv_dir, "bin", "pip")
            
        # Install requirements
        req_file = os.path.join(base_dir, "requirements.txt")
        if os.path.exists(req_file):
            print("Installing/updating requirements...")
            # We redirect stdout to DEVNULL to avoid noisy install logs on every startup unless there's an error
            subprocess.run([pip_exec, "install", "-r", req_file], check=True, stdout=subprocess.DEVNULL)
            
        # Relaunch script using the venv's python
        print("Relaunching in virtual environment...")
        sys.exit(subprocess.run([python_exec, __file__] + sys.argv[1:]).returncode)

setup_and_run_venv()

from app import app
from flasgger import Swagger

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

template = {
    "swagger": "2.0",
    "info": {
        "title": "Minihotel Management API",
        "description": "REST API for hotel management system"
    },
    "basePath": "/api",
    "schemes": ["http", "https"]
}

Swagger(app, config=swagger_config, template=template)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)