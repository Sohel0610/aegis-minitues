# Directors Disclosure Route Module
# This module handles directors disclosure functionality including document processing and summary generation
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from docx import Document as DocxDocument
import sys
import re
import shutil
from pathlib import Path

# Add the parent directory to the path to import llm_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_utils import generate_and_save_summary

# Import our enhanced matching algorithm
from routes.EnhancedIndianNameMatcher import indian_name_similarity

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for directors disclosure endpoints
router = APIRouter()

# Response models for directors disclosure
class DirectorMasterResponse(BaseModel):
    id: int
    name: str
    din: str
    pan: Optional[str] = None
    created_at: str

class DirectorsMasterResponse(BaseModel):
    data: List[DirectorMasterResponse]
    count: int

class DisclosureResponse(BaseModel):
    id: int
    director_name: str
    din: str
    disclosure_date: str
    disclosure_type: str
    file_path: str

class DisclosuresResponse(BaseModel):
    data: List[DisclosureResponse]
    count: int

class DisclosureContentResponse(BaseModel):
    content: str

class DisclosureAnalyticsResponse(BaseModel):
    total_disclosures: int
    by_type: List[Dict[str, Any]]
    by_month: List[Dict[str, Any]]
    by_director: List[Dict[str, Any]]

class DirectorCreateRequest(BaseModel):
    name: str
    din: str

class DirectorUpdateRequest(BaseModel):
    name: str
    din: str

class DirectorPanUpdateRequest(BaseModel):
    pan: str

# Add Pydantic model for document summary
class DocumentSummaryResponse(BaseModel):
    id: int
    director_name: str
    din: str
    file_path: str
    full_text: str
    summary: str
    created_at: str
    updated_at: str

# Add Pydantic model for summary generation response
class SummaryGenerationResponse(BaseModel):
    success: bool
    message: str
    summary: Optional[str] = None

# Add Pydantic models for family information
class FamilyMemberInfo(BaseModel):
    relationship: str
    details: str
    pan_number: Optional[str] = None

class DirectorFamilyInfoResponse(BaseModel):
    director_name: str
    matched_family_name: str
    match_score: float
    section_2_77_i: Optional[str] = None
    section_2_77_ii: Optional[str] = None
    section_2_77_iii: Optional[str] = None
    family_members: List[FamilyMemberInfo]
    created_at: str = datetime.now().isoformat()

# Add Pydantic model for updating family information
class UpdateFamilyInfoRequest(BaseModel):
    section_2_77_i: Optional[str] = None
    section_2_77_ii: Optional[str] = None
    section_2_77_iii: Optional[str] = None
    family_members: List[FamilyMemberInfo]

# Add Pydantic model for director profile
class DirectorProfileResponse(BaseModel):
    name: str
    din: str
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    pan: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None

# Add Pydantic model for updating director profile (excluding name)
class DirectorProfileUpdateRequest(BaseModel):
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    pan: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None

# Add Pydantic models for image upload
class ImageUploadResponse(BaseModel):
    success: bool
    message: str
    image_url: Optional[str] = None

class ImageDeleteResponse(BaseModel):
    success: bool
    message: str

# Endpoint to get all directors from directors database
@router.get("/api/directors-master", response_model=DirectorsMasterResponse)
async def get_directors_master():
    """Get all directors from directors database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
        
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Directors database not found")
        
        def fetch_directors():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, din, created_at FROM directors ORDER BY name")
            rows = cursor.fetchall()
            
            # Get PAN information from directors_profile.db
            profile_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors_profile.db")
            pan_data = {}
            if os.path.exists(profile_db_path):
                profile_conn = sqlite3.connect(profile_db_path)
                profile_cursor = profile_conn.cursor()
                profile_cursor.execute("SELECT DIN, PAN FROM directors_profile WHERE PAN IS NOT NULL AND PAN != ''")
                pan_rows = profile_cursor.fetchall()
                profile_conn.close()
                
                # Create a dictionary mapping DIN to PAN
                for din, pan in pan_rows:
                    if din:
                        pan_data[din.strip()] = pan.strip() if pan else None
            
            conn.close()
            
            return [{
                'id': row[0],
                'name': row[1],
                'din': row[2],
                'pan': pan_data.get(row[2].strip()) if row[2] else None,
                'created_at': row[3]
            } for row in rows]
        
        loop = asyncio.get_event_loop()
        directors = await loop.run_in_executor(thread_pool, fetch_directors)
        
        return DirectorsMasterResponse(
            data=[DirectorMasterResponse(**d) for d in directors],
            count=len(directors)
        )
    except Exception as e:
        logger.error(f"Error fetching directors master: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch directors: {str(e)}")

# Endpoint to create a new director in directors database
@router.post("/api/directors-master", response_model=DirectorMasterResponse)
async def create_director(request: DirectorCreateRequest):
    """Create a new director in directors database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
        
        def insert_director():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if director with same DIN already exists
            cursor.execute("SELECT id FROM directors WHERE din = ?", (request.din,))
            if cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=400, detail="Director with this DIN already exists")
            
            # Insert new director
            cursor.execute(
                "INSERT INTO directors (name, din) VALUES (?, ?)",
                (request.name, request.din)
            )
            director_id = cursor.lastrowid
            
            # Fetch the created director
            cursor.execute("SELECT id, name, din, created_at FROM directors WHERE id = ?", (director_id,))
            row = cursor.fetchone()
            conn.commit()
            conn.close()
            
            return {
                'id': row[0],
                'name': row[1],
                'din': row[2],
                'created_at': row[3]
            }
        
        loop = asyncio.get_event_loop()
        director = await loop.run_in_executor(thread_pool, insert_director)
        
        return DirectorMasterResponse(**director)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating director: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create director: {str(e)}")

