"""
Agenda Service

Handles agenda detection and retrieval.
"""

from sqlalchemy.orm import Session
from minutes_chatbot.database.models import Agenda
from typing import List
from minutes_chatbot.config import logger


class AgendaService:
    """Service for agenda management"""
    
    @staticmethod
    def get_user_agendas(db: Session, user_id: int) -> List[Agenda]:
        """
        Get all agendas for a user.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            List of Agenda objects
        """
        agendas = db.query(Agenda).filter(Agenda.user_id == user_id).order_by(Agenda.meeting_date.desc()).all()
        logger.info(f"Retrieved {len(agendas)} agendas for user {user_id}")
        return agendas
    
    @staticmethod
    def create_agenda(db: Session, user_id: int, title: str, content: str = None, meeting_date: str = None) -> Agenda:
        """
        Create a new agenda (called by external AI system).
        
        Args:
            db: Database session
            user_id: User ID
            title: Agenda title
            content: Agenda content
            meeting_date: Meeting date (YYYY-MM-DD)
        
        Returns:
            Created Agenda object
        """
        agenda = Agenda(
            user_id=user_id,
            agenda_title=title,
            agenda_content=content,
            meeting_date=meeting_date
        )
        db.add(agenda)
        db.commit()
        db.refresh(agenda)
        logger.info(f"Created agenda: {title} for user {user_id}")
        return agenda
