"""API package initialization"""
from .documents import router as documents_router
from .chatbot import router as chatbot_router
from .history import router as history_router
from .agendas import router as agendas_router

__all__ = [
    "documents_router",
    "chatbot_router",
    "history_router",
    "agendas_router",
]
