from sqlalchemy.orm import Session
from ..models import ChatHistory
from typing import List
import logging

logger = logging.getLogger(__name__)

class ChatHistoryService:
    @staticmethod
    def save_message(
        db: Session,
        user_id: int,
        session_id: str,
        role: str,
        message: str
    ) -> ChatHistory:
        chat_message = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            message=message
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        return chat_message

    @staticmethod
    def get_session_history(
        db: Session,
        user_id: int,
        session_id: str,
        limit: int = 50
    ) -> List[ChatHistory]:
        return db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id,
            ChatHistory.session_id == session_id
        ).order_by(ChatHistory.timestamp.asc()).limit(limit).all()

    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[str]:
        sessions = db.query(ChatHistory.session_id).filter(
            ChatHistory.user_id == user_id
        ).distinct().all()
        return [session[0] for session in sessions]
