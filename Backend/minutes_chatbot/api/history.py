"""
Chat History API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from minutes_chatbot.database.connection import get_db_session
from minutes_chatbot.services.chat_history_service import ChatHistoryService
from minutes_chatbot.config.logging_config import logger
from minutes_chatbot.middleware import get_current_user
from minutes_chatbot.database.models import User

router = APIRouter(prefix="/api/history", tags=["Chat History"])


@router.get("/")
async def get_chat_history(
    session_id: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get chat history for a session.
    
    Requires SSO authentication via Bearer token.
    Returns all messages (user + assistant) for the specified session.
    """
    try:
        # User is automatically extracted from SSO token
        logger.info(f"Getting chat history for user {user.email}, session {session_id}")
        
        # Get chat history
        history = ChatHistoryService.get_session_history(
            db=db,
            user_id=user.id,
            session_id=session_id
        )
        
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg.role,
                    "message": msg.message,
                    "timestamp": str(msg.timestamp)
                }
                for msg in history
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/sessions")
async def get_user_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get all session IDs for the authenticated user.
    
    Requires SSO authentication via Bearer token.
    """
    try:
        # User is automatically extracted from SSO token
        logger.info(f"Getting sessions for user {user.email}")
        
        # Get sessions
        sessions = ChatHistoryService.get_user_sessions(db=db, user_id=user.id)
        
        return {"sessions": sessions}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
