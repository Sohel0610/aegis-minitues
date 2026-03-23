# Minutes Generation Route Module
# This module handles minutes preparation functionality including place management and document generation
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from docx import Document
import shutil

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
    
# Resolution Templates models
class ResolutionTemplateResponse(BaseModel):
    id: int
    template_name: str
    resolution_text: str
    created_at: str

class ResolutionTemplateCreate(BaseModel):
    template_name: str
    resolution_text: str

class ResolutionTemplatesList(BaseModel):
    data: List[ResolutionTemplateResponse]
    count: int

# Compliance models
class ComplianceResponse(BaseModel):
    id: int
    form: str
    description: str
    due_date: str
    status: str
    priority: str
    created_at: str

class ComplianceCreate(BaseModel):
    form: str
    description: str
    due_date: str
    status: str
    priority: str

class CompliancesList(BaseModel):
    data: List[ComplianceResponse]
    count: int

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
    # Disclosure of Interest (Section 184)
    hasSection184Disclosure: bool = False
    section184Subject: Optional[str] = ""
    section184Text: Optional[str] = ""
    resolutions: Optional[str] = ""
    customTemplateFilename: Optional[str] = None

# Initialize places database on startup
init_places_db()

# Initialize minutes database
MINUTES_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "minutes.db")

def init_minutes_db():
    try:
        conn = sqlite3.connect(MINUTES_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_minutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                meeting_type TEXT,
                meeting_date TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resolution_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT,
                resolution_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form TEXT,
                description TEXT,
                due_date TEXT,
                status TEXT,
                priority TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize minutes database: {e}")

init_minutes_db()

class GeneratedMinuteResponse(BaseModel):
    id: int
    company_name: str
    meeting_type: str
    meeting_date: str
    file_path: str
    created_at: str
    download_url: str

class MinutesHistoryResponse(BaseModel):
    data: List[GeneratedMinuteResponse]
    count: int

class MinuteGenerationResponse(BaseModel):
    success: bool
    message: str
    filename: str
    download_url: str

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

# Endpoint to upload a custom template
@router.post("/upload-template")
async def upload_template(file: UploadFile = File(...)):
    """Upload a custom meeting minutes template"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")
    
    try:
        # Standardize filename to avoid conflicts and security issues
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_filename = f"custom_{timestamp}_{file.filename}"
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        
        # Ensure directory exists
        os.makedirs(templates_dir, exist_ok=True)
        
        file_path = os.path.join(templates_dir, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"filename": safe_filename, "message": "Template uploaded successfully"}
    except Exception as e:
        logger.error(f"Error uploading template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload template: {str(e)}")

# Endpoint to generate meeting minutes document from template
@router.post("/generate-minutes", response_model=MinuteGenerationResponse)
async def generate_minutes(request: MinutesGenerationRequest):
    """Generate meeting minutes document from template"""
    try:
        logger.info(f"Generating minutes for template: {request.template}")
        
        # Define template path
        if request.template == "custom" and request.customTemplateFilename:
            template_path = os.path.join(os.path.dirname(__file__), "..", "public", "templates", request.customTemplateFilename)
        else:
            template_path = os.path.join(os.path.dirname(__file__), "..", "public", "templates", f"{request.template.lower()}_meeting_template.docx")
        
        # If specific template not found, try generic one or default
        if not os.path.exists(template_path):
            if request.template == "custom":
                 raise HTTPException(status_code=404, detail="Custom template file not found")
            # Fallback to q1_meeting_template.docx if specific one doesn't exist
            fallback_path = os.path.join(os.path.dirname(__file__), "..", "public", "templates", "q1_meeting_template.docx")
            if os.path.exists(fallback_path):
                template_path = fallback_path
            else:
                raise HTTPException(status_code=404, detail=f"Template {request.template} not found and fallback missing")
        
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
                '[Section-184-Text]': request.section184Text if request.hasSection184Disclosure else "",
                '[Resolutions]': request.resolutions or "",
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
            
            # Smart replacement for [Dir-name] and [Din-num]
            if request.presentDirectors and len(request.presentDirectors) > 0:
                director_index = 0
                total_directors = len(request.presentDirectors)
                
                # Replace in paragraphs
                for para in doc.paragraphs:
                    while '[Dir-name]' in para.text or '[Din-num]' in para.text:
                        if director_index < total_directors:
                            current_director = request.presentDirectors[director_index]
                            if '[Dir-name]' in para.text:
                                para.text = para.text.replace('[Dir-name]', current_director.get('name', ''), 1)
                            if '[Din-num]' in para.text:
                                para.text = para.text.replace('[Din-num]', current_director.get('din', ''), 1)
                            director_index += 1
                        else:
                            para.text = para.text.replace('[Dir-name]', '')
                            para.text = para.text.replace('[Din-num]', '')
                            break

            # Generate filename: Company - Type - Date (DD-MM-YYYY)
            # Ensure date is in DD-MM-YYYY format
            try:
                # Try to parse ISO format YYYY-MM-DD
                date_obj = datetime.strptime(request.meetingDate, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                # Fallback if already in other format or invalid
                formatted_date = request.meetingDate.replace('/', '-')

            sanitized_company = "".join([c for c in request.companyName if c.isalnum() or c in (' ', '-', '_')]).strip()
            sanitized_type = "".join([c for c in request.meetingType if c.isalnum() or c in (' ', '-', '_')]).strip()
            
            filename = f"{sanitized_company} - {sanitized_type} - {formatted_date}.docx"
            output_path = os.path.join(os.path.dirname(__file__), "..", "public", "templates", filename)
            
            # Save the document
            doc.save(output_path)
            
            # Save to database
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO generated_minutes (company_name, meeting_type, meeting_date, file_path)
                VALUES (?, ?, ?, ?)
            ''', (request.companyName, request.meetingType, formatted_date, filename))
            conn.commit()
            conn.close()
            
            return filename, output_path
        
        # Run document generation in thread pool
        loop = asyncio.get_event_loop()
        filename, output_path = await loop.run_in_executor(thread_pool, generate_document)
        
        # Return JSON response
        return MinuteGenerationResponse(
            success=True,
            message="Minutes generated successfully",
            filename=filename,
            download_url=f"/api/generated-minutes/download/{filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating minutes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate minutes: {str(e)}")

# Endpoint to get generated minutes history
@router.get("/generated-minutes", response_model=MinutesHistoryResponse)
async def get_generated_minutes_history():
    """Get history of generated minutes"""
    try:
        def fetch_history():
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, company_name, meeting_type, meeting_date, file_path, created_at FROM generated_minutes ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            return [
                GeneratedMinuteResponse(
                    id=row[0],
                    company_name=row[1],
                    meeting_type=row[2],
                    meeting_date=row[3],
                    file_path=row[4],
                    created_at=row[5],
                    download_url=f"/api/generated-minutes/download/{row[4]}"
                )
                for row in rows
            ]
        
        loop = asyncio.get_event_loop()
        history = await loop.run_in_executor(thread_pool, fetch_history)
        
        return MinutesHistoryResponse(
            data=history,
            count=len(history)
        )
    except Exception as e:
        logger.error(f"Error fetching minutes history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

@router.delete("/generated-minutes/{id}")
async def delete_generated_minute(id: int):
    """Delete a generated minute record and file"""
    try:
        def do_delete():
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            # Get filename first
            cursor.execute("SELECT file_path FROM generated_minutes WHERE id = ?", (id,))
            row = cursor.fetchone()
            if row:
                filename = row[0]
                # Delete from DB
                cursor.execute("DELETE FROM generated_minutes WHERE id = ?", (id,))
                conn.commit()
                # Delete file
                file_path = os.path.join(os.path.dirname(__file__), "..", "public", "templates", filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            conn.close()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, do_delete)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting minute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to list all templates
@router.get("/templates")
async def list_templates():
    """List all available DOCX templates"""
    try:
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        if not os.path.exists(templates_dir):
            return {"data": [], "count": 0}
            
        files = []
        for f in os.listdir(templates_dir):
            if f.endswith('.docx') and not f.startswith('~'):
                file_path = os.path.join(templates_dir, f)
                stats = os.stat(file_path)
                files.append({
                    "name": f,
                    "size": stats.st_size,
                    "lastModified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "path": f
                })
        
        return {"data": files, "count": len(files)}
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to download generated minutes or templates
@router.get("/generated-minutes/download/{filename}")
@router.get("/templates/download/{filename}")
async def download_file(filename: str):
    """Download a file from templates directory"""
    try:
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        file_path = os.path.join(templates_dir, filename)
        
        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="File not found")
            
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

# Endpoint to delete a template
@router.delete("/templates/{filename}")
async def delete_template(filename: str):
    """Delete a template file"""
    try:
        # Prevent traversal attacks
        if ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        file_path = os.path.join(templates_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        os.remove(file_path)
        return {"success": True, "message": "Template deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting template {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# RESOLUTION TEMPLATE ENDPOINTS
@router.get("/resolutions", response_model=ResolutionTemplatesList)
async def get_resolutions():
    """Get all resolution templates"""
    try:
        def fetch_res():
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, template_name, resolution_text, created_at FROM resolution_templates ORDER BY template_name")
            rows = cursor.fetchall()
            conn.close()
            return [ResolutionTemplateResponse(id=r[0], template_name=r[1], resolution_text=r[2], created_at=r[3]) for r in rows]
        
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(thread_pool, fetch_res)
        return ResolutionTemplatesList(data=res, count=len(res))
    except Exception as e:
        logger.error(f"Error fetching resolutions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resolutions", response_model=ResolutionTemplateResponse)
async def create_resolution(request: ResolutionTemplateCreate):
    """Create a new resolution template"""
    try:
        def insert_res():
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO resolution_templates (template_name, resolution_text) VALUES (?, ?)", 
                         (request.template_name, request.resolution_text))
            res_id = cursor.lastrowid
            conn.commit()
            cursor.execute("SELECT id, template_name, resolution_text, created_at FROM resolution_templates WHERE id = ?", (res_id,))
            row = cursor.fetchone()
            conn.close()
            return ResolutionTemplateResponse(id=row[0], template_name=row[1], resolution_text=row[2], created_at=row[3])
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, insert_res)
    except Exception as e:
        logger.error(f"Error creating resolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/resolutions/{id}")
async def delete_resolution(id: int):
    """Delete a resolution template"""
    try:
        def do_delete():
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resolution_templates WHERE id = ?", (id,))
            conn.commit()
            conn.close()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, do_delete)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting resolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# COMPLIANCE ENDPOINTS
@router.get("/compliances", response_model=CompliancesList)
async def get_compliances():
    """Get all secretarial compliances"""
    try:
        def fetch_comp():
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, form, description, due_date, status, priority, created_at FROM compliances ORDER BY due_date")
            rows = cursor.fetchall()
            conn.close()
            return [ComplianceResponse(
                id=r[0], form=r[1], description=r[2], due_date=r[3], 
                status=r[4], priority=r[5], created_at=r[6]
            ) for r in rows]
        
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(thread_pool, fetch_comp)
        return CompliancesList(data=res, count=len(res))
    except Exception as e:
        logger.error(f"Error fetching compliances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliances", response_model=ComplianceResponse)
async def create_compliance(request: ComplianceCreate):
    """Create a new compliance record"""
    try:
        def insert_comp():
            conn = sqlite3.connect(MINUTES_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO compliances (form, description, due_date, status, priority) VALUES (?, ?, ?, ?, ?)", 
                         (request.form, request.description, request.due_date, request.status, request.priority))
            comp_id = cursor.lastrowid
            conn.commit()
            cursor.execute("SELECT id, form, description, due_date, status, priority, created_at FROM compliances WHERE id = ?", (comp_id,))
            row = cursor.fetchone()
            conn.close()
            return ComplianceResponse(
                id=row[0], form=row[1], description=row[2], due_date=row[3], 
                status=row[4], priority=row[5], created_at=row[6]
            )
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, insert_comp)
    except Exception as e:
        logger.error(f"Error creating compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))