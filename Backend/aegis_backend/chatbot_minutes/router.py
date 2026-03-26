from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import uuid
from datetime import datetime

from .database import get_db_session, init_db
from .models import User, Document, ChatHistory
from .services.chatbot_service import ChatbotService
from .services.embedding_service import EmbeddingService
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/minutes-chatbot", tags=["Minutes Chatbot"])

# Dependency to get current user - adapting for integrated version
async def get_current_chatbot_user(request: Request, db: Session = Depends(get_db_session)):
    """
    Returns the current user based on SSO state.
    If SSO is disabled, returns a guest user.
    If SSO is enabled, in a real implementation we would validate the session.
    """
    sso_enabled = os.getenv("SSO_ENABLED", "true").lower() == "true"
    
    if not sso_enabled:
        email = "guest@adani.com" 
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, name="Guest User")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    # When SSO is enabled, we expect user info to be passed or resolved from session
    # For now, we'll look for an X-User-Email header as a simple integration pattern
    email = request.headers.get("X-User-Email")
    if not email:
        # Fallback for development if no header is present
        email = "guest@adani.com"
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=email.split("@")[0])
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

class QueryRequest(BaseModel):
    query: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session)
):
    try:
        # 1. RBAC check (Check if user is admin globally for this tool)
        from routes.rbac import check_route_permission
        permission = check_route_permission(user.email, "/api/minutes-chatbot")
        is_admin = (permission == "admin")

        chatbot_service = ChatbotService()
        result = chatbot_service.process_query(
            db=db,
            user_id=user.id,
            query=request.query,
            session_id=request.session_id,
            is_admin=is_admin
        )
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        logger.error(f"Chatbot query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session)
):
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(status_code=400, detail=f"File type .{file_ext} not allowed")

    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Extract text (simulated for now or use external tool)
    # In a real app, use python-docx, PyPDF2, etc.
    extracted_text = ""
    try:
        if file_ext == "docx":
            from docx import Document as DocxDoc
            doc = DocxDoc(file_path)
            extracted_text = "\n".join([para.text for para in doc.paragraphs])
        elif file_ext == "txt":
            extracted_text = content.decode("utf-8")
        elif file_ext == "pdf":
            try:
                import PyPDF2
                with open(file_path, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh)
                    extracted_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            except ImportError:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    extracted_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        else:
            extracted_text = f"Content of {file.filename}" # Placeholder for other types
    except Exception as e:
        logger.error(f"Text extraction error for {file.filename}: {e}")
        extracted_text = f"Error extracting text from {file.filename}"

    # Save to DB
    doc = Document(
        user_id=user.id,
        filename=file.filename,
        file_path=file_path,
        file_type=file_ext,
        file_size=len(content),
        extracted_text=extracted_text
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Generate embeddings
    try:
        embedding_service = EmbeddingService()
        embedding_service.create_document_embeddings(db, doc)
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        # We still return success for upload even if embedding fails

    return {"id": doc.id, "filename": doc.filename, "message": "Document uploaded and indexed"}

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session)
):
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == user.id,
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.timestamp.asc()).all()
    
    return [
        {"role": h.role, "message": h.message, "timestamp": h.timestamp}
        for h in history
    ]

@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session)
):
    """List all previous sessions for the user (ChatGPT history style)"""
    from .services.chat_history_service import ChatHistoryService
    service = ChatHistoryService()
    sessions = service.get_user_sessions(db, user.id)
    return {"sessions": sessions}

@router.get("/documents")
async def list_documents(
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session)
):
    docs = db.query(Document).filter(Document.user_id == user.id).all()
    return [
        {"id": d.id, "filename": d.filename, "upload_date": d.upload_date}
        for d in docs
    ]
