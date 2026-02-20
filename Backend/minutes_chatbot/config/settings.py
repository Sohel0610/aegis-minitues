"""
Configuration Management for Minutes Chatbot

This module handles all configuration settings using Pydantic Settings.
Environment variables are loaded from .env file.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database (PostgreSQL for production, SQLite for local)
    DATABASE_URL: str | None = None  # Direct database URL (for SQLite)
    PGHOST: str | None = None
    PGUSER: str | None = None
    PGPORT: int = 5432
    PGDATABASE: str | None = None
    PGPASSWORD: str | None = None
    
    # Azure OpenAI (optional - for production only)
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    AZURE_OPENAI_API_VERSION: str = "2023-12-01-preview"
    
    # Groq API (optional - for local testing)
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    
    # Local Embedding Model (sentence-transformers)
    # Path to pre-downloaded model directory
    EMBEDDING_MODEL_PATH: str | None = None
    
    # Application
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,docx,xlsx,pptx,doc,xls,ppt,txt,json"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/minutes_chatbot.log"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    class Config:
        env_file = ".env.local"  # Try .env.local first for local testing
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields
    
    @property
    def database_url(self) -> str:
        """Construct database connection URL"""
        # If DATABASE_URL is set directly (for SQLite), use it
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Otherwise, construct PostgreSQL URL
        if all([self.PGHOST, self.PGUSER, self.PGPASSWORD, self.PGDATABASE]):
            return f"postgresql://{self.PGUSER}:{self.PGPASSWORD}@{self.PGHOST}:{self.PGPORT}/{self.PGDATABASE}"
        
        # Default to SQLite for local testing
        return "sqlite:///./local_chatbot_test.db"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get list of allowed file extensions"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get list of CORS origins"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Create global settings instance
settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
