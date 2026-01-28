# Minutes Generation Route Module
# This module handles minutes preparation functionality including place management and document generation
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from docx import Document

# Add the parent directory to the path to import utils
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_init import init_places_db

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for minutes endpoints
router = APIRouter()

# Response model for place information
class PlaceResponse(BaseModel):
    id: int
    name: str
    address: str
    is_default: bool
    created_at: str

# Response model for places list
class PlacesListResponse(BaseModel):
    data: List[PlaceResponse]
    count: int

# Request model for creating a place
class PlaceCreateRequest(BaseModel):
    name: str
    address: str
    is_default: bool = False

# Request model for minutes generation
class MinutesGenerationRequest(BaseModel):
    template: str
    companyName: str
    meetingNumber: str
    meetingType: str
    meetingDay: str
    meetingDate: str
    meetingStartTime: str
    meetingEndTime: str
    meetingPlace: str
    chairmanName: str
    presentDirectors: List[Dict[str, str]]
    inAttendance: List[Dict[str, str]]
    companySecretary: str
    previousMeetingDate: str
    authorisedOfficer: str
    quorum: str
    concerns: str
    declarations: str
    auditorPaymentAmount: str
    auditorPaymentWords: str
    financialYear: str
    agmNumber: str
    agmDay: str
    agmMonthName: str
    agmDate: str
    agmTime: str
    agmPlace: str
    recordingDate: str
    signingDate: str
    signingPlace: str

# Initialize places database on startup
init_places_db()

# Endpoint to get all places from database
@router.get("/places", response_model=PlacesListResponse)
async def get_places():
    """Get all places from database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "places.db")
        
        def fetch_places():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, address, is_default, created_at FROM places ORDER BY is_default DESC, name")
            rows = cursor.fetchall()
            conn.close()
            
            places = [
                PlaceResponse(
                    id=row[0],
                    name=row[1],
                    address=row[2],
                    is_default=bool(row[3]),
                    created_at=row[4]
                )
                for row in rows
            ]
            return places
        
        loop = asyncio.get_event_loop()
        places = await loop.run_in_executor(thread_pool, fetch_places)
        
        return PlacesListResponse(
            data=places,
            count=len(places)
        )
    except Exception as e:
        logger.error(f"Error fetching places: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch places: {str(e)}")

# Endpoint to create a new place
@router.post("/places", response_model=PlaceResponse)
async def create_place(request: PlaceCreateRequest):
    """Create a new place"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "places.db")
        
        def insert_place():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # If this is set as default, unset other defaults
            if request.is_default:
                cursor.execute("UPDATE places SET is_default = 0")
            
            cursor.execute('''
                INSERT INTO places (name, address, is_default)
                VALUES (?, ?, ?)
            ''', (request.name, request.address, request.is_default))
            
            place_id = cursor.lastrowid
            conn.commit()
            
            # Fetch the created place
            cursor.execute("SELECT id, name, address, is_default, created_at FROM places WHERE id = ?", (place_id,))
            row = cursor.fetchone()
            conn.close()
            
            return PlaceResponse(
                id=row[0],
                name=row[1],
                address=row[2],
                is_default=bool(row[3]),
                created_at=row[4]
            )
        
        loop = asyncio.get_event_loop()
        new_place = await loop.run_in_executor(thread_pool, insert_place)
        
        return new_place
    except Exception as e:
        logger.error(f"Error creating place: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create place: {str(e)}")

