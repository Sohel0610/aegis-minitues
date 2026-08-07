from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import uuid
from datetime import datetime, date as date_type

from .database import get_db_session, init_db
from .models import User, Document, ChatHistory, MeetingMetadata
from .services.chatbot_service import ChatbotService
from .services.embedding_service import EmbeddingService
from .services.document_extractor import extract_document
from .services.metadata_extractor import MeetingMetadataExtractor
from .config import settings
from utils.auth_dep import require_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/minutes-chatbot", tags=["Minutes Chatbot"])


@router.get("/status")
async def chatbot_status():
    """Non-sensitive configuration status for the UI; never returns keys/endpoints."""
    return {
        "status": "ready",
        "environment": settings.APP_ENV,
        "llm_provider": settings.CHATBOT_LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "document_processor": settings.DOCUMENT_PROCESSOR,
    }

# Dependency to get current user - adapting for integrated version
async def get_current_chatbot_user(claims: dict = Depends(require_session), db: Session = Depends(get_db_session)):
    """
    Returns the current user based on SSO state.
    If SSO is disabled, returns a guest user.
    If SSO is enabled, in a real implementation we would validate the session.
    """
    # The complete platform startup can include optional Azure/PostgreSQL modules.
    # Ensure this isolated local SQLite chatbot is usable even if another module
    # fails its startup initialization.
    init_db()
    email = claims["email"].lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=claims.get("name") or email.split("@")[0])
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

class QueryRequest(BaseModel):
    query: str
    session_id: str
    document_ids: Optional[List[int]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_mode: str
    response_format: str
    confidence: Dict[str, Any]
    activity: List[str]

class MetadataUpdateRequest(BaseModel):
    meeting_title: Optional[str] = None
    meeting_date: Optional[str] = None  # YYYY-MM-DD
    meeting_type: Optional[str] = None
    company_name: Optional[str] = None
    project_name: Optional[str] = None
    participants: Optional[List[Dict[str, str]]] = None
    chairperson: Optional[str] = None
    agenda_summary: Optional[str] = None
    key_topics: Optional[List[str]] = None
    key_decisions: Optional[List[str]] = None
    action_items_summary: Optional[List[Dict[str, str]]] = None
    meeting_summary: Optional[str] = None

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session)
):
    try:
        # Local demo mode uses the isolated SQLite chatbot and intentionally does
        # not contact the platform RBAC PostgreSQL database.
        if os.getenv("SSO_ENABLED", "false").lower() == "true":
            from routes.rbac import check_route_access
            rbac_resp = await check_route_access(user.email, "/api/minutes-chatbot")
            is_admin = (rbac_resp.permission_type == "admin")
        else:
            is_admin = False

        chatbot_service = ChatbotService()
        result = chatbot_service.process_query(
            db=db,
            user_id=user.id,
            query=request.query,
            session_id=request.session_id,
            is_admin=is_admin,
            document_ids=request.document_ids,
        )
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            retrieval_mode=result["retrieval_mode"],
            response_format=result["response_format"],
            confidence=result["confidence"],
            activity=result["activity"],
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
    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename or "." not in safe_filename:
        raise HTTPException(status_code=400, detail="A filename with a supported extension is required")
    file_ext = safe_filename.rsplit(".", 1)[-1].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(status_code=400, detail=f"File type .{file_ext} not allowed")

    # Validate size before persisting.  Large OCR/scanned PDFs should be routed to
    # Azure Document Intelligence once that service is approved.
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE // 1024 // 1024}MB limit")

    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{safe_filename}")
    
    with open(file_path, "wb") as f:
        f.write(content)

    extraction = None
    try:
        extraction = extract_document(file_path, file_ext)
        if not extraction.text.strip():
            raise ValueError("No machine-readable text found; this document likely needs OCR")
    except Exception as e:
        logger.error(f"Text extraction error for {file.filename}: {e}")
        raise HTTPException(status_code=422, detail=f"Could not extract readable text: {e}")

    # Save to DB
    doc = Document(
        user_id=user.id,
        filename=safe_filename,
        file_path=file_path,
        file_type=file_ext,
        file_size=len(content),
        extracted_text=extraction.text,
        processing_status="extracting_complete",
        extraction_method=extraction.extractor,
        extraction_metadata=extraction.as_metadata(),
        page_count=extraction.page_count,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # ---- Extract meeting metadata (non-blocking) ----
    meeting_meta_dict: Dict[str, Any] = {}
    try:
        extractor = MeetingMetadataExtractor()
        meeting_meta_dict = extractor.extract(extraction.text, safe_filename)
        parsed_date = None
        if meeting_meta_dict.get("meeting_date"):
            try:
                parsed_date = datetime.strptime(str(meeting_meta_dict["meeting_date"])[:10], "%Y-%m-%d").date()
            except ValueError:
                parsed_date = None
        meta = MeetingMetadata(
            document_id=doc.id,
            user_id=user.id,
            meeting_title=meeting_meta_dict.get("meeting_title"),
            meeting_date=parsed_date,
            meeting_type=meeting_meta_dict.get("meeting_type"),
            company_name=meeting_meta_dict.get("company_name"),
            project_name=meeting_meta_dict.get("project_name"),
            participants=meeting_meta_dict.get("participants", []),
            chairperson=meeting_meta_dict.get("chairperson"),
            agenda_summary=meeting_meta_dict.get("agenda_summary"),
            key_topics=meeting_meta_dict.get("key_topics", []),
            key_decisions=meeting_meta_dict.get("key_decisions", []),
            action_items_summary=meeting_meta_dict.get("action_items_summary", []),
            meeting_summary=meeting_meta_dict.get("meeting_summary"),
            extraction_confidence=meeting_meta_dict.get("extraction_confidence", "auto"),
        )
        db.add(meta)
        db.commit()
        logger.info("Meeting metadata extracted for document %s: %s", doc.id, meeting_meta_dict.get("meeting_title"))
    except Exception as e:
        logger.warning(f"Meeting metadata extraction failed for {safe_filename} (non-blocking): {e}")
        db.rollback()

    # ---- Generate embeddings ----
    try:
        embedding_service = EmbeddingService()
        chunks_created = embedding_service.create_document_embeddings(db, doc)
        if settings.RETRIEVAL_BACKEND.lower() == "azure_ai_search":
            from .services.azure_search_indexer import AzureSearchIndexer
            AzureSearchIndexer().upsert_document(db, doc)
        doc.processing_status = "ready"
        db.commit()
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        doc.processing_status = "failed"
        doc.processing_error = "Embedding/indexing failed. Check the embedding provider configuration and retry."
        db.commit()
        raise HTTPException(status_code=500, detail=doc.processing_error)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.processing_status,
        "pages": doc.page_count,
        "warnings": extraction.warnings,
        "chunks_indexed": chunks_created,
        "meeting_metadata": {
            "meeting_title": meeting_meta_dict.get("meeting_title"),
            "meeting_date": meeting_meta_dict.get("meeting_date"),
            "meeting_type": meeting_meta_dict.get("meeting_type"),
            "company_name": meeting_meta_dict.get("company_name"),
            "participants_count": len(meeting_meta_dict.get("participants", [])),
            "key_topics": meeting_meta_dict.get("key_topics", []),
            "extraction_confidence": meeting_meta_dict.get("extraction_confidence", "auto"),
        },
        "message": "Document uploaded, extracted, indexed, and meeting metadata extracted",
    }

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
        {"role": h.role, "message": h.message, "timestamp": h.timestamp, "metadata": h.response_metadata or {}}
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
    docs = db.query(Document).filter(Document.user_id == user.id).order_by(Document.upload_date.desc()).all()
    results = []
    for d in docs:
        meta = db.query(MeetingMetadata).filter(MeetingMetadata.document_id == d.id).first()
        entry = {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "upload_date": d.upload_date,
            "status": d.processing_status,
            "pages": d.page_count,
            "extractor": d.extraction_method,
            "warnings": (d.extraction_metadata or {}).get("warnings", []),
            "error": d.processing_error,
            "meeting_title": meta.meeting_title if meta else None,
            "meeting_date": meta.meeting_date.isoformat() if meta and meta.meeting_date else None,
            "meeting_type": meta.meeting_type if meta else None,
            "company_name": meta.company_name if meta else None,
            "key_topics": meta.key_topics if meta else [],
            "participants_count": len(meta.participants or []) if meta else 0,
            "extraction_confidence": meta.extraction_confidence if meta else None,
        }
        results.append(entry)
    return results


