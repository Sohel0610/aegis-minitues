"""
Document API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from minutes_chatbot.database.connection import get_db_session
from minutes_chatbot.services.document_service import DocumentService
from minutes_chatbot.services.embedding_service import EmbeddingService
from minutes_chatbot.config.settings import settings
from minutes_chatbot.config.logging_config import logger
from minutes_chatbot.middleware import get_current_user
from minutes_chatbot.database.models import User

router = APIRouter(prefix="/api/documents", tags=["Documents"])


class DocumentResponse(BaseModel):
    """Document response model"""
    id: int
    filename: str
    file_type: str
    file_size: int
    uploaded_at: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Upload a document.
    
    Requires SSO authentication via Bearer token.
    Supports: PDF, Word, Excel, PowerPoint, Text files
    """
    try:
        # User is automatically extracted from SSO token
        logger.info(f"User {user.email} uploading document: {file.filename}")
        
        # Validate file type
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.allowed_extensions_list:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Upload and process document
        document = DocumentService.upload_and_process_document(
            db=db,
            user_id=user.id,
            file=file,
            filename=file.filename
        )
        
        # Generate embeddings
        embedding_service = EmbeddingService()
        embedding_service.create_document_embeddings(db=db, document=document)
        
        logger.info(f"Document uploaded successfully: {file.filename}")
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            uploaded_at=str(document.uploaded_at)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        db.close()


@router.get("/list")
async def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get list of user's uploaded documents.
    
    Requires SSO authentication via Bearer token.
    """
    try:
        # User is automatically extracted from SSO token
        logger.info(f"Listing documents for user {user.email}")
        
        # Get documents
        documents = DocumentService.get_user_documents(db=db, user_id=user.id)
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "uploaded_at": str(doc.uploaded_at)
                }
                for doc in documents
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