# Endpoint to generate meeting minutes document from template
@router.post("/generate-minutes")
async def generate_minutes(request: MinutesGenerationRequest):
    """Generate meeting minutes document from template"""
    try:
        logger.info(f"Generating minutes for template: {request.template}")
        
        # Define template path
        template_path = os.path.join(os.path.dirname(__file__), "..", "public", "templates", f"{request.template.lower()}_meeting_template.docx")
        
        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail=f"Template {request.template} not found")
        
        def generate_document():
            # Load the template
            doc = Document(template_path)
            
            # Get non-chairman directors for signature tables
            non_chairman_directors = [d for d in request.presentDirectors if d.get('name') != request.chairmanName]
            director_for_signature = non_chairman_directors[0] if non_chairman_directors else (request.presentDirectors[0] if request.presentDirectors else {'name': '', 'din': ''})
            
            # Create basic placeholder mapping
            placeholders = {
                '[No. of Meeting]': request.meetingNumber,
                '[Type of Meeting]': request.meetingType,
                '[Name of Company]': request.companyName,
                '[Day of Meeting]': request.meetingDay,
                '[Date of Meeting]': request.meetingDate,
                '[Time: COMMENCED AT]': request.meetingStartTime,
                '[Time: CONCLUDED AT]': request.meetingEndTime,
                '[Place of Meeting]': request.meetingPlace,
                '[Chairman]': request.chairmanName,
                '[Director]': director_for_signature.get('name', ''),  # Different from chairman
                '[Date-previous-meeting]': request.previousMeetingDate,
                '[amount]': request.auditorPaymentAmount,
                '[Amount-in-words]': request.auditorPaymentWords,
                '[amount-in-words]': request.auditorPaymentWords,
                '[Year]': request.financialYear,
                '[year]': request.financialYear,
                '[YEAR]': request.financialYear,
                '[start-year]': request.financialYear.split('-')[0] if '-' in request.financialYear else request.financialYear,
                '[end-year]': request.financialYear.split('-')[1] if '-' in request.financialYear else str(int(request.financialYear) + 1),
                '[Day-of-meeting]': request.meetingDay,
                '[Month-of-meeting]': request.agmMonthName,
                '[TIME]': request.agmTime,
                '[Office-address]': request.agmPlace,
                '[Date-of-Recording]': request.recordingDate,
                '[Date-of-signing]': request.signingDate,
                '[Place of signing]': request.signingPlace,
                '[Officer]': request.companySecretary or request.authorisedOfficer,
            }
            
            # Replace basic placeholders in paragraphs first
            for para in doc.paragraphs:
                for placeholder, value in placeholders.items():
                    if placeholder in para.text:
                        para.text = para.text.replace(placeholder, str(value))
            
            # Replace basic placeholders in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for placeholder, value in placeholders.items():
                            if placeholder in cell.text:
                                cell.text = cell.text.replace(placeholder, str(value))
            
            # Replace placeholders in headers and footers
            for section in doc.sections:
                # Replace in header
                for para in section.header.paragraphs:
                    for placeholder, value in placeholders.items():
                        if placeholder in para.text:
                            para.text = para.text.replace(placeholder, str(value))
                
                # Replace in header tables
                for table in section.header.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for placeholder, value in placeholders.items():
                                if placeholder in cell.text:
                                    cell.text = cell.text.replace(placeholder, str(value))
                
                # Replace in footer
                for para in section.footer.paragraphs:
                    for placeholder, value in placeholders.items():
                        if placeholder in para.text:
                            para.text = para.text.replace(placeholder, str(value))
                
                # Replace in footer tables
                for table in section.footer.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for placeholder, value in placeholders.items():
                                if placeholder in cell.text:
                                    cell.text = cell.text.replace(placeholder, str(value))
            
            # Smart replacement for [Dir-name] and [Din-num] - replace each occurrence with different directors
            if request.presentDirectors and len(request.presentDirectors) > 0:
                director_index = 0
                total_directors = len(request.presentDirectors)
                
                # Replace in paragraphs - each occurrence gets a different director
                for para in doc.paragraphs:
                    while '[Dir-name]' in para.text or '[Din-num]' in para.text:
                        if director_index < total_directors:
                            current_director = request.presentDirectors[director_index]
                            # Replace only the first occurrence in this paragraph
                            if '[Dir-name]' in para.text:
                                para.text = para.text.replace('[Dir-name]', current_director.get('name', ''), 1)
                            if '[Din-num]' in para.text:
                                para.text = para.text.replace('[Din-num]', current_director.get('din', ''), 1)
                            director_index += 1
                        else:
                            # No more directors, use empty or repeat
                            para.text = para.text.replace('[Dir-name]', '')
                            para.text = para.text.replace('[Din-num]', '')
                            break

            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"meeting_minutes_{request.template}_{timestamp}.docx"
            output_path = os.path.join(os.path.dirname(__file__), "..", "public", "templates", filename)
            
            # Save the document
            doc.save(output_path)
            
            return filename, output_path
        
        # Run document generation in thread pool
        loop = asyncio.get_event_loop()
        filename, output_path = await loop.run_in_executor(thread_pool, generate_document)
        
        # Return file for download
        from fastapi.responses import FileResponse
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating minutes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate minutes: {str(e)}")