@router.get("/documents/{document_id}/metadata")
async def get_document_metadata(
    document_id: int,
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session),
):
    """Return the full meeting metadata for a single document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    meta = db.query(MeetingMetadata).filter(MeetingMetadata.document_id == document_id).first()
    if not meta:
        return {"document_id": document_id, "has_metadata": False}
    return {
        "document_id": document_id,
        "has_metadata": True,
        "meeting_title": meta.meeting_title,
        "meeting_date": meta.meeting_date.isoformat() if meta.meeting_date else None,
        "meeting_type": meta.meeting_type,
        "company_name": meta.company_name,
        "project_name": meta.project_name,
        "participants": meta.participants or [],
        "chairperson": meta.chairperson,
        "agenda_summary": meta.agenda_summary,
        "key_topics": meta.key_topics or [],
        "key_decisions": meta.key_decisions or [],
        "action_items_summary": meta.action_items_summary or [],
        "meeting_summary": meta.meeting_summary,
        "extraction_confidence": meta.extraction_confidence,
        "extracted_at": meta.extracted_at.isoformat() if meta.extracted_at else None,
        "user_edited": meta.user_edited.isoformat() if meta.user_edited else None,
    }


@router.put("/documents/{document_id}/metadata")
async def update_document_metadata(
    document_id: int,
    request: MetadataUpdateRequest,
    user: User = Depends(get_current_chatbot_user),
    db: Session = Depends(get_db_session),
):
    """Allow the user to correct or enhance auto-extracted meeting metadata."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    meta = db.query(MeetingMetadata).filter(MeetingMetadata.document_id == document_id).first()
    if not meta:
        # Create metadata row if it doesn't exist
        meta = MeetingMetadata(document_id=document_id, user_id=user.id)
        db.add(meta)

    update_data = request.model_dump(exclude_unset=True)
    if "meeting_date" in update_data and update_data["meeting_date"]:
        try:
            update_data["meeting_date"] = datetime.strptime(update_data["meeting_date"][:10], "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="meeting_date must be YYYY-MM-DD")

    for field, value in update_data.items():
        if hasattr(meta, field):
            setattr(meta, field, value)

    meta.extraction_confidence = "user_verified"
    meta.user_edited = datetime.utcnow()
    db.commit()
    return {"status": "updated", "document_id": document_id}
