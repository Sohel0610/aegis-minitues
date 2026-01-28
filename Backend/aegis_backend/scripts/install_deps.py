"""
Script to install backend dependencies
"""
import subprocess
import sys
import os

def install_dependencies():
    """Install Python dependencies from requirements.txt"""
    try:
        # Check if pip is available
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
        print("pip is available")
    except subprocess.CalledProcessError:
        print("pip is not available. Please install Python and pip.")
        return False
    
    # Install dependencies
    try:
        requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

if __name__ == "__main__":
    success = install_dependencies()
    if not success:
        sys.exit(1)