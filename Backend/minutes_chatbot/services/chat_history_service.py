"""
Chat History Service

Manages conversation history for users.
"""

from sqlalchemy.orm import Session
from minutes_chatbot.database.models import ChatHistory
from typing import List
from minutes_chatbot.config import logger


class ChatHistoryService:
    """Service for chat history management"""
    
    @staticmethod
    def save_message(
        db: Session,
        user_id: int,
        session_id: str,
        role: str,
        message: str
    ) -> ChatHistory:
        """
        Save a chat message.
        
        Args:
            db: Database session
            user_id: User ID
            session_id: Chat session ID
            role: 'user' or 'assistant'
            message: Message content
        
        Returns:
            Created ChatHistory object
        """
        chat_message = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            message=message
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        logger.debug(f"Saved {role} message for session {session_id}")
        return chat_message
    
    @staticmethod
    def get_session_history(
        db: Session,
        user_id: int,
        session_id: str,
        limit: int = 50
    ) -> List[ChatHistory]:
        """
        Get chat history for a session.
        
        Args:
            db: Database session
            user_id: User ID
            session_id: Chat session ID
            limit: Maximum number of messages to return
        
        Returns:
            List of ChatHistory objects
        """
        history = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id,
            ChatHistory.session_id == session_id
        ).order_by(ChatHistory.timestamp.asc()).limit(limit).all()
        
        logger.info(f"Retrieved {len(history)} messages for session {session_id}")
        return history
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[str]:
        """
        Get all session IDs for a user.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            List of session IDs
        """
        sessions = db.query(ChatHistory.session_id).filter(
            ChatHistory.user_id == user_id
        ).distinct().all()
        
        return [session[0] for session in sessions]
