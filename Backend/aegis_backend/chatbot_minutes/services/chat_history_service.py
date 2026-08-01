from sqlalchemy.orm import Session
from ..models import ChatHistory, ConversationEntity, SessionSummary, UserPreference
from typing import Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class ChatHistoryService:
    @staticmethod
    def save_message(
        db: Session,
        user_id: int,
        session_id: str,
        role: str,
        message: str,
        response_metadata: Optional[Dict] = None,
    ) -> ChatHistory:
        chat_message = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            message=message,
            response_metadata=response_metadata,
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
    def get_memory_context(db: Session, user_id: int, session_id: str, recent_turns: int) -> tuple[Optional[str], List[ChatHistory]]:
        summary = db.query(SessionSummary).filter(
            SessionSummary.user_id == user_id,
            SessionSummary.session_id == session_id,
        ).first()
        recent = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id,
            ChatHistory.session_id == session_id,
        ).order_by(ChatHistory.timestamp.desc()).limit(recent_turns * 2).all()
        return (summary.summary if summary else None), list(reversed(recent))

    @staticmethod
    def upsert_session_summary(db: Session, user_id: int, session_id: str, summary: str, last_message_id: int) -> None:
        row = db.query(SessionSummary).filter(
            SessionSummary.user_id == user_id,
            SessionSummary.session_id == session_id,
        ).first()
        if row:
            row.summary, row.last_message_id = summary, last_message_id
        else:
            db.add(SessionSummary(user_id=user_id, session_id=session_id, summary=summary, last_message_id=last_message_id))
        db.commit()

    @staticmethod
    def remember_entities(db: Session, user_id: int, entities: List[Dict[str, str]]) -> None:
        """Persist only normal query entities; no prompt or secret content is retained."""
        for entity in entities[:12]:
            entity_type = (entity.get("type") or "topic").lower()[:100]
            value = (entity.get("value") or "").strip()[:500]
            if not value or len(value) < 2:
                continue
            row = db.query(ConversationEntity).filter_by(user_id=user_id, entity_type=entity_type, entity_value=value).first()
            if row:
                row.mentions += 1
            else:
                db.add(ConversationEntity(user_id=user_id, entity_type=entity_type, entity_value=value))
            if entity_type in {"company", "director", "topic", "regulation"}:
                preference = db.query(UserPreference).filter_by(user_id=user_id, preference_key=entity_type, preference_value=value).first()
                if preference:
                    preference.weight += 1
                else:
                    db.add(UserPreference(user_id=user_id, preference_key=entity_type, preference_value=value))
        db.commit()

    @staticmethod
    def extract_basic_entities(query: str) -> List[Dict[str, str]]:
        """Privacy-preserving fallback when the optional LLM planner is unavailable."""
        entities = []
        for value in re.findall(r"\b(?:SEBI|RBI|BSE|MCA|DIN|AGEL|Adani(?:\s+[A-Z][A-Za-z]+){0,3})\b", query):
            entity_type = "regulation" if value in {"SEBI", "RBI", "BSE", "MCA"} else "company"
            entities.append({"type": entity_type, "value": value})
        for value in re.findall(r"\b(?:FY\s?\d{2,4}(?:-\d{2,4})?|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", query):
            entities.append({"type": "date", "value": value})
        return entities

    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[dict]:
        sessions = db.query(ChatHistory.session_id).filter(
            ChatHistory.user_id == user_id
        ).distinct().all()
        
        results = []
        for (session_id,) in sessions:
            first_msg = db.query(ChatHistory).filter(
                ChatHistory.user_id == user_id,
                ChatHistory.session_id == session_id,
                ChatHistory.role == 'user'
            ).order_by(ChatHistory.timestamp.asc()).first()
            
            title = session_id
            if first_msg and first_msg.message:
                title = first_msg.message[:30] + ("..." if len(first_msg.message) > 30 else "")
                
            results.append({
                "id": session_id,
                "title": title
            })
            
        return results
