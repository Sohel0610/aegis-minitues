"""
Chatbot API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from minutes_chatbot.database.connection import get_db_session
from minutes_chatbot.services.chatbot_service import ChatbotService
from minutes_chatbot.config.logging_config import logger
from minutes_chatbot.middleware import get_current_user
from minutes_chatbot.database.models import User

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


class QueryRequest(BaseModel):
    """Chatbot query request model"""
    query: str
    session_id: str


class QueryResponse(BaseModel):
    """Chatbot query response model"""
    answer: str
    sources: list


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Process chatbot query using RAG.
    
    Requires SSO authentication via Bearer token.
    Searches uploaded documents and generates answer using LLM.
    """
    try:
        # User is automatically extracted from SSO token
        logger.info(f"Processing query for user {user.email}: {request.query[:50]}...")
        
        # Process query
        chatbot_service = ChatbotService()
        result = chatbot_service.process_query(
            db=db,
            user_id=user.id,
            query=request.query,
            session_id=request.session_id
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    finally:
        db.close()
