"""
LLM Configuration Module
Handles configuration for different LLM providers
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMConfig:
    """Configuration class for LLM settings"""
    
    # LLM Provider selection
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Azure OpenAI Configuration
    AZURE_ENDPOINT = os.getenv("LLM_ENDPOINT", "https://az10oaidmrctbtp01.openai.azure.com")
    AZURE_DEPLOYMENT = os.getenv("LLM_DEPLOYMENT", "az10gpt41mdmrctbtp01")
    AZURE_API_KEY = os.getenv("LLM_API_KEY", "a026dffd6de4451f8986fe1a6e1a1649")
    AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2023-05-15")
    
    @classmethod
    def is_azure_enabled(cls):
        """Check if Azure LLM is enabled"""
        return cls.LLM_PROVIDER == "azure"
    
    @classmethod
    def is_groq_enabled(cls):
        """Check if Groq LLM is enabled"""
        return cls.LLM_PROVIDER == "groq"