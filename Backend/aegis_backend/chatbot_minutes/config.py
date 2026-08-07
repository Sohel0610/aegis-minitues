"""Configuration for the Minutes Chatbot.

The same code runs in two deliberately separate modes:
* local demo: SQLite + Sentence Transformers + Groq + optional Tesseract
* Azure VM: PostgreSQL/pgvector or Azure AI Search + Cohere + Foundry/Azure OpenAI
"""
from __future__ import annotations

import os
import urllib.parse
from typing import List

from pydantic_settings import BaseSettings

from utils.shared_env import load_backend_env

load_backend_env()


class ChatbotSettings(BaseSettings):
    @property
    def DATABASE_URL(self) -> str:
        host = os.getenv("POSTGRES_HOST")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DATABASE_MINUTES") or os.getenv("POSTGRES_DATABASE")
        port = os.getenv("POSTGRES_PORT", "5432")
        sslmode = os.getenv("POSTGRES_SSLMODE", "require")
        if all([host, user, password, database]):
            safe_password = urllib.parse.quote_plus(password)
            return f"postgresql://{user}:{safe_password}@{host}:{port}/{database}?sslmode={sslmode}"
        return os.getenv("DATABASE_URL", "sqlite:///./data/minutes_chatbot_demo.db")

    # Runtime mode: local keeps all processing on the developer machine except
    # the explicitly configured Groq API call. Production switches providers by env.
    APP_ENV: str = os.getenv("APP_ENV", "local")
    CHATBOT_LLM_PROVIDER: str = os.getenv("CHATBOT_LLM_PROVIDER", "groq")
    CHATBOT_LLM_MODEL: str = os.getenv("CHATBOT_LLM_MODEL", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    CHATBOT_FALLBACK_LLM_PROVIDER: str = os.getenv(
        "CHATBOT_FALLBACK_LLM_PROVIDER",
        os.getenv("CHATBOT_LLM_FALLBACK_PROVIDER", ""),
    )
    CHATBOT_FALLBACK_LLM_MODEL: str = os.getenv(
        "CHATBOT_FALLBACK_LLM_MODEL",
        os.getenv("CHATBOT_LLM_FALLBACK_MODEL", ""),
    )
    CHATBOT_MAX_OUTPUT_TOKENS: int = int(os.getenv("CHATBOT_MAX_OUTPUT_TOKENS", "1800"))

    # Local Groq provider
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Azure OpenAI fallback (for example gpt-4.1-mini deployment)
    AZURE_OPENAI_ENDPOINT: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
    )
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    # Azure AI Foundry OpenAI-compatible endpoint. Set this for a deployed
    # Llama 4 Maverick (or another organisation-approved primary model).
    AZURE_FOUNDRY_ENDPOINT: str | None = os.getenv("AZURE_FOUNDRY_ENDPOINT")
    AZURE_FOUNDRY_API_KEY: str | None = os.getenv("AZURE_FOUNDRY_API_KEY")
    AZURE_FOUNDRY_DEPLOYMENT: str = os.getenv(
        "AZURE_FOUNDRY_DEPLOYMENT",
        os.getenv("AZURE_FOUNDRY_MODEL", ""),
    )
    AZURE_FOUNDRY_API_VERSION: str = os.getenv("AZURE_FOUNDRY_API_VERSION", "2024-10-21")

    # Embeddings: local Sentence Transformer for demo; Azure-hosted Cohere for VM.
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence_transformer")
    EMBEDDING_MODEL_PATH: str | None = os.getenv("EMBEDDING_MODEL_PATH")
    COHERE_API_KEY: str | None = os.getenv("COHERE_API_KEY")
    COHERE_AZURE_ENDPOINT: str | None = os.getenv("COHERE_AZURE_ENDPOINT")
    COHERE_EMBED_MODEL: str = os.getenv("COHERE_EMBED_MODEL", "embed-v4.0")
    COHERE_EMBED_DIMENSIONS: int = int(os.getenv("COHERE_EMBED_DIMENSIONS", "1024"))

    # Optional Azure AI Search production retrieval adapter.
    RETRIEVAL_BACKEND: str = os.getenv("RETRIEVAL_BACKEND", "database")
    AZURE_SEARCH_ENDPOINT: str | None = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_API_KEY: str | None = os.getenv("AZURE_SEARCH_API_KEY")
    AZURE_SEARCH_ADMIN_KEY: str | None = os.getenv("AZURE_SEARCH_ADMIN_KEY")
    AZURE_SEARCH_INDEX: str | None = os.getenv("AZURE_SEARCH_INDEX") or os.getenv("AZURE_SEARCH_INDEX_NAME")
    AZURE_SEARCH_VECTOR_FIELD: str = os.getenv("AZURE_SEARCH_VECTOR_FIELD", "content_vector")
    AZURE_SEARCH_CONTENT_FIELD: str = os.getenv("AZURE_SEARCH_CONTENT_FIELD", "content")
    AZURE_SEARCH_OWNER_FIELD: str = os.getenv("AZURE_SEARCH_OWNER_FIELD", "owner_user_id")

    # Ingestion: local native extraction with a Tesseract fallback now; Azure
    # Document Intelligence prebuilt-layout when the VM values are supplied.
    DOCUMENT_PROCESSOR: str = os.getenv("DOCUMENT_PROCESSOR", "local")
    OCR_ENABLED: bool = os.getenv("OCR_ENABLED", "true").lower() == "true"
    OCR_MIN_TEXT_PER_PAGE: int = int(os.getenv("OCR_MIN_TEXT_PER_PAGE", "40"))
    OCR_DPI: int = int(os.getenv("OCR_DPI", "220"))
    DOCUMENT_INTELLIGENCE_ENDPOINT: str | None = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
    DOCUMENT_INTELLIGENCE_API_KEY: str | None = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY")

    # Retrieval and memory safety limits.
    RETRIEVAL_CANDIDATES: int = int(os.getenv("RETRIEVAL_CANDIDATES", "20"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    RETRIEVAL_MIN_RELEVANCE: float = float(os.getenv("RETRIEVAL_MIN_RELEVANCE", "0.15"))
    MAX_CONTEXT_CHARS: int = int(os.getenv("MAX_CONTEXT_CHARS", "18000"))
    SESSION_SUMMARY_TURN_THRESHOLD: int = int(os.getenv("SESSION_SUMMARY_TURN_THRESHOLD", "20"))
    HISTORY_RECENT_TURNS: int = int(os.getenv("HISTORY_RECENT_TURNS", "4"))
    ENABLE_LLM_QUERY_PLANNER: bool = os.getenv("ENABLE_LLM_QUERY_PLANNER", "true").lower() == "true"
    ENABLE_LLM_FAITHFULNESS_CHECK: bool = os.getenv("ENABLE_LLM_FAITHFULNESS_CHECK", "false").lower() == "true"

    UPLOAD_DIR: str = os.getenv("CHATBOT_UPLOAD_DIR", "public/chatbot_docs")
    MAX_FILE_SIZE: int = int(os.getenv("CHATBOT_MAX_FILE_SIZE", "52428800"))
    ALLOWED_EXTENSIONS: str = os.getenv(
        "CHATBOT_ALLOWED_EXTENSIONS",
        "pdf,docx,xlsx,pptx,txt,json,png,jpg,jpeg,tif,tiff",
    )

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [extension.strip().lower() for extension in self.ALLOWED_EXTENSIONS.split(",") if extension.strip()]


settings = ChatbotSettings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
