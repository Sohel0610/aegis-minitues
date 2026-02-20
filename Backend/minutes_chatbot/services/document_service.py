"""
Document Service

Handles document upload, processing, and storage.
"""

import os
import shutil
from sqlalchemy.orm import Session
from minutes_chatbot.database.models import Document
from minutes_chatbot.utils.text_extraction import UniversalTextExtractor as TextExtractor
from minutes_chatbot.config import settings, logger
from typing import Optional
from datetime import datetime


class DocumentService:
    """Service for document management"""
    
    @staticmethod
    def save_uploaded_file(user_id: int, file, filename: str) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            user_id: User ID
            file: Uploaded file object
            filename: Original filename
        
        Returns:
            File path where file was saved
        """
        # Create user-specific directory
        user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    
    @staticmethod
    def create_document_record(
        db: Session,
        user_id: int,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        extracted_text: str
    ) -> Document:
        """
        Create document record in database.
        
        Args:
            db: Database session
            user_id: User ID
            filename: Original filename
            file_path: Path where file is saved
            file_type: File extension
            file_size: File size in bytes
            extracted_text: Extracted text from file
        
        Returns:
            Created Document object
        """
        document = Document(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            extracted_text=extracted_text
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Document record created: {filename} (ID: {document.id})")
        return document
    
    @staticmethod
    def upload_and_process_document(db: Session, user_id: int, file, filename: str) -> Document:
        """
        Complete document upload and processing workflow.
        
        Args:
            db: Database session
            user_id: User ID
            file: Uploaded file object
            filename: Original filename
        
        Returns:
            Created Document object
        """
        # Save file to disk
        file_path = DocumentService.save_uploaded_file(user_id, file, filename)
        
        # Get file info
        file_type = os.path.splitext(filename)[1].replace(".", "")
        file_size = os.path.getsize(file_path)
        
        # Extract text
        extractor = TextExtractor()
        extracted_text = extractor.extract_to_text(file_path, file_type=file_type)
        
        # Create database record
        document = DocumentService.create_document_record(
            db=db,
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            extracted_text=extracted_text
        )
        
        logger.info(f"Document uploaded and processed: {filename}")
        return document
    
    @staticmethod
    def get_user_documents(db: Session, user_id: int):
        """Get all documents for a user"""
        return db.query(Document).filter(Document.user_id == user_id).order_by(Document.upload_date.desc()).all()
    
    @staticmethod
    def get_document_by_id(db: Session, document_id: int) -> Optional[Document]:
        """Get document by ID"""
        return db.query(Document).filter(Document.id == document_id).first()
