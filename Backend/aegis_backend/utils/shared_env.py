"""Shared environment loader for the backend.

All backend components should resolve configuration from the single
`Backend/aegis_backend/.env` file so local and Azure behavior stay aligned.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv


def load_backend_env() -> str:
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(backend_dir, ".env")
    load_dotenv(env_path, override=False)
    return env_path