# Endpoint to update an existing director in directors database
@router.put("/api/directors-master/{director_id}", response_model=DirectorMasterResponse)
async def update_director(director_id: int, request: DirectorUpdateRequest):
    """Update an existing director in directors database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
        
        def update_director_data():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if director exists
            cursor.execute("SELECT id FROM directors WHERE id = ?", (director_id,))
            if not cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=404, detail="Director not found")
            
            # Check if another director has the same DIN
            cursor.execute("SELECT id FROM directors WHERE din = ? AND id != ?", (request.din, director_id))
            if cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=400, detail="Another director with this DIN already exists")
            
            # Update director
            cursor.execute(
                "UPDATE directors SET name = ?, din = ? WHERE id = ?",
                (request.name, request.din, director_id)
            )
            
            # Fetch updated director
            cursor.execute("SELECT id, name, din, created_at FROM directors WHERE id = ?", (director_id,))
            row = cursor.fetchone()
            conn.commit()
            conn.close()
            
            return {
                'id': row[0],
                'name': row[1],
                'din': row[2],
                'created_at': row[3]
            }
        
        loop = asyncio.get_event_loop()
        director = await loop.run_in_executor(thread_pool, update_director_data)
        
        return DirectorMasterResponse(**director)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating director: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update director: {str(e)}")

# Endpoint to update PAN for a director (stored in directors_profile.db, keyed by DIN)
@router.put("/api/directors-master/{director_id}/pan")
async def update_director_pan(director_id: int, request: DirectorPanUpdateRequest):
    """Update PAN for a director using DIN mapping in directors_profile.db"""
    try:
        directors_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
        profile_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors_profile.db")

        def upsert_pan():
            # Ensure directors_profile.db exists; create table if missing
            conn = sqlite3.connect(profile_db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS directors_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    DIN TEXT UNIQUE,
                    PAN TEXT
                )
                """
            )

            # Get DIN for the given director_id from directors.db
            dconn = sqlite3.connect(directors_db_path)
            dcur = dconn.cursor()
            dcur.execute("SELECT din FROM directors WHERE id = ?", (director_id,))
            row = dcur.fetchone()
            dconn.close()
            if not row:
                conn.close()
                raise HTTPException(status_code=404, detail="Director not found")
            din = (row[0] or "").strip()
            if not din:
                conn.close()
                raise HTTPException(status_code=400, detail="Director DIN is empty; cannot set PAN")

            # Upsert PAN by DIN
            cursor.execute("SELECT DIN FROM directors_profile WHERE DIN = ?", (din,))
            exists = cursor.fetchone() is not None
            if exists:
                cursor.execute("UPDATE directors_profile SET PAN = ? WHERE DIN = ?", (request.pan.strip(), din))
            else:
                cursor.execute("INSERT INTO directors_profile (DIN, PAN) VALUES (?, ?)", (din, request.pan.strip()))

            conn.commit()
            conn.close()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, upsert_pan)
        return {"message": "PAN updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating director PAN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update director PAN: {str(e)}")

