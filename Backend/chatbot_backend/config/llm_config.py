"""
LLM Configuration Module
Handles configuration for different LLM providers
"""
import os
from dotenv import load_dotenv
from pathlib import Path

def _load_env_files():
    """Load the project env file even when the backend is started elsewhere."""
    backend_dir = Path(__file__).resolve().parents[2]
    load_dotenv(backend_dir / "aegis_backend" / ".env")
    load_dotenv()


def _clean_env_value(value):
    if value is None:
        return None

    value = value.strip()
    if not value or value.lower().startswith("your-"):
        return None

    return value


def _detect_provider():
    configured_provider = _clean_env_value(os.getenv("LLM_PROVIDER"))
    if configured_provider:
        return configured_provider.lower()

    azure_key = _clean_env_value(os.getenv("LLM_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))
    azure_endpoint = _clean_env_value(os.getenv("LLM_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT"))
    if azure_key and azure_endpoint:
        return "azure"

    if _clean_env_value(os.getenv("GROQ_API_KEY")):
        return "groq"

    return "azure"


# Load environment variables
_load_env_files()

class LLMConfig:
    """Configuration class for LLM settings"""
    
    # LLM Provider selection
    LLM_PROVIDER = _detect_provider()
    
    # Groq Configuration
    GROQ_API_KEY = _clean_env_value(os.getenv("GROQ_API_KEY"))
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Azure OpenAI Configuration
    AZURE_ENDPOINT = _clean_env_value(os.getenv("LLM_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT"))
    AZURE_DEPLOYMENT = _clean_env_value(os.getenv("LLM_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
    AZURE_API_KEY = _clean_env_value(os.getenv("LLM_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION") or "2023-05-15"
    
    @classmethod
    def is_azure_enabled(cls):
        """Check if Azure LLM is enabled"""
        return cls.LLM_PROVIDER == "azure"
    
    @classmethod
    def is_groq_enabled(cls):
        """Check if Groq LLM is enabled"""
        return cls.LLM_PROVIDER == "groq"
