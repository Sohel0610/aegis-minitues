import os
from pydantic_settings import BaseSettings
from typing import List

class ChatbotSettings(BaseSettings):
    # Database - Default to SQLite in the Backend directory
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5436/chatbot_minutes")
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-o")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
    
    # Groq (for local testing if Azure is not available)
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Local Embedding Model (sentence-transformers)
    EMBEDDING_MODEL_PATH: str | None = os.getenv("EMBEDDING_MODEL_PATH")
    
    # Application
    # Base uploads dir relative to Backend directory
    UPLOAD_DIR: str = os.getenv("CHATBOT_UPLOAD_DIR", "public/chatbot_docs")
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,docx,xlsx,pptx,doc,xls,ppt,txt,json"

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

settings = ChatbotSettings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