# Endpoint to delete a director from directors database
@router.delete("/api/directors-master/{director_id}")
async def delete_director(director_id: int):
    """Delete a director from directors database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
        
        def delete_director_data():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if director exists
            cursor.execute("SELECT id FROM directors WHERE id = ?", (director_id,))
            if not cursor.fetchone():
                conn.close()
                raise HTTPException(status_code=404, detail="Director not found")
            
            # Delete director
            cursor.execute("DELETE FROM directors WHERE id = ?", (director_id,))
            conn.commit()
            conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, delete_director_data)
        
        return {"message": "Director deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting director: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete director: {str(e)}")

# Endpoint to get all directors' disclosures from Word files
@router.get("/api/directors-disclosures", response_model=DisclosuresResponse)
async def get_directors_disclosures():
    """Get all directors' disclosures from Word files"""
    try:
        # Path to disclosure output folder
        disclosures_dir = os.path.join(os.path.dirname(__file__), "..", "public", "Directors Discloser Output")
        
        def fetch_disclosures():
            disclosures = []
            
            # Check if directory exists
            if not os.path.exists(disclosures_dir):
                logger.warning(f"Disclosures directory not found: {disclosures_dir}")
                return []
            
            # Scan directory for .docx files
            for idx, filename in enumerate(sorted(os.listdir(disclosures_dir))):
                if filename.endswith('.docx') and not filename.startswith('~$'):
                    file_path = os.path.join(disclosures_dir, filename)
                    
                    # Extract metadata from filename or file stats
                    file_stat = os.stat(file_path)
                    created_date = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d')
                    
                    # Extract director name from filename (remove _MBP.docx)
                    director_name = filename.replace('_MBP.docx', '').replace('.docx', '').strip()
                    din = 'N/A'  # Default value
                    
                    # Try to extract DIN from document
                    try:
                        doc = DocxDocument(file_path)
                        # Look for DIN in document paragraphs
                        for para in doc.paragraphs:
                            text = para.text.strip()
                            # Match pattern like "DIN : 12345678" or "DIN: 12345678"
                            din_match = re.search(r'DIN\s*:\s*([0-9]{8})', text, re.IGNORECASE)
                            if din_match:
                                din = din_match.group(1)
                                break
                    except Exception as e:
                        logger.warning(f"Error reading DIN from {filename}: {e}")
                    
                    disclosures.append({
                        'id': idx + 1,
                        'director_name': director_name,
                        'din': din,
                        'disclosure_date': created_date,
                        'disclosure_type': 'MBP-1',
                        'file_path': filename
                    })
            
            return disclosures
        
        loop = asyncio.get_event_loop()
        disclosures = await loop.run_in_executor(thread_pool, fetch_disclosures)
        
        return DisclosuresResponse(
            data=[DisclosureResponse(**d) for d in disclosures],
            count=len(disclosures)
        )
    except Exception as e:
        logger.error(f"Error fetching disclosures: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch disclosures: {str(e)}")

