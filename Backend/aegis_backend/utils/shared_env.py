import os
from dotenv import load_dotenv

def load_backend_env() -> None:
    """Load environment variables from .env in aegis_backend directory."""
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    aegis_backend_dir = os.path.dirname(utils_dir)
    env_path = os.path.join(aegis_backend_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
