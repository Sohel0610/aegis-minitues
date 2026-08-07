# Minutes Generation Route Module
# This module handles minutes preparation functionality including place management and document generation using PostgreSQL
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import asyncio
import concurrent.futures
from datetime import datetime
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
import shutil
from utils.pgsql_service import get_pg_connection, get_pg_cursor
from utils.auth_dep import require_session
from fastapi import Depends

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for minutes endpoints
router = APIRouter()

# --- Models ---

class GeneratedMinuteResponse(BaseModel):
    id: int
    company_name: str
    meeting_type: str
    meeting_date: str
    file_path: str
    created_at: str
    download_url: Optional[str] = None

class MinutesHistoryResponse(BaseModel):
    data: List[GeneratedMinuteResponse]
    count: int

class PlaceResponse(BaseModel):
    id: int
    name: str
    address: str
    is_default: bool
    created_at: str

class PlacesListResponse(BaseModel):
    data: List[PlaceResponse]
    count: int

class PlaceCreateRequest(BaseModel):
    name: str
    address: str
    is_default: bool = False
    
class ResolutionTemplateResponse(BaseModel):
    id: int
    template_name: str
    resolution_text: str
    created_at: str

class ResolutionTemplatesList(BaseModel):
    data: List[ResolutionTemplateResponse]
    count: int

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

# --- Database Init ---