# Endpoint to get content of a specific disclosure document
@router.get("/api/directors-disclosures/{disclosure_id}/content", response_model=DisclosureContentResponse)
async def get_disclosure_content(disclosure_id: int):
    """Get content of a specific disclosure document"""
    try:
        disclosures_dir = os.path.join(os.path.dirname(__file__), "..", "public", "Directors Discloser Output")
        
        def read_disclosure_content():
            if not os.path.exists(disclosures_dir):
                raise HTTPException(status_code=404, detail="Disclosures directory not found")
            
            # Get list of docx files
            docx_files = [f for f in os.listdir(disclosures_dir) 
                         if f.endswith('.docx') and not f.startswith('~$')]
            
            # Check if disclosure_id is valid
            if disclosure_id < 1 or disclosure_id > len(docx_files):
                raise HTTPException(status_code=404, detail="Disclosure not found")
            
            # Get the file at the specified index
            filename = sorted(docx_files)[disclosure_id - 1]
            file_path = os.path.join(disclosures_dir, filename)
            
            # Read Word document content
            try:
                doc = DocxDocument(file_path)
                
                # Extract all text from document
                content_parts = []
                
                # Add document title if available
                content_parts.append(f"Document: {filename}\n")
                content_parts.append("=" * 80 + "\n\n")
                
                # Extract all paragraphs
                for para in doc.paragraphs:
                    if para.text.strip():
                        content_parts.append(para.text + "\n")
                
                # Extract tables if any
                if doc.tables:
                    content_parts.append("\n" + "=" * 80 + "\n")
                    content_parts.append("TABLES\n")
                    content_parts.append("=" * 80 + "\n\n")
                    
                    for idx, table in enumerate(doc.tables):
                        content_parts.append(f"Table {idx + 1}:\n")
                        for row in table.rows:
                            row_text = " | ".join([cell.text.strip() for cell in row.cells])
                            content_parts.append(row_text + "\n")
                        content_parts.append("\n")
                
                full_content = "".join(content_parts)
                
                if not full_content.strip():
                    return "No content found in document"
                
                return full_content
                
            except Exception as e:
                logger.error(f"Error reading Word document: {e}")
                raise HTTPException(status_code=500, detail=f"Error reading document: {str(e)}")
        
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(thread_pool, read_disclosure_content)
        
        return DisclosureContentResponse(content=content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching disclosure content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch content: {str(e)}")

# Endpoint to download a specific disclosure document
@router.get("/api/directors-disclosures/{disclosure_id}/download")
async def download_disclosure(disclosure_id: int):
    """Download a specific disclosure document"""
    try:
        disclosures_dir = os.path.join(os.path.dirname(__file__), "..", "public", "Directors Discloser Output")
        
        def get_file_path():
            if not os.path.exists(disclosures_dir):
                raise HTTPException(status_code=404, detail="Disclosures directory not found")
            
            # Get list of docx files
            docx_files = [f for f in os.listdir(disclosures_dir) 
                         if f.endswith('.docx') and not f.startswith('~$')]
            
            # Check if disclosure_id is valid
            if disclosure_id < 1 or disclosure_id > len(docx_files):
                raise HTTPException(status_code=404, detail="Disclosure not found")
            
            # Get the file at the specified index
            filename = sorted(docx_files)[disclosure_id - 1]
            file_path = os.path.join(disclosures_dir, filename)
            
            return file_path, filename
        
        loop = asyncio.get_event_loop()
        file_path, filename = await loop.run_in_executor(thread_pool, get_file_path)
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading disclosure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

# Endpoint to get analytics data for directors' disclosures
@router.get("/api/directors-disclosures/analytics", response_model=DisclosureAnalyticsResponse)
async def get_disclosures_analytics():
    """Get analytics data for directors' disclosures"""
    try:
        disclosures_dir = os.path.join(os.path.dirname(__file__), "..", "public", "Directors Discloser Output")
        
        def calculate_analytics():
            from collections import defaultdict
            
            if not os.path.exists(disclosures_dir):
                # Return empty analytics if directory doesn't exist
                return {
                    'total_disclosures': 0,
                    'by_type': [],
                    'by_month': [],
                    'by_director': []
                }
            
            docx_files = [f for f in os.listdir(disclosures_dir) 
                         if f.endswith('.docx') and not f.startswith('~$')]
            
            total_count = len(docx_files)
            
            # Track statistics
            by_type = defaultdict(int)
            by_month = defaultdict(int)
            by_director = defaultdict(int)
            
            for filename in docx_files:
                file_path = os.path.join(disclosures_dir, filename)
                
                # Get file modification date for monthly stats
                file_stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                month_key = file_date.strftime('%b %Y')
                by_month[month_key] += 1
                
                # Extract director name from filename (remove _MBP.docx)
                director_name = filename.replace('_MBP.docx', '').replace('.docx', '').strip()
                
                # Try to read document for better classification
                try:
                    doc = DocxDocument(file_path)
                    
                    # Look for disclosure type in content
                    for para in doc.paragraphs[:15]:
                        text = para.text.lower()
                        
                        # Classify disclosure type
                        if 'shareholding' in text or 'shares' in text:
                            by_type['Shareholding'] += 1
                            break
                        elif 'transaction' in text or 'acquisition' in text:
                            by_type['Transaction'] += 1
                            break
                        elif 'interest' in text or 'concern' in text:
                            by_type['Interest'] += 1
                            break
                    else:
                        # Default type - MBP-1 form
                        by_type['MBP-1'] += 1
                    
                except Exception as e:
                    logger.warning(f"Error analyzing {filename}: {e}")
                    by_type['MBP-1'] += 1
                
                # Track by director
                by_director[director_name] += 1
            
            # Convert to list format for response
            analytics = {
                'total_disclosures': total_count,
                'by_type': [{'type': k, 'count': v} for k, v in sorted(by_type.items(), key=lambda x: -x[1])],
                'by_month': [{'month': k, 'count': v} for k, v in sorted(by_month.items())],
                'by_director': [{'director': k, 'count': v} for k, v in sorted(by_director.items(), key=lambda x: -x[1])[:10]]  # Top 10
            }
            
            return analytics
        
        loop = asyncio.get_event_loop()
        analytics = await loop.run_in_executor(thread_pool, calculate_analytics)
        
        return DisclosureAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

# Endpoint to generate summary for a specific disclosure document
@router.post("/api/directors-disclosures/{disclosure_id}/generate-summary", response_model=SummaryGenerationResponse)
async def generate_disclosure_summary(disclosure_id: int):
    """Generate summary for a specific disclosure document"""
    try:
        disclosures_dir = os.path.join(os.path.dirname(__file__), "..", "public", "Directors Discloser Output")
        
        def generate_summary():
            if not os.path.exists(disclosures_dir):
                raise HTTPException(status_code=404, detail="Disclosures directory not found")
            
            # Get list of docx files
            docx_files = [f for f in os.listdir(disclosures_dir) 
                         if f.endswith('.docx') and not f.startswith('~$')]
            
            # Check if disclosure_id is valid
            if disclosure_id < 1 or disclosure_id > len(docx_files):
                raise HTTPException(status_code=404, detail="Disclosure not found")
            
            # Get the file at the specified index
            filename = sorted(docx_files)[disclosure_id - 1]
            
            # Extract director name from filename
            director_name = filename.replace('_MBP.docx', '').replace('.docx', '').strip()
            din = 'N/A'  # Default value
            
            # Generate and save summary
            summary = generate_and_save_summary(director_name, din, filename)
            
            return {
                'success': True,
                'message': 'Summary generated successfully',
                'summary': summary
            }
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(thread_pool, generate_summary)
        
        return SummaryGenerationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating disclosure summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

# Endpoint to get summary of a specific disclosure document
@router.get("/api/directors-disclosures/{disclosure_id}/summary", response_model=DocumentSummaryResponse)
async def get_disclosure_summary(disclosure_id: int):
    """Get summary of a specific disclosure document"""
    try:
        disclosures_dir = os.path.join(os.path.dirname(__file__), "..", "public", "Directors Discloser Output")
        
        def get_summary_data():
            if not os.path.exists(disclosures_dir):
                raise HTTPException(status_code=404, detail="Disclosures directory not found")
            
            # Get list of docx files
            docx_files = [f for f in os.listdir(disclosures_dir) 
                         if f.endswith('.docx') and not f.startswith('~$')]
            
            # Check if disclosure_id is valid
            if disclosure_id < 1 or disclosure_id > len(docx_files):
                raise HTTPException(status_code=404, detail="Disclosure not found")
            
            # Get the file at the specified index
            filename = sorted(docx_files)[disclosure_id - 1]
            
            # Connect to database to get summary
            db_path = os.path.join(os.path.dirname(__file__), "..", 'directors_data.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try to get existing record
            cursor.execute('''
                SELECT id, director_name, din, file_path, full_text, summary, created_at, updated_at 
                FROM document_summaries WHERE file_path = ?
            ''', (filename,))
            
            result = cursor.fetchone()
            conn.close()
            
            # If record exists with full text and summary, return it
            if result and result[4] and result[5]:  # Check if full_text and summary are not null/empty
                return {
                    'id': result[0],
                    'director_name': result[1],
                    'din': result[2],
                    'file_path': result[3],
                    'full_text': result[4],
                    'summary': result[5],
                    'created_at': result[6],
                    'updated_at': result[7]
                }
            
            # If no record exists or it's incomplete, generate it automatically
            file_path = os.path.join(disclosures_dir, filename)
            
            # Extract director name from filename
            director_name = filename.replace('_MBP.docx', '').replace('.docx', '').strip()
            din = 'N/A'  # Default value
            
            # Try to generate full text and summary
            try:
                # Generate and save full text and summary
                full_text, summary = generate_and_save_summary(director_name, din, filename)
                
                # Return the newly generated data
                file_stat = os.stat(file_path)
                return {
                    'id': 0,  # Will be updated when saved to DB
                    'director_name': director_name,
                    'din': din,
                    'file_path': filename,
                    'full_text': full_text,
                    'summary': summary,
                    'created_at': file_stat.st_mtime,
                    'updated_at': file_stat.st_mtime
                }
            except Exception as e:
                logger.error(f"Error generating full text and summary: {str(e)}")
                # Return a default response if generation fails
                file_stat = os.stat(file_path)
                error_msg = 'Error processing document'
                return {
                    'id': 0,
                    'director_name': director_name,
                    'din': din,
                    'file_path': filename,
                    'full_text': error_msg,
                    'summary': error_msg,
                    'created_at': file_stat.st_mtime,
                    'updated_at': file_stat.st_mtime
                }
        
        loop = asyncio.get_event_loop()
        summary_data = await loop.run_in_executor(thread_pool, get_summary_data)
        
        return DocumentSummaryResponse(**summary_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching disclosure summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

# Endpoint to get family information for a specific director
@router.get("/api/directors/{director_name}/family-info", response_model=DirectorFamilyInfoResponse)
async def get_director_family_info(director_name: str):
    """Get family information for a specific director using enhanced Indian name matching"""
    try:
        directors_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
        family_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "Director_Family_Information.db")
        
        def fetch_family_info():
            if not os.path.exists(directors_db_path) or not os.path.exists(family_db_path):
                raise HTTPException(status_code=404, detail="Required databases not found")
            
            # Connect to family database
            family_conn = sqlite3.connect(family_db_path)
            family_cursor = family_conn.cursor()
            
            try:
                # Get all family members
                family_cursor.execute("SELECT Name FROM Sheet1 ORDER BY Name")
                family_rows = family_cursor.fetchall()
                family_list = [row[0] for row in family_rows]
                
                # Find the best match for the director
                best_match = None
                best_score = 0
                
                for family_member in family_list:
                    score = indian_name_similarity(director_name, family_member)
                    if score > best_score and score >= 0.5:  # Minimum threshold
                        best_score = score
                        best_match = family_member
                
                # If we found a match, get the detailed family information
                if best_match:
                    family_cursor.execute("""
                        SELECT Name, "Section_2(77)(i)", "Section_2(77)(ii)", "Section_2(77)(iii)", 
                               Father, Mother, Son, "Son's_Wife", Daughter, "Daughter's_husband", Brother, Sister,
                               Father_PAN, Mother_PAN, Father_PAN_File, Mother_PAN_File
                        FROM Sheet1 
                        WHERE Name = ?
                    """, (best_match,))
                    
                    family_data = family_cursor.fetchone()
                    
                    if family_data:
                        # Create family members list
                        family_members = []
                        
                        # Add section information
                        section_2_77_i = family_data[1] if family_data[1] else None
                        section_2_77_ii = family_data[2] if family_data[2] else None
                        section_2_77_iii = str(family_data[3]) if family_data[3] is not None else None
                        
                        # Add family members
                        relationships = [
                            ("Father", family_data[4], family_data[12], family_data[14]),
                            ("Mother", family_data[5], family_data[13], family_data[15]),
                            ("Son", family_data[6], None, None),
                            ("Son's Wife", family_data[7], None, None),
                            ("Daughter", family_data[8], None, None),
                            ("Daughter's Husband", family_data[9], None, None),
                            ("Brother", family_data[10], None, None),
                            ("Sister", family_data[11], None, None)
                        ]
                        
                        for relationship, details, pan_no, _ in relationships:
                            if (details and str(details).strip().lower() not in ['n/a', 'none', '', 'nil']) or pan_no:
                                family_members.append({
                                    "relationship": relationship,
                                    "details": str(details) if details else "",
                                    "pan_number": pan_no
                                })
                        
                        return {
                            "director_name": director_name,
                            "matched_family_name": best_match,
                            "match_score": round(best_score, 2),
                            "section_2_77_i": section_2_77_i,
                            "section_2_77_ii": section_2_77_ii,
                            "section_2_77_iii": section_2_77_iii,
                            "family_members": family_members
                        }
                
                # No match found
                return None
                
            finally:
                family_conn.close()
        
        loop = asyncio.get_event_loop()
        family_info = await loop.run_in_executor(thread_pool, fetch_family_info)
        
        if not family_info:
            raise HTTPException(status_code=404, detail="No family information found for this director")
        
        return DirectorFamilyInfoResponse(**family_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family info for director {director_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch family info: {str(e)}")

# Endpoint to update family information for a specific director
@router.put("/api/directors/{director_name}/family-info", response_model=DirectorFamilyInfoResponse)
async def update_director_family_info(director_name: str, request: UpdateFamilyInfoRequest):
    """Update family information for a specific director"""
    try:
        family_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "Director_Family_Information.db")
        
        def update_family_info():
            if not os.path.exists(family_db_path):
                raise HTTPException(status_code=404, detail="Family database not found")
            
            # Connect to family database
            family_conn = sqlite3.connect(family_db_path)
            family_cursor = family_conn.cursor()
            
            try:
                # Check if director exists in family database
                family_cursor.execute("SELECT Name FROM Sheet1 WHERE Name = ?", (director_name,))
                existing_record = family_cursor.fetchone()
                
                if not existing_record:
                    # Insert new record if it doesn't exist
                    family_cursor.execute("""
                        INSERT INTO Sheet1 (Name, "Section_2(77)(i)", "Section_2(77)(ii)", "Section_2(77)(iii)", 
                                           Father, Mother, Son, "Son's_Wife", Daughter, "Daughter's_husband", Brother, Sister)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        director_name,
                        request.section_2_77_i,
                        request.section_2_77_ii,
                        request.section_2_77_iii,
                        None,  # Father
                        None,  # Mother
                        None,  # Son
                        None,  # Son's Wife
                        None,  # Daughter
                        None,  # Daughter's Husband
                        None,  # Brother
                        None   # Sister
                    ))
                
                # Update the record with new information
                family_cursor.execute("""
                    UPDATE Sheet1 SET 
                        "Section_2(77)(i)" = ?,
                        "Section_2(77)(ii)" = ?,
                        "Section_2(77)(iii)" = ?
                    WHERE Name = ?
                """, (
                    request.section_2_77_i,
                    request.section_2_77_ii,
                    request.section_2_77_iii,
                    director_name
                ))
                
                # Update family members
                for member in request.family_members:
                    relationship = member.relationship
                    details = member.details
                    
                    # Map relationship to column name
                    column_map = {
                        "Father": "Father",
                        "Mother": "Mother",
                        "Son": "Son",
                        "Son's Wife": "Son's_Wife",
                        "Daughter": "Daughter",
                        "Daughter's Husband": "Daughter's_husband",
                        "Brother": "Brother",
                        "Sister": "Sister"
                    }
                    
                    if relationship in column_map:
                        column_name = column_map[relationship]
                        
                        # Update details
                        family_cursor.execute(f"""
                            UPDATE Sheet1 SET "{column_name}" = ? WHERE Name = ?
                        """, (details, director_name))
                        
                        # Update PAN number if provided
                        if member.pan_number is not None:
                            pan_col = f"{column_name}_PAN"
                            # Check if column exists (it should after migration)
                            try:
                                family_cursor.execute(f"""
                                    UPDATE Sheet1 SET "{pan_col}" = ? WHERE Name = ?
                                """, (member.pan_number, director_name))
                            except sqlite3.OperationalError:
                                pass # Column might not exist for non- Father/Mother
                
                family_conn.commit()
                
                # Return updated information
                family_cursor.execute("""
                    SELECT Name, "Section_2(77)(i)", "Section_2(77)(ii)", "Section_2(77)(iii)", 
                           Father, Mother, Son, "Son's_Wife", Daughter, "Daughter's_husband", Brother, Sister,
                           Father_PAN, Mother_PAN, Father_PAN_File, Mother_PAN_File
                    FROM Sheet1 
                    WHERE Name = ?
                """, (director_name,))
                
                family_data = family_cursor.fetchone()
                
                if family_data:
                    # Create family members list
                    family_members = []
                    
                    # Add section information
                    section_2_77_i = family_data[1] if family_data[1] else None
                    section_2_77_ii = family_data[2] if family_data[2] else None
                    section_2_77_iii = str(family_data[3]) if family_data[3] is not None else None
                    
                    # Add family members
                    relationships = [
                        ("Father", family_data[4], family_data[12], family_data[14]),
                        ("Mother", family_data[5], family_data[13], family_data[15]),
                        ("Son", family_data[6], None, None),
                        ("Son's Wife", family_data[7], None, None),
                        ("Daughter", family_data[8], None, None),
                        ("Daughter's Husband", family_data[9], None, None),
                        ("Brother", family_data[10], None, None),
                        ("Sister", family_data[11], None, None)
                    ]
                    
                    for relationship, details, pan_no, _ in relationships:
                        if (details and str(details).strip().lower() not in ['n/a', 'none', '', 'nil']) or pan_no:
                            family_members.append({
                                "relationship": relationship,
                                "details": str(details) if details else "",
                                "pan_number": pan_no
                            })
                    
                    return {
                        "director_name": director_name,
                        "matched_family_name": director_name,
                        "match_score": 1.0,  # Exact match since we're updating the director's own record
                        "section_2_77_i": section_2_77_i,
                        "section_2_77_ii": section_2_77_ii,
                        "section_2_77_iii": section_2_77_iii,
                        "family_members": family_members
                    }
                
                return None
                
            finally:
                family_conn.close()
        
        loop = asyncio.get_event_loop()
        updated_info = await loop.run_in_executor(thread_pool, update_family_info)
        
        if not updated_info:
            raise HTTPException(status_code=404, detail="Failed to update family information")
        
        return DirectorFamilyInfoResponse(**updated_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating family info for director {director_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update family info: {str(e)}")


# Endpoint to get director profile information
@router.get("/api/directors-profile/{din}", response_model=DirectorProfileResponse)
async def get_director_profile(din: str):
    """Get director profile information from directors_profile.db"""
    try:
        profile_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors_profile.db")
        
        def fetch_profile():
            if not os.path.exists(profile_db_path):
                raise HTTPException(status_code=404, detail="Directors profile database not found")
            
            conn = sqlite3.connect(profile_db_path)
            cursor = conn.cursor()
            
            # Fetch director profile data (excluding Unnamed:_8 column)
            cursor.execute("""
                SELECT Name_of_Director, DIN, Address, Date_of_Birth, PAN, Qualification, 
                       Nature_of_Experience_in_specific_Functional_Areas
                FROM directors_profile 
                WHERE DIN = ?
            """, (din,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                raise HTTPException(status_code=404, detail="Director profile not found")
            
            return {
                'name': row[0] if row[0] else '',
                'din': row[1] if row[1] else '',
                'address': row[2] if row[2] else None,
                'date_of_birth': row[3].split(' ')[0] if row[3] else None,  # Remove time part
                'pan': row[4] if row[4] else None,
                'qualification': row[5] if row[5] else None,
                'experience': row[6] if row[6] else None
            }
        
        loop = asyncio.get_event_loop()
        profile = await loop.run_in_executor(thread_pool, fetch_profile)
        
        return DirectorProfileResponse(**profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching director profile for DIN {din}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch director profile: {str(e)}")

# Endpoint to update director profile information
@router.put("/api/directors-profile/{din}", response_model=DirectorProfileResponse)
async def update_director_profile(din: str, request: DirectorProfileUpdateRequest):
    """Update director profile information in directors_profile.db"""
    try:
        profile_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors_profile.db")
        
        def update_profile():
            if not os.path.exists(profile_db_path):
                raise HTTPException(status_code=404, detail="Directors profile database not found")
            
            conn = sqlite3.connect(profile_db_path)
            cursor = conn.cursor()
            
            # Build dynamic update query based on provided fields
            update_fields = []
            values = []
            
            if request.address is not None:
                update_fields.append("Address = ?")
                values.append(request.address)
            
            if request.date_of_birth is not None:
                update_fields.append("Date_of_Birth = ?")
                values.append(request.date_of_birth)
            
            if request.pan is not None:
                update_fields.append("PAN = ?")
                values.append(request.pan)
            
            if request.qualification is not None:
                update_fields.append("Qualification = ?")
                values.append(request.qualification)
            
            if request.experience is not None:
                update_fields.append("Nature_of_Experience_in_specific_Functional_Areas = ?")
                values.append(request.experience)
            
            # Only proceed if there are fields to update
            if not update_fields:
                conn.close()
                raise HTTPException(status_code=400, detail="No fields to update")
            
            # Add DIN to values for WHERE clause
            values.append(din)
            
            # Update the record
            query = f"UPDATE directors_profile SET {', '.join(update_fields)} WHERE DIN = ?"
            cursor.execute(query, values)
            
            # Check if any row was updated
            if cursor.rowcount == 0:
                conn.close()
                raise HTTPException(status_code=404, detail="Director profile not found")
            
            conn.commit()
            
            # Fetch updated profile data
            cursor.execute("""
                SELECT Name_of_Director, DIN, Address, Date_of_Birth, PAN, Qualification, 
                       Nature_of_Experience_in_specific_Functional_Areas
                FROM directors_profile 
                WHERE DIN = ?
            """, (din,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                raise HTTPException(status_code=404, detail="Director profile not found after update")
            
            return {
                'name': row[0] if row[0] else '',
                'din': row[1] if row[1] else '',
                'address': row[2] if row[2] else None,
                'date_of_birth': row[3].split(' ')[0] if row[3] else None,  # Remove time part
                'pan': row[4] if row[4] else None,
                'qualification': row[5] if row[5] else None,
                'experience': row[6] if row[6] else None
            }
        
        loop = asyncio.get_event_loop()
        updated_profile = await loop.run_in_executor(thread_pool, update_profile)
        
        return DirectorProfileResponse(**updated_profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating director profile for DIN {din}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update director profile: {str(e)}")

# Endpoint to upload director profile image
@router.post("/api/directors-profile/{din}/image", response_model=ImageUploadResponse)
async def upload_director_image(din: str, file: UploadFile = File(...)):
    """Upload director profile image and save to server"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (5MB limit)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")
        
        # Reset file pointer
        await file.seek(0)
        
        # Create director_images directory if it doesn't exist
        images_dir = os.path.join(os.path.dirname(__file__), "..", "director_images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Save image with DIN as filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        image_filename = f"{din}{file_extension}"
        image_path = os.path.join(images_dir, image_filename)
        
        # Save file
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return success response with image URL
        image_url = f"/api/directors-profile/{din}/image"
        return ImageUploadResponse(
            success=True,
            message="Image uploaded successfully",
            image_url=image_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image for DIN {din}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

# Endpoint to get director profile image
@router.get("/api/directors-profile/{din}/image")
async def get_director_image(din: str):
    """Serve director profile image"""
    try:
        # Look for image file with the DIN
        images_dir = os.path.join(os.path.dirname(__file__), "..", "director_images")
        
        # Check for various image extensions
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        image_path = None
        
        for ext in extensions:
            potential_path = os.path.join(images_dir, f"{din}{ext}")
            if os.path.exists(potential_path):
                image_path = potential_path
                break
        
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(image_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image for DIN {din}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to serve image: {str(e)}")

# Endpoint to delete director profile image
@router.delete("/api/directors-profile/{din}/image", response_model=ImageDeleteResponse)
async def delete_director_image(din: str):
    """Delete director profile image"""
    try:
        # Look for image file with the DIN
        images_dir = os.path.join(os.path.dirname(__file__), "..", "director_images")
        
        # Check for various image extensions
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        image_path = None
        
        for ext in extensions:
            potential_path = os.path.join(images_dir, f"{din}{ext}")
            if os.path.exists(potential_path):
                image_path = potential_path
                break
        
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete the image file
        os.remove(image_path)
        
        return ImageDeleteResponse(
            success=True,
            message="Image deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image for DIN {din}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

# Endpoint to get all directors from directors database for Minutes Preparation
@router.get("/directors", response_model=DirectorsMasterResponse)
async def get_directors_for_minutes():
    """Get all directors from directors database for Minutes Preparation"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
        
        if not os.path.exists(db_path):
            logger.warning(f"Directors database not found: {db_path}")
            return DirectorsMasterResponse(data=[], count=0)
        
        def fetch_directors():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, din, created_at FROM directors ORDER BY name")
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'id': row[0],
                'name': row[1],
                'din': row[2],
                'created_at': row[3]
            } for row in rows]
        
        loop = asyncio.get_event_loop()
        directors = await loop.run_in_executor(thread_pool, fetch_directors)
        
        return DirectorsMasterResponse(
            data=[DirectorMasterResponse(**d) for d in directors],
            count=len(directors)
        )
    except Exception as e:
        logger.error(f"Error fetching directors for minutes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch directors: {str(e)}")
