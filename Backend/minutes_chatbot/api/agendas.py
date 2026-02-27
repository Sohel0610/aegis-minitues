"""
Agenda API Endpoints

For external AI system to create agendas.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from minutes_chatbot.database.connection import get_db_session
from minutes_chatbot.services.agenda_service import AgendaService
from minutes_chatbot.config.logging_config import logger
from minutes_chatbot.middleware import get_current_user
from minutes_chatbot.database.models import User
from datetime import date
from typing import Optional

router = APIRouter(prefix="/api/agendas", tags=["Agendas"])


class CreateAgendaRequest(BaseModel):
    """Request model for creating agenda"""
    title: str
    content: Optional[str] = None
    meeting_date: Optional[str] = None  # Format: YYYY-MM-DD


class AgendaResponse(BaseModel):
    """Agenda response model"""
    id: int
    title: str
    content: str = None
    meeting_date: str = None
    created_at: str


@router.post("/create", response_model=AgendaResponse)
async def create_agenda(
    request: CreateAgendaRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new agenda.
    
    User is automatically extracted from the session.
    
    Example:
        POST /api/agendas/create
        {
            "title": "Board Meeting - Q3 Review",
            "content": "1. Approve Q3 results\\n2. Budget approval",
            "meeting_date": "2024-02-15"
        }
    """
    try:
        # User is automatically extracted from the session
        logger.info(f"Creating agenda for user {user.email}: {request.title}")
        
        # Create agenda
        agenda = AgendaService.create_agenda(
            db=db,
            user_id=user.id,
            title=request.title,
            content=request.content,
            meeting_date=request.meeting_date
        )
        
        logger.info(f"Agenda created via API: {request.title} for {request.email}")
        
        return AgendaResponse(
            id=agenda.id,
            title=agenda.agenda_title,
            content=agenda.agenda_content,
            meeting_date=str(agenda.meeting_date) if agenda.meeting_date else None,
            created_at=str(agenda.created_at)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create agenda error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create agenda: {str(e)}")
    finally:
        db.close()


@router.get("/list")
async def list_user_agendas(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get all agendas for the authenticated user.
    
    Returns list of agendas sorted by meeting date (most recent first).
    """
    try:
        # User is automatically extracted from the session
        logger.info(f"Listing agendas for user {user.email}")
        
        # Get agendas
        agendas = AgendaService.get_user_agendas(db=db, user_id=user.id)
        
        return {
            "email": user.email,
            "agendas": [
                {
                    "id": agenda.id,
                    "title": agenda.agenda_title,
                    "content": agenda.agenda_content,
                    "meeting_date": str(agenda.meeting_date) if agenda.meeting_date else None,
                    "created_at": str(agenda.created_at)
                }
                for agenda in agendas
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List agendas error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/import-from-ai-assistant")
async def import_meeting_from_ai_assistant(
    task_id: str,
    user_email: str,
    db: Session = Depends(get_db_session)
):
    """
    Import COMPLETE meeting data from AEGIS AI Assistant.
    
    This endpoint reads the mom.json file created by the AI assistant
    and imports ALL meeting data into the chatbot database:
    - Agendas
    - Decisions
    - Action Items
    - Attendees
    
    Args:
        task_id: AI assistant task ID (UUID)
        user_email: Email of user who owns this meeting
    
    Returns:
        Summary of imported data
    
    Example:
        POST /api/agendas/import-from-ai-assistant
        {
            "task_id": "abc-123-def",
            "user_email": "cfo@adanigreen.com"
        }
    """
    try:
        from services.meeting_integration_service import MeetingIntegrationService
        
        # Import complete meeting data
        results = MeetingIntegrationService.import_from_task_id(
            db=db,
            task_id=task_id,
            user_email=user_email
        )
        
        total_items = sum(results.values())
        
        return {
            "success": True,
            "message": f"Imported {total_items} items from meeting",
            "details": {
                "agendas": results.get('agendas', 0),
                "decisions": results.get('decisions', 0),
                "action_items": results.get('action_items', 0),
                "attendees": results.get('attendees', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error importing meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/import-all-from-directory")
async def import_all_meetings(
    user_email: str,
    db: Session = Depends(get_db_session)
):
    """
    Import ALL meetings from AI assistant directory.
    
    This is useful for bulk import of existing meetings.
    Imports all meeting data: agendas, decisions, action items, attendees.
    
    Args:
        user_email: Email of user who owns these meetings
    
    Returns:
        Summary of all imported meetings
    """
    try:
        from services.meeting_integration_service import MeetingIntegrationService
        
        directory_path = "/Users/sohelkumarsahoo/Downloads/aegis_chatbot_shared_3/aegis_backend/public/ai_assistant_mom"
        
        results = MeetingIntegrationService.import_all_from_directory(
            db=db,
            directory_path=directory_path,
            user_email=user_email
        )
        
        # Calculate totals
        total_agendas = sum(r.get('agendas', 0) for r in results.values() if isinstance(r, dict))
        total_decisions = sum(r.get('decisions', 0) for r in results.values() if isinstance(r, dict))
        total_action_items = sum(r.get('action_items', 0) for r in results.values() if isinstance(r, dict))
        total_attendees = sum(r.get('attendees', 0) for r in results.values() if isinstance(r, dict))
        
        return {
            "success": True,
            "message": f"Imported {len(results)} meetings",
            "summary": {
                "meetings": len(results),
                "total_agendas": total_agendas,
                "total_decisions": total_decisions,
                "total_action_items": total_action_items,
                "total_attendees": total_attendees
            },
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Error importing all meetings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