def init_minutes_pg():
    """Initialize minutes tables in PostgreSQL public schema."""
    target_db = os.getenv('POSTGRES_DATABASE_MINUTES')
    conn = get_pg_connection(target_db)
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            
            # Generated Minutes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_minutes (
                    id SERIAL PRIMARY KEY,
                    company_name TEXT,
                    meeting_type TEXT,
                    meeting_date TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Resolution Templates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resolution_templates (
                    id SERIAL PRIMARY KEY,
                    template_name TEXT UNIQUE,
                    resolution_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Compliance Tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliances (
                    id SERIAL PRIMARY KEY,
                    form TEXT,
                    description TEXT,
                    due_date TEXT,
                    status TEXT,
                    priority TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Places Table (Local to minutes if needed, or shared)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS places (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    address TEXT,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info(f"Minutes tables initialized successfully in {target_db or 'default'}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Minutes init failed: {e}")
        finally:
            conn.close()

# --- API Endpoints ---

@router.get("/generated-minutes", response_model=MinutesHistoryResponse)
async def get_history():
    """Get history of generated minutes from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, company_name, meeting_type, meeting_date, file_path, created_at FROM generated_minutes ORDER BY id DESC")
                rows = cursor.fetchall()
                data = [GeneratedMinuteResponse(
                    id=r['id'], 
                    company_name=r['company_name'], 
                    meeting_type=r['meeting_type'], 
                    meeting_date=str(r['meeting_date']), 
                    file_path=r['file_path'], 
                    created_at=str(r['created_at']),
                    download_url=f"/api/generated-minutes/download/{r['file_path']}"
                ) for r in rows]
                return data, len(data)
            finally:
                conn.close()
        
        loop = asyncio.get_running_loop()
        data, count = await loop.run_in_executor(thread_pool, fetch)
        return MinutesHistoryResponse(data=data, count=count)
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/minutes/history", response_model=MinutesHistoryResponse)
async def get_minutes_history_post():
    """Fallback for POST history request."""
    return await get_history()

@router.delete("/generated-minutes/{id}")
async def delete_minute(id: int, user: dict = Depends(require_session)):
    try:
        def delete():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT file_path FROM generated_minutes WHERE id = %s", (id,))
                row = cursor.fetchone()
                if row:
                    fp = os.path.join(os.path.dirname(__file__), "..", "public", "templates", row['file_path'])
                    if os.path.exists(fp): os.remove(fp)
                    cursor.execute("DELETE FROM generated_minutes WHERE id = %s", (id,))
                    conn.commit()
                    return True
            finally:
                conn.close()
            return False
        success = await asyncio.get_running_loop().run_in_executor(thread_pool, delete)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generated-minutes/download/{filename}")
@router.get("/templates/download/{filename}")
async def download_file(filename: str):
    fp = os.path.join(os.path.dirname(__file__), "..", "public", "templates", filename)
    if not os.path.exists(fp): raise HTTPException(status_code=404)
    from fastapi.responses import FileResponse
    return FileResponse(path=fp, filename=filename, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

@router.get("/templates")
async def list_templates():
    td = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
    if not os.path.exists(td): return {"data": [], "count": 0}
    fs = []
    for f in os.listdir(td):
        if f.endswith('.docx') and not f.startswith('~'):
            stats = os.stat(os.path.join(td, f))
            fs.append({"name": f, "size": stats.st_size, "lastModified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'), "path": f})
    return {"data": fs, "count": len(fs)}

# --- Place Endpoints ---

@router.get("/places", response_model=PlacesListResponse)
async def get_places():
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, name, address, is_default, created_at FROM places ORDER BY name")
                rows = cursor.fetchall()
                return [PlaceResponse(id=r['id'], name=r['name'], address=r['address'], is_default=r['is_default'], created_at=str(r['created_at'])) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        return PlacesListResponse(data=data, count=len(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/places", response_model=PlaceResponse)
async def create_place(request: PlaceCreateRequest, user: dict = Depends(require_session)):
    try:
        def insert():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("DB connection failed")
            cursor = get_pg_cursor(conn)
            try:
                # If this is default, unset other defaults
                if request.is_default:
                    cursor.execute("UPDATE places SET is_default = FALSE")
                
                cursor.execute(
                    "INSERT INTO places (name, address, is_default) VALUES (%s, %s, %s) RETURNING id, name, address, is_default, created_at",
                    (request.name, request.address, request.is_default))
                row = cursor.fetchone()
                conn.commit()
                return PlaceResponse(id=row['id'], name=row['name'], address=row['address'], is_default=row['is_default'], created_at=str(row['created_at']))
            finally:
                conn.close()
        return await asyncio.get_event_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Compliance Endpoints ---

@router.get("/compliances", response_model=CompliancesList)
async def get_compliances():
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, form, description, due_date, status, priority, created_at FROM compliances ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [ComplianceResponse(id=r['id'], form=r['form'], description=r['description'],
                                          due_date=r['due_date'], status=r['status'], priority=r['priority'],
                                          created_at=str(r['created_at'])) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        return CompliancesList(data=data, count=len(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliances", response_model=ComplianceResponse)
async def create_compliance(request: ComplianceCreate, user: dict = Depends(require_session)):
    try:
        def insert():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("DB connection failed")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute(
                    "INSERT INTO compliances (form, description, due_date, status, priority) VALUES (%s, %s, %s, %s, %s) RETURNING id, form, description, due_date, status, priority, created_at",
                    (request.form, request.description, request.due_date, request.status, request.priority))
                row = cursor.fetchone()
                conn.commit()
                return ComplianceResponse(id=row['id'], form=row['form'], description=row['description'],
                                         due_date=row['due_date'], status=row['status'], priority=row['priority'],
                                         created_at=str(row['created_at']))
            finally:
                conn.close()
        return await asyncio.get_running_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Place Create Endpoint ---

@router.post("/places", response_model=PlaceResponse)
async def create_place(request: PlaceCreateRequest):
    """Create a new meeting place in PostgreSQL."""
    try:
        def insert():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                raise RuntimeError("DB connection failed")
            cursor = get_pg_cursor(conn)
            try:
                # If this is set as default, unset other defaults
                if request.is_default:
                    cursor.execute("UPDATE places SET is_default = FALSE WHERE is_default = TRUE")

                cursor.execute(
                    "INSERT INTO places (name, address, is_default) VALUES (%s, %s, %s) RETURNING id, name, address, is_default, created_at",
                    (request.name, request.address, request.is_default)
                )
                row = cursor.fetchone()
                conn.commit()
                return PlaceResponse(
                    id=row['id'], name=row['name'], address=row['address'],
                    is_default=row['is_default'], created_at=str(row['created_at'])
                )
            finally:
                conn.close()
        return await asyncio.get_running_loop().run_in_executor(thread_pool, insert)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating place: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Upload Custom Template Endpoint ---

@router.post("/upload-template")
async def upload_template(file: UploadFile = File(...)):
    """Upload a custom DOCX template for minutes generation."""
    if not file.filename or not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    try:
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        os.makedirs(templates_dir, exist_ok=True)

        # Generate a unique filename to avoid collisions
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = file.filename.replace(' ', '_')
        filename = f"custom_{timestamp}_{safe_name}"
        file_path = os.path.join(templates_dir, filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Custom template uploaded: {filename}")
        return {"filename": filename, "message": "Template uploaded successfully"}
    except Exception as e:
        logger.error(f"Error uploading template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload template: {str(e)}")


# --- Minutes Generation Endpoint ---

class MinutesGenerationRequest(BaseModel):
    template: str
    companyName: str
    meetingNumber: str = ""
    meetingType: str = ""
    meetingDay: str = ""
    meetingDate: str = ""
    meetingStartTime: str = ""
    meetingEndTime: str = ""
    meetingPlace: str = ""
    chairmanName: str = ""
    presentDirectors: List[Dict[str, str]] = []
    inAttendance: List[Dict[str, str]] = []
    companySecretary: str = ""
    previousMeetingDate: str = ""
    authorisedOfficer: str = ""
    quorum: str = ""
    concerns: str = ""
    declarations: str = ""
    auditorPaymentAmount: str = ""
    auditorPaymentWords: str = ""
    financialYear: str = ""
    agmNumber: str = ""
    agmDay: str = ""
    agmMonthName: str = ""
    agmDate: str = ""
    agmTime: str = ""
    agmPlace: str = ""
    recordingDate: str = ""
    signingDate: str = ""
    signingPlace: str = ""
    # Extended fields from FormBasedGenerator
    hasSection184Disclosure: bool = False
    section184Subject: str = ""
    section184Text: str = ""
    resolutions: str = ""
    customTemplateFilename: Optional[str] = None
    # TemplateRenderer sends directors as a list too
    directors: List[Dict[str, str]] = []


@router.post("/generate-minutes")
async def generate_minutes(request: MinutesGenerationRequest):
    """Generate meeting minutes document from a DOCX template with placeholder replacement."""
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=500, detail="python-docx is not installed on the server")

    try:
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")

        # Resolve the template path
        if request.template == 'custom' and request.customTemplateFilename:
            template_path = os.path.join(templates_dir, request.customTemplateFilename)
        else:
            template_path = os.path.join(templates_dir, f"{request.template.lower()}_meeting_template.docx")

        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail=f"Template '{request.template}' not found at expected path")

        def generate_document():
            doc = Document(template_path)

            # Merge presentDirectors and directors (TemplateRenderer sends 'directors')
            all_directors = request.presentDirectors or request.directors or []

            # Get non-chairman director for signature tables
            non_chairman = [d for d in all_directors if d.get('name') != request.chairmanName]
            sig_director = non_chairman[0] if non_chairman else (all_directors[0] if all_directors else {'name': '', 'din': ''})

            # Build placeholder mapping
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
                '[Director]': sig_director.get('name', ''),
                '[Date-previous-meeting]': request.previousMeetingDate,
                '[amount]': request.auditorPaymentAmount,
                '[Amount-in-words]': request.auditorPaymentWords,
                '[amount-in-words]': request.auditorPaymentWords,
                '[Year]': request.financialYear,
                '[year]': request.financialYear,
                '[YEAR]': request.financialYear,
                '[start-year]': request.financialYear.split('-')[0] if '-' in request.financialYear else request.financialYear,
                '[end-year]': request.financialYear.split('-')[1] if '-' in request.financialYear else (str(int(request.financialYear) + 1) if request.financialYear.isdigit() else ''),
                '[Day-of-meeting]': request.meetingDay,
                '[Month-of-meeting]': request.agmMonthName,
                '[TIME]': request.agmTime,
                '[Office-address]': request.agmPlace,
                '[Date-of-Recording]': request.recordingDate,
                '[Date-of-signing]': request.signingDate,
                '[Place of signing]': request.signingPlace,
                '[Officer]': request.companySecretary or request.authorisedOfficer,
            }

            # Helper: replace placeholders in a paragraph (preserving formatting where possible)
            def replace_in_paragraph(para):
                for placeholder, value in placeholders.items():
                    if placeholder in para.text:
                        para.text = para.text.replace(placeholder, str(value))

            # Replace in document body paragraphs
            for para in doc.paragraphs:
                replace_in_paragraph(para)

            # Replace in document body tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for placeholder, value in placeholders.items():
                            if placeholder in cell.text:
                                cell.text = cell.text.replace(placeholder, str(value))

            # Replace in headers and footers
            for section in doc.sections:
                for para in section.header.paragraphs:
                    replace_in_paragraph(para)
                for table in section.header.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for placeholder, value in placeholders.items():
                                if placeholder in cell.text:
                                    cell.text = cell.text.replace(placeholder, str(value))
                for para in section.footer.paragraphs:
                    replace_in_paragraph(para)
                for table in section.footer.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for placeholder, value in placeholders.items():
                                if placeholder in cell.text:
                                    cell.text = cell.text.replace(placeholder, str(value))

            # Smart [Dir-name] / [Din-num] replacement — each occurrence gets a different director
            if all_directors:
                director_index = 0
                total_directors = len(all_directors)
                for para in doc.paragraphs:
                    while '[Dir-name]' in para.text or '[Din-num]' in para.text:
                        if director_index < total_directors:
                            d = all_directors[director_index]
                            if '[Dir-name]' in para.text:
                                para.text = para.text.replace('[Dir-name]', d.get('name', ''), 1)
                            if '[Din-num]' in para.text:
                                para.text = para.text.replace('[Din-num]', d.get('din', ''), 1)
                            director_index += 1
                        else:
                            para.text = para.text.replace('[Dir-name]', '')
                            para.text = para.text.replace('[Din-num]', '')
                            break

            # Save generated document
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"meeting_minutes_{request.template}_{timestamp}.docx"
            output_path = os.path.join(templates_dir, filename)
            doc.save(output_path)

            return filename, output_path

        loop = asyncio.get_running_loop()
        filename, output_path = await loop.run_in_executor(thread_pool, generate_document)

        # Record in PostgreSQL history
        try:
            def record_history():
                conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
                if not conn:
                    return
                cursor = get_pg_cursor(conn)
                try:
                    cursor.execute(
                        "INSERT INTO generated_minutes (company_name, meeting_type, meeting_date, file_path) VALUES (%s, %s, %s, %s)",
                        (request.companyName, request.meetingType, request.meetingDate, filename)
                    )
                    conn.commit()
                finally:
                    conn.close()
            await loop.run_in_executor(thread_pool, record_history)
        except Exception as hist_err:
            logger.warning(f"Failed to record history (non-fatal): {hist_err}")

        # Return JSON with download URL (the frontend expects JSON, not FileResponse)
        return {
            "message": "Document generated successfully!",
            "filename": filename,
            "download_url": f"/api/generated-minutes/download/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating minutes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate minutes: {str(e)}")


# --- Resolution Endpoints ---

@router.get("/resolutions", response_model=ResolutionTemplatesList)
async def get_resolutions():
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, template_name, resolution_text, created_at FROM resolution_templates ORDER BY template_name")
                rows = cursor.fetchall()
                return [ResolutionTemplateResponse(id=r['id'], template_name=r['template_name'], resolution_text=r['resolution_text'], created_at=str(r['created_at'])) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        return ResolutionTemplatesList(data=data, count=len(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resolutions", response_model=ResolutionTemplateResponse)
async def create_resolution(template_name: str, resolution_text: str, user: dict = Depends(require_session)):
    try:
        def insert():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("DB connection failed")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute(
                    "INSERT INTO resolution_templates (template_name, resolution_text) VALUES (%s, %s) RETURNING id, template_name, resolution_text, created_at",
                    (template_name, resolution_text))
                row = cursor.fetchone()
                conn.commit()
                return ResolutionTemplateResponse(id=row['id'], template_name=row['template_name'], resolution_text=row['resolution_text'], created_at=str(row['created_at']))
            finally:
                conn.close()
        return await asyncio.get_event_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# --- Generation Endpoints ---

@router.post("/upload-template")
async def upload_template(file: UploadFile = File(...), user: dict = Depends(require_session)):
    """Upload a custom DOCX template."""
    try:
        td = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        os.makedirs(td, exist_ok=True)
        fp = os.path.join(td, file.filename)
        with open(fp, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": "Template uploaded successfully", "filename": file.filename}
    except Exception as e:
        logger.error(f"Error uploading template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-minutes")
async def generate_minutes(request: MinutesGenerationRequest, user: dict = Depends(require_session)):
    """Generate meeting minutes document from template and log to PostgreSQL."""
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=500, detail="python-docx is not installed on the server.")
    
    try:
        logger.info(f"Generating minutes for template: {request.template}")
        
        # Define template path
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        
        # Check if it's a preset template or a custom one
        if request.template.lower() in ['q1', 'q2', 'q3', 'q4']:
            template_path = os.path.join(templates_dir, f"{request.template.lower()}_meeting_template.docx")
        else:
            template_path = os.path.join(templates_dir, request.template)
            
        if not os.path.exists(template_path):
            # Fallback check
            alt_path = os.path.join(templates_dir, f"{request.template.lower()}_meeting_template.docx")
            if os.path.exists(alt_path):
                template_path = alt_path
            else:
                raise HTTPException(status_code=404, detail=f"Template {request.template} not found at {template_path}")
        
        def process_doc():
            # Load the template
            doc = Document(template_path)
            
            # Get non-chairman directors for signature tables
            non_chairman_directors = [d for d in request.presentDirectors if d.get('name') != request.chairmanName]
            director_for_signature = non_chairman_directors[0] if non_chairman_directors else (request.presentDirectors[0] if request.presentDirectors else {'name': '', 'din': ''})
            
            # Basic placeholders
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
                '[Director]': director_for_signature.get('name', ''),
                '[Date-previous-meeting]': request.previousMeetingDate,
                '[amount]': request.auditorPaymentAmount,
                '[Amount-in-words]': request.auditorPaymentWords,
                '[amount-in-words]': request.auditorPaymentWords,
                '[Year]': request.financialYear,
                '[year]': request.financialYear,
                '[YEAR]': request.financialYear,
                '[Day-of-meeting]': request.meetingDay,
                '[Month-of-meeting]': request.agmMonthName,
                '[TIME]': request.agmTime,
                '[Office-address]': request.agmPlace,
                '[Date-of-Recording]': request.recordingDate,
                '[Date-of-signing]': request.signingDate,
                '[Place of signing]': request.signingPlace,
                '[Officer]': request.companySecretary or request.authorisedOfficer,
            }

            # Helper for multi-director replacement
            def replace_placeholders(text_container):
                nonlocal director_index
                if not hasattr(text_container, 'text'): return
                
                # First handle basic placeholders
                for p, v in placeholders.items():
                    if p in text_container.text:
                        text_container.text = text_container.text.replace(p, str(v))
                
                # Handle cycling directors
                while '[Dir-name]' in text_container.text or '[Din-num]' in text_container.text:
                    if director_index < len(request.presentDirectors):
                        curr = request.presentDirectors[director_index]
                        if '[Dir-name]' in text_container.text:
                            text_container.text = text_container.text.replace('[Dir-name]', curr.get('name', ''), 1)
                        if '[Din-num]' in text_container.text:
                            text_container.text = text_container.text.replace('[Din-num]', curr.get('din', ''), 1)
                        director_index += 1
                    else:
                        text_container.text = text_container.text.replace('[Dir-name]', '', 1)
                        text_container.text = text_container.text.replace('[Din-num]', '', 1)
                        break

            director_index = 0
            
            # Replace in paragraphs
            for para in doc.paragraphs:
                replace_placeholders(para)
            
            # Replace in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            replace_placeholders(para)
            
            # Replace in headers/footers
            for section in doc.sections:
                for header_para in section.header.paragraphs:
                    replace_placeholders(header_para)
                for header_table in section.header.tables:
                    for row in header_table.rows:
                        for cell in row.cells:
                            for para in cell.paragraphs:
                                replace_placeholders(para)
                                
                for footer_para in section.footer.paragraphs:
                    replace_placeholders(footer_para)
                for footer_table in section.footer.tables:
                    for row in footer_table.rows:
                        for cell in row.cells:
                            for para in cell.paragraphs:
                                replace_placeholders(para)

            # Generate output filename
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_company = request.companyName.replace(' ', '_')[:30]
            out_filename = f"Minutes_{safe_company}_{ts}.docx"
            out_path = os.path.join(templates_dir, out_filename)
            
            # Save
            doc.save(out_path)
            return out_filename

        # Run processing in thread pool
        loop = asyncio.get_event_loop()
        out_filename = await loop.run_in_executor(thread_pool, process_doc)
        
        # Log to PostgreSQL
        def log_to_db():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: return
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute(
                    "INSERT INTO generated_minutes (company_name, meeting_type, meeting_date, file_path) VALUES (%s, %s, %s, %s)",
                    (request.companyName, request.meetingType, request.meetingDate, out_filename)
                )
                conn.commit()
            finally:
                conn.close()
        
        await loop.run_in_executor(thread_pool, log_to_db)
        
        return {
            "message": "Minutes generated successfully",
            "filename": out_filename,
            "download_url": f"/api/generated-minutes/download/{out_filename}"
        }
        
    except Exception as e:
        logger.error(f"Error generating minutes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate minutes: {str(e)}")
