import os, sys
from dotenv import load_dotenv
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)
env_path = os.path.join(_BACKEND_DIR, ".env")
load_dotenv(env_path)
API_URL = os.getenv("SERVICENOW_API_URL")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")
print("API_URL:", API_URL[:50] if API_URL else None)
print("USERNAME:", USERNAME)
print("PASSWORD:", "SET" if PASSWORD else "NOT SET")