# Minutes Generation Route Module
# This module handles minutes preparation functionality including place management and document generation using PostgreSQL
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import re
import io
import json
import sqlite3
import logging
import asyncio
import concurrent.futures
from datetime import datetime
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
try:
    import pdfplumber
    PDF_PLUMBER_AVAILABLE = True
except ImportError:
    PDF_PLUMBER_AVAILABLE = False
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
import shutil
from utils.pgsql_service import get_pg_connection, get_pg_cursor
from utils.auth_dep import require_session
from fastapi import Depends


# --- Document Content Extraction Helpers ---

def extract_text_from_docx(file_bytes: bytes) -> Dict[str, Any]:
    """Extract text paragraphs and tables from a .docx file."""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    tables = []
    for tbl_idx, table in enumerate(doc.tables):
        rows_data = []
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells]
            rows_data.append(row_cells)
        if rows_data:
            headers = rows_data[0] if rows_data else []
            tables.append({
                "table_index": tbl_idx,
                "headers": headers,
                "rows": rows_data[1:] if len(rows_data) > 1 else [],
                "total_rows": len(rows_data) - 1
            })
    return {
        "text": "\n".join(paragraphs),
        "paragraph_count": len(paragraphs),
        "tables": tables,
        "table_count": len(tables)
    }


def render_resolutions_into_doc(doc, resolutions_text: str, anchor_para=None):
    """Insert resolution content preserving structure (MOM #8): plain lines become
    paragraphs; pipe/tab-delimited blocks become real DOCX tables. If anchor_para
    is given, content is relocated directly after it."""
    def is_table_line(ln: str) -> bool:
        return ('|' in ln and ln.count('|') >= 2) or ('\t' in ln)

    lines = resolutions_text.replace('\r\n', '\n').split('\n')
    created_elements = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_table_line(line):
            block = []
            while i < len(lines) and is_table_line(lines[i]):
                raw = lines[i].strip().strip('|')
                cells = [c.strip() for c in (raw.split('|') if '|' in lines[i] else raw.split('\t'))]
                # skip markdown separator rows such as ---|---
                if not all(set(c) <= set('-: ') for c in cells):
                    block.append(cells)
                i += 1
            if block:
                cols = max(len(r) for r in block)
                table = doc.add_table(rows=len(block), cols=cols)
                try:
                    table.style = 'Table Grid'
                except Exception:
                    pass
                for r_idx, row_cells in enumerate(block):
                    for c_idx in range(cols):
                        table.rows[r_idx].cells[c_idx].text = row_cells[c_idx] if c_idx < len(row_cells) else ''
                created_elements.append(table._tbl)
        else:
            if line.strip():
                p = doc.add_paragraph(line)
                created_elements.append(p._p)
            i += 1

    if anchor_para is not None:
        for el in reversed(created_elements):
            anchor_para._p.addnext(el)


def extract_text_from_pdf(file_bytes: bytes) -> Dict[str, Any]:
    """Extract text and tables from a .pdf file using pdfplumber."""
    all_text = []
    tables = []
    tbl_idx = 0

    if PDF_PLUMBER_AVAILABLE:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    all_text.append(page_text)
                page_tables = page.extract_tables()
                if page_tables:
                    for pt in page_tables:
                        if pt and len(pt) > 0:
                            headers = [str(c or '') for c in pt[0]]
                            rows = [[str(c or '') for c in row] for row in pt[1:]]
                            tables.append({
                                "table_index": tbl_idx,
                                "page": page_num + 1,
                                "headers": headers,
                                "rows": rows,
                                "total_rows": len(rows)
                            })
                            tbl_idx += 1
    elif PYPDF2_AVAILABLE:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)

    # OCR fallback for scanned/image-only PDFs (BRD #4 / #17)
    ocr_used = False
    if len("".join(all_text).strip()) < 50 and OCR_AVAILABLE:
        try:
            images = convert_from_bytes(file_bytes, dpi=200)
            ocr_text = []
            for img in images:
                page_text = pytesseract.image_to_string(img)
                if page_text and page_text.strip():
                    ocr_text.append(page_text.strip())
            if ocr_text:
                all_text = ocr_text
                ocr_used = True
        except Exception as ocr_err:
            logging.getLogger(__name__).warning(f"OCR fallback failed: {ocr_err}")

    return {
        "text": "\n".join(all_text),
        "paragraph_count": len(all_text),
        "tables": tables,
        "table_count": len(tables),
        "ocr_used": ocr_used
    }

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

class ResolutionCreate(BaseModel):
    template_name: str
    resolution_text: str

class ComplianceResponse(BaseModel):
    id: int
    form: str
    description: str
    due_date: str
    status: str
    priority: str
    company_name: Optional[str] = None
    vertical_name: Optional[str] = None
    created_at: str

class ComplianceCreate(BaseModel):
    form: str
    description: str
    due_date: str
    status: str
    priority: str
    company_name: Optional[str] = None
    vertical_name: Optional[str] = None

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
            
            # Verticals Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verticals (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    code TEXT UNIQUE
                )
            """)

            # Companies Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    cin TEXT,
                    type TEXT,
                    vertical_id INTEGER REFERENCES verticals(id),
                    status TEXT DEFAULT 'Active'
                )
            """)

            # Ensure companies table column extensions exist (safety for SQLite fallback schema updates)
            for col, col_type in [("cin", "TEXT"), ("type", "TEXT"), ("vertical_id", "INTEGER"), ("status", "TEXT DEFAULT 'Active'")]:
                try:
                    cursor.execute(f"ALTER TABLE companies ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            # Ensure generated_minutes schema extensions exist
            for col, col_type in [("vertical_name", "TEXT"), ("meeting_number", "TEXT"), ("meeting_year", "TEXT")]:
                try:
                    cursor.execute(f"ALTER TABLE generated_minutes ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            # Seed default Verticals
            cursor.execute("SELECT COUNT(*) as count FROM verticals")
            if cursor.fetchone()['count'] == 0:
                logger.info("Seeding default verticals...")
                verticals = [
                    ('Energy', 'ENG'),
                    ('Ports & Logistics', 'PRT'),
                    ('Gas & Utilities', 'GAS'),
                    ('Infrastructure', 'INF'),
                    ('Digital & Media', 'DIG')
                ]
                for name, code in verticals:
                    cursor.execute("INSERT INTO verticals (name, code) VALUES (%s, %s)", (name, code))

            # Seed default Companies under Verticals
            cursor.execute("SELECT COUNT(*) as count FROM companies")
            if cursor.fetchone()['count'] == 0:
                logger.info("Seeding default companies...")
                # We fetch vertical IDs
                cursor.execute("SELECT id, name FROM verticals")
                v_map = {r['name']: r['id'] for r in cursor.fetchall()}
                
                companies = [
                    ('Adani Green Energy Ltd.', 'L40106GJ2015PLC082851', 'Public', v_map.get('Energy'), 'Active'),
                    ('Adani Power Ltd.', 'L40100GJ1996PLC030533', 'Public', v_map.get('Energy'), 'Active'),
                    ('Adani Energy Solutions Ltd.', 'L40120GJ2013PLC077218', 'Public', v_map.get('Energy'), 'Active'),
                    ('Adani Ports and Special Economic Zone Ltd.', 'L63090GJ1998PLC034182', 'Public', v_map.get('Ports & Logistics'), 'Active'),
                    ('Adani Logistics Ltd.', 'U63090GJ2005PLC046481', 'Private', v_map.get('Ports & Logistics'), 'Active'),
                    ('Adani Total Gas Ltd.', 'L40100GJ2005PLC046553', 'Public', v_map.get('Gas & Utilities'), 'Active'),
                    ('Adani Enterprises Ltd.', 'L51100GJ1993PLC019006', 'Public', v_map.get('Infrastructure'), 'Active'),
                    ('Adani Wilmar Ltd.', 'L15140GJ1999PLC035320', 'Public', v_map.get('Infrastructure'), 'Active'),
                    ('Adani Digital Labs Private Ltd.', 'U72900DL2021PTC386026', 'Private', v_map.get('Digital & Media'), 'Active')
                ]
                for name, cin, ctype, v_id, status in companies:
                    if v_id:
                        cursor.execute(
                            "INSERT INTO companies (name, cin, type, vertical_id, status) VALUES (%s, %s, %s, %s, %s)",
                            (name, cin, ctype, v_id, status)
                        )
            
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
                    company_name TEXT,
                    vertical_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Ensure columns exist
            for col, col_type in [("company_name", "TEXT"), ("vertical_name", "TEXT")]:
                try:
                    cursor.execute(f"ALTER TABLE compliances ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            # Seed default Compliances
            cursor.execute("SELECT COUNT(*) as count FROM compliances")
            if cursor.fetchone()['count'] == 0:
                logger.info("Seeding default compliances...")
                seeded_compliances = [
                    ('Form MGT-7', 'Annual Return Filing', '2026-11-29', 'Pending', 'High', 'Adani Green Energy Ltd.', 'Energy'),
                    ('Form AOC-4', 'Filing of Audited Financial Statements', '2026-10-30', 'Pending', 'Critical', 'Adani Ports and Special Economic Zone Ltd.', 'Ports & Logistics'),
                    ('Form DIR-12', 'Filing for Appointment of statutory director', '2026-08-15', 'Completed', 'Medium', 'Adani Total Gas Ltd.', 'Gas & Utilities'),
                    ('Form MBP-1', 'First Board Meeting Interest Disclosure', '2026-04-30', 'Completed', 'High', 'Adani Power Ltd.', 'Energy'),
                    ('Form ADT-1', 'Statutory Auditor Appointment Filing', '2026-10-15', 'Pending', 'High', 'Adani Enterprises Ltd.', 'Infrastructure'),
                    ('Form DIR-8', 'Director Disqualification Declaration', '2026-04-30', 'Completed', 'Medium', 'Adani Digital Labs Private Ltd.', 'Digital & Media')
                ]
                for form, desc, due, status, priority, comp, vert in seeded_compliances:
                    cursor.execute(
                        "INSERT INTO compliances (form, description, due_date, status, priority, company_name, vertical_name) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (form, desc, due, status, priority, comp, vert)
                    )

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

            # Local manual-director overlay: writes here never touch the Director Disclosure DB
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_directors (
                    id SERIAL PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    din TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Per-meeting attendance records for real meeting/person-wise reporting
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_attendance (
                    id SERIAL PRIMARY KEY,
                    minutes_id INTEGER,
                    company_name TEXT,
                    meeting_type TEXT,
                    meeting_date TEXT,
                    director_name TEXT NOT NULL,
                    din TEXT,
                    status TEXT DEFAULT 'Present',
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

# Ensure tables exist on module load (idempotent: CREATE TABLE IF NOT EXISTS)
try:
    init_minutes_pg()
except Exception as _init_err:
    logger.error(f"init_minutes_pg on import failed: {_init_err}")

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
    if os.path.basename(filename) != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    base = os.path.join(os.path.dirname(__file__), "..", "public")
    for sub in ("generated", "templates"):
        fp = os.path.join(base, sub, filename)
        if os.path.exists(fp):
            from fastapi.responses import FileResponse
            return FileResponse(path=fp, filename=filename, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    raise HTTPException(status_code=404)

@router.get("/templates")
async def list_templates():
    """List templates from database repository with metadata."""
    td = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
    fs = []
    
    # Query database table first
    db_path = os.path.join(os.path.dirname(__file__), "..", "public", "local_fallback.db")
    if os.path.exists(db_path):
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, template_name, category, company_name, quarter, file_path, file_size, created_at FROM templates ORDER BY template_name")
            rows = cursor.fetchall()
            for r in rows:
                fs.append({
                    "id": r["id"],
                    "name": r["template_name"],
                    "category": r["category"],
                    "companyName": r["company_name"],
                    "quarter": r["quarter"],
                    "size": r["file_size"],
                    "lastModified": str(r["created_at"]),
                    "path": r["file_path"]
                })
            conn.close()
            if fs:
                return {"data": fs, "count": len(fs)}
        except Exception as err:
            logger.warning(f"Error querying templates table: {err}")

    # Fallback to filesystem scan if DB query is empty
    if os.path.exists(td):
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

# --- Compliance Endpoints ---

@router.get("/compliances", response_model=CompliancesList)
async def get_compliances():
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, form, description, due_date, status, priority, company_name, vertical_name, created_at FROM compliances ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [ComplianceResponse(id=r['id'], form=r['form'], description=r['description'],
                                          due_date=r['due_date'], status=r['status'], priority=r['priority'],
                                          company_name=r['company_name'] if 'company_name' in r.keys() else None,
                                          vertical_name=r['vertical_name'] if 'vertical_name' in r.keys() else None,
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
                    "INSERT INTO compliances (form, description, due_date, status, priority, company_name, vertical_name) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, form, description, due_date, status, priority, company_name, vertical_name, created_at",
                    (request.form, request.description, request.due_date, request.status, request.priority, request.company_name, request.vertical_name))
                row = cursor.fetchone()
                conn.commit()
                return ComplianceResponse(id=row['id'], form=row['form'], description=row['description'],
                                         due_date=row['due_date'], status=row['status'], priority=row['priority'],
                                         company_name=row['company_name'] if 'company_name' in row.keys() else None,
                                         vertical_name=row['vertical_name'] if 'vertical_name' in row.keys() else None,
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
    vertical_name: Optional[str] = "Energy"
    # TemplateRenderer sends directors as a list too
    directors: List[Dict[str, str]] = []


@router.post("/generate-minutes")
async def generate_minutes(request: MinutesGenerationRequest):
    """Generate meeting minutes document from a DOCX template with placeholder replacement."""
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=500, detail="python-docx is not installed on the server")

    try:
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")

        # Validate template name is provided
        if not request.template or not request.template.strip():
            raise HTTPException(status_code=400, detail="Template name is required. Please select a template before generating.")

        # Resolve the template path
        template_path = None
        if request.template == 'custom' and request.customTemplateFilename:
            template_path = os.path.join(templates_dir, request.customTemplateFilename)
            if not os.path.exists(template_path):
                raise HTTPException(status_code=400, detail=f"Custom template file '{request.customTemplateFilename}' not found on server. Please re-upload the template.")
        elif os.path.exists(os.path.join(templates_dir, request.template)):
            template_path = os.path.join(templates_dir, request.template)
        else:
            official_q_map = {
                'q1': '87. AGEL - BM - 28.04.2025.docx',
                'q2': '88. AGEL - BM - 28.07.2025.docx',
                'q3': '89. AGEL - BM - 28.10.2025.docx',
                'q4': '90. AGEL - BM - 23.01.2026.docx',
            }
            template_filename = official_q_map.get(request.template.lower(), f"{request.template.lower()}_meeting_template.docx")
            template_path = os.path.join(templates_dir, template_filename)

        # Final check: ensure the resolved template file exists
        if not os.path.exists(template_path):
            raise HTTPException(
                status_code=404,
                detail=f"Template '{request.template}' could not be resolved to an existing file. Available templates can be viewed on the Templates page."
            )

        def generate_document():
            doc = Document(template_path)

            # Merge presentDirectors and directors (TemplateRenderer sends 'directors')
            all_directors = request.presentDirectors or request.directors or []

            # Get non-chairman director for signature tables
            non_chairman = [d for d in all_directors if d.get('name') != request.chairmanName]
            sig_director = non_chairman[0] if non_chairman else (all_directors[0] if all_directors else {'name': '', 'din': ''})

            # Auto-pull real Director Disclosure DTOs (MBP-1 & DIR-8) via Service Repository
            mbp1_disclosures_list = []
            dir8_declarations_list = []

            for d in all_directors:
                d_din = d.get('din', '').strip()
                if d_din:
                    try:
                        from routes.directors_disclosure import get_director_disclosure_dto
                        dto = get_director_disclosure_dto(d_din)
                        if dto.dir8_confirmation:
                            dir8_declarations_list.append(dto.dir8_confirmation)
                        if dto.mbp1_disclosure_text:
                            mbp1_disclosures_list.append(dto.mbp1_disclosure_text)
                    except Exception as ex:
                        logger.warning(f"Failed to query director disclosure DTO for DIN {d_din}: {ex}")

            sec_184_text = request.section184Text or "\n".join(mbp1_disclosures_list) or "Notices of Interest in Form MBP-1 pursuant to Section 184(1) of the Companies Act, 2013 received from attending directors were placed before the Board and noted."
            sec_164_text = "\n".join(dir8_declarations_list) or "Declarations in Form DIR-8 in terms of Section 164(2) of the Companies Act, 2013 received from attending directors confirming no disqualification were taken on record."

            # Dynamic placeholders dictionary
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
                '[Manual]': request.chairmanName,
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
                '[Resolutions]': request.resolutions,
                '[resolutions]': request.resolutions,
                '[RESOLUTIONS]': request.resolutions,
                '[Section-184-Disclosures]': sec_184_text,
                '[Section-164-Declarations]': sec_164_text,
            }

            # Explicit Sample Place & Address Replacement Rules
            if request.meetingPlace and request.meetingPlace.strip():
                placeholders['Plot No. 83, Sector 32, Institutional Area, Gurgaon, Haryana 122001'] = request.meetingPlace
                placeholders['Plot No. 83, Sector 32, Institutional Area, Gurgaon, Haryana-122001'] = request.meetingPlace

            if request.signingPlace and request.signingPlace.strip():
                placeholders['hyderabad'] = request.signingPlace
                placeholders['Hyderabad'] = request.signingPlace
                placeholders['HYDERABAD'] = request.signingPlace.upper()

            # ════════════════════════════════════════════════════════════
            # SMART AUTO-DETECTION ENGINE
            # Instead of manually listing every sample string from every
            # template, we scan the document text at generation time
            # and dynamically discover company names, director names,
            # dates, and meeting numbers — then replace them with the
            # user's actual form data.
            # ════════════════════════════════════════════════════════════

            import re as _re

            # Gather the full text of the template for pattern scanning
            _full_text = "\n".join(p.text for p in doc.paragraphs)
            for _tbl in doc.tables:
                for _row in _tbl.rows:
                    for _cell in _row.cells:
                        _full_text += "\n" + "\n".join(p.text for p in _cell.paragraphs)

            # ── 1. AUTO-DETECT & REPLACE COMPANY NAMES ──────────────
            # Find all "ALL CAPS ... LIMITED/LTD" strings in the template
            if request.companyName and request.companyName.strip():
                upper_comp = request.companyName.upper()
                # Match company name patterns (10+ chars ending with LIMITED or LTD)
                _found_companies = _re.findall(
                    r'[A-Z][A-Z\s\(\)\-\']{8,}(?:LIMITED|LTD\.?)',
                    _full_text
                )
                _found_companies = list(set(c.strip() for c in _found_companies if len(c.strip()) > 10))

                # Filter: only replace companies that look like Adani entities or
                # match the template's BU company. Skip generic bank names, legal refs, etc.
                _skip_keywords = ['BANK ', 'STOCK EXCHANGE', 'SECURITIES', 'RESERVE BANK',
                                  'REGISTRAR', 'INSURANCE', 'SEBI', 'NSDL', 'CDSL']
                for _comp in _found_companies:
                    # Skip bank names and regulatory bodies
                    if any(sk in _comp for sk in _skip_keywords):
                        continue
                    # Skip if it's already the user's company name
                    if _comp == upper_comp:
                        continue
                    # Replace the sample company name with user's company
                    placeholders[_comp] = upper_comp

            # ── 2. AUTO-DETECT & REPLACE TITLE LINE (MINUTES OF THE...) ──
            # The title line follows the pattern:
            # "MINUTES OF THE <ORDINAL> MEETING OF ... <COMPANY NAME>"
            _title_pattern = _re.compile(
                r'(MINUTES\s+OF\s+THE\s+)([A-Z\s\-]+?)'
                r'(\s+MEETING\s+OF\s+(?:THE\s+)?(?:BOARD\s+OF\s+DIRECTORS|AUDIT\s+COMMITTEE|NOMINATION\s+AND\s+REMUNERATION\s+COMMITTEE|STAKEHOLDERS\s+RELATIONSHIP\s+COMMITTEE|CORPORATE\s+SOCIAL\s+RESPONSIBILITY\s+COMMITTEE|RISK\s+MANAGEMENT\s+COMMITTEE)\s+OF\s+)'
                r'(.+?)(?=\s*$|\s*\n)',
                _re.MULTILINE
            )
            _title_matches = _title_pattern.findall(_full_text)
            for _match in _title_matches:
                _old_ordinal = _match[1].strip()
                _old_company = _match[3].strip()
                # Replace the ordinal meeting number in the title
                if request.meetingNumber and request.meetingNumber.strip():
                    if _old_ordinal and _old_ordinal not in placeholders:
                        placeholders[_old_ordinal] = request.meetingNumber.upper()
                # Replace the company name in the title
                if request.companyName and request.companyName.strip():
                    if _old_company and _old_company not in placeholders:
                        placeholders[_old_company] = request.companyName.upper()

            # ── 3. AUTO-DETECT & REPLACE MEETING NUMBER ORDINALS ─────
            if request.meetingNumber and request.meetingNumber.strip():
                m_num = request.meetingNumber
                # Find word-ordinals like "EIGHTY SEVENTH", "FIFTY NINTH" etc.
                _ordinal_pattern = _re.compile(
                    r'\b('
                    r'(?:TWENTY|THIRTY|FORTY|FIFTY|SIXTY|SEVENTY|EIGHTY|NINETY)'
                    r'[\s\-]?'
                    r'(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)'
                    r'|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH'
                    r'|ELEVENTH|TWELFTH|THIRTEENTH|FOURTEENTH|FIFTEENTH|SIXTEENTH'
                    r'|SEVENTEENTH|EIGHTEENTH|NINETEENTH|TWENTIETH|THIRTIETH|FORTIETH'
                    r'|FIFTIETH|SIXTIETH|SEVENTIETH|EIGHTIETH|NINETIETH|HUNDREDTH'
                    r')\b'
                )
                _found_ordinals = set(_ordinal_pattern.findall(_full_text))
                for _ord in _found_ordinals:
                    # Only replace ordinals that appear in the TITLE context
                    # (i.e. near "MEETING OF"), not random uses like "FOURTH quarter"
                    _context_check = _re.search(
                        _re.escape(_ord) + r'\s+MEETING',
                        _full_text
                    )
                    if _context_check and _ord not in placeholders:
                        placeholders[_ord] = m_num

                # Also find numeric ordinals that reference previous meetings
                # e.g. "86TH", "87TH" (previous meeting number references)
                _num_ord_pattern = _re.compile(r'\b(\d+)(?:ST|ND|RD|TH)\s+MEETING\b', _re.IGNORECASE)
                _found_num_ords = _num_ord_pattern.findall(_full_text)
                for _n in set(_found_num_ords):
                    _full_match = _re.search(r'\b(' + _n + r'(?:ST|ND|RD|TH))\s+MEETING\b', _full_text, _re.IGNORECASE)
                    if _full_match:
                        _old_num_ord = _full_match.group(1)
                        if _old_num_ord not in placeholders:
                            placeholders[_old_num_ord] = m_num

            # ── 4. AUTO-DETECT & REPLACE DIRECTOR/PERSON NAMES ───────
            # Find all "Mr./Mrs./Ms./Shri <Name>" patterns in the template
            _person_pattern = _re.compile(
                r'(?:Mr\.|Mrs\.|Ms\.|Shri|Smt\.)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3}'
            )
            _found_persons = list(set(_person_pattern.findall(_full_text)))

            # Build a set of the user's entered director names for matching
            _user_director_names = set()
            for _d in all_directors:
                _dn = _d.get('name', '').strip()
                if _dn:
                    _user_director_names.add(_dn)
            if request.chairmanName and request.chairmanName.strip():
                _user_director_names.add(request.chairmanName)

            # Only replace sample person names that are NOT in the user's director list
            # (If the user actually has a director with the same name, don't replace it)
            _sample_persons = [p for p in _found_persons if p not in _user_director_names]

            # Don't auto-replace person names with a single value — that would make
            # every name in the doc the same. Instead, we only replace the CHAIRMAN
            # and the SIGNING DIRECTOR names. The rest of the attendance list is
            # handled by the [Dir-name]/[Din-num] placeholder system.
            # But we DO need to replace the specific chairman/signing names embedded
            # in the template's body text (resolutions, authorizations, etc.)
            if request.chairmanName and request.chairmanName.strip():
                # Find the first person mentioned in the template — that's typically
                # the chairman in the original sample
                # Look for the chairman pattern: appears right after "IN THE CHAIR" or
                # near "Chairman" context
                _chair_context = _re.search(
                    r'(?:Mr\.|Mrs\.|Ms\.)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3}'
                    r'(?=.*?(?:Chair|chair|CHAIR|presided))',
                    _full_text, _re.DOTALL
                )
                if _chair_context:
                    _old_chair = _chair_context.group(0).strip()
                    if _old_chair not in _user_director_names and _old_chair not in placeholders:
                        placeholders[_old_chair] = request.chairmanName
                        # Also add without honorific
                        _bare_old = _re.sub(r'^(?:Mr\.|Mrs\.|Ms\.)\s+', '', _old_chair)
                        if _bare_old and _bare_old not in placeholders:
                            _bare_new = _re.sub(r'^(?:Mr\.|Mrs\.|Ms\.)\s+', '', request.chairmanName)
                            placeholders[_bare_old] = _bare_new if _bare_new else request.chairmanName

            # ── 5. AUTO-DETECT & REPLACE KEY DATES ────────────────────
            # We only replace the PRIMARY meeting date (the one in the title/header)
            # and the previous meeting date. We do NOT replace random dates in
            # resolution bodies (like agreement dates, appointment dates, etc.)
            # because those are part of the legal content.
            if request.meetingDate and request.meetingDate.strip():
                m_date = request.meetingDate
                try:
                    dt_obj = datetime.strptime(m_date, '%Y-%m-%d')
                    day_num = dt_obj.day
                    ord_suffix = 'th' if 11 <= day_num <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
                    formatted_date_upper = f"{dt_obj.day}{ord_suffix.upper()} {dt_obj.strftime('%B %Y').upper()}"
                    formatted_date_title = f"{dt_obj.day}{ord_suffix} {dt_obj.strftime('%B, %Y')}"
                except Exception:
                    formatted_date_upper = m_date.upper()
                    formatted_date_title = m_date

                # Find the primary meeting date in the template
                # It's typically the date that appears in the title or right after
                # "held on" / "HELD ON" or matches the filename date
                # Strategy: extract the date from the template filename
                _template_basename = os.path.basename(template_path)
                _fname_date_match = _re.search(r'(\d{2})\.(\d{2})\.(\d{4})', _template_basename)
                if _fname_date_match:
                    _fd, _fm, _fy = _fname_date_match.groups()
                    _fname_date_str = f"{_fd}.{_fm}.{_fy}"
                    # Replace the DD.MM.YYYY format date
                    placeholders[_fname_date_str] = formatted_date_upper

                    # Build the spelled-out version of this date for replacement
                    try:
                        _tpl_dt = datetime(int(_fy), int(_fm), int(_fd))
                        _tpl_day = _tpl_dt.day
                        _tpl_suffix = 'th' if 11 <= _tpl_day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(_tpl_day % 10, 'th')
                        _month_name = _tpl_dt.strftime('%B')
                        _year = _tpl_dt.strftime('%Y')

                        # All common date format variations of the template's primary date
                        _date_variants = [
                            f"{_tpl_day}{_tpl_suffix.upper()} {_month_name.upper()}, {_year}",
                            f"{_tpl_day}{_tpl_suffix.upper()} {_month_name.upper()} {_year}",
                            f"{_tpl_day}{_tpl_suffix} {_month_name}, {_year}",
                            f"{_tpl_day}{_tpl_suffix} {_month_name} {_year}",
                            f"{_fd}{_tpl_suffix.upper()} {_month_name.upper()}, {_year}",
                            f"{_fd}{_tpl_suffix.upper()} {_month_name.upper()} {_year}",
                            f"{_fd}{_tpl_suffix} {_month_name}, {_year}",
                            f"{_fd}{_tpl_suffix} {_month_name} {_year}",
                        ]
                        for _dv in _date_variants:
                            if _dv in _full_text and _dv not in placeholders:
                                placeholders[_dv] = formatted_date_upper
                    except Exception:
                        pass

                # Also find the signing/recording date pattern (DD.MM.YYYY after the main date)
                _all_dotdates = _re.findall(r'\b(\d{2}\.\d{2}\.\d{4})\b', _full_text)
                for _dd in set(_all_dotdates):
                    # Only replace if it's the signing/conclusion date, not random dates
                    # The signing date typically appears near the end of the document
                    _dd_pos = _full_text.rfind(_dd)
                    _doc_len = len(_full_text)
                    if _dd_pos > _doc_len * 0.8:  # Last 20% of the document
                        if request.signingDate and request.signingDate.strip():
                            try:
                                _sd_obj = datetime.strptime(request.signingDate, '%Y-%m-%d')
                                _sd_day = _sd_obj.day
                                _sd_suf = 'th' if 11 <= _sd_day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(_sd_day % 10, 'th')
                                _sd_formatted = f"{_sd_day}{_sd_suf.upper()} {_sd_obj.strftime('%B %Y').upper()}"
                                placeholders[_dd] = _sd_formatted
                            except Exception:
                                placeholders[_dd] = request.signingDate

            # ── Style-preserving run-level replacement ──────────────────
            # Instead of setting para.text (which destroys all formatting),
            # we replace text inside individual runs so that each run's
            # font size, bold, italic, underline, color, etc. are kept.

            def _replace_in_runs(runs, placeholder, value):
                """Replace *placeholder* with *value* across a list of runs,
                preserving all run-level formatting.

                Case 1 – placeholder sits inside a single run:
                    Simply do run.text = run.text.replace(...)

                Case 2 – placeholder is split across consecutive runs:
                    Concatenate adjacent run texts, find the placeholder span,
                    put the replacement in the first participating run (keeping
                    its formatting), and clear the remaining runs.
                """
                val = str(value)

                # --- Single-run replacement (most common) ---
                for run in runs:
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, val)

                # --- Cross-run replacement (placeholder split by Word) ---
                # Word sometimes splits a single placeholder across 2-3 runs
                # e.g. run1="[Name of ", run2="Company]"
                full = "".join(r.text for r in runs)
                if placeholder not in full:
                    return  # nothing left to do

                while placeholder in "".join(r.text for r in runs):
                    combined = ""
                    start_idx = None
                    end_idx = None
                    for i, run in enumerate(runs):
                        combined += run.text
                        if start_idx is None and placeholder[:1] in run.text:
                            # potential start — re-check from this run
                            partial = "".join(r.text for r in runs[i:])
                            if partial.startswith(placeholder) or placeholder in "".join(r.text for r in runs[:i+1]):
                                pass  # continue scanning
                        if placeholder in combined:
                            end_idx = i
                            # walk backwards to find where placeholder text begins
                            back = ""
                            for j in range(i, -1, -1):
                                back = runs[j].text + back
                                if placeholder in back:
                                    start_idx = j
                                    break
                            break

                    if start_idx is None or end_idx is None:
                        break  # safety – avoid infinite loop

                    # Merge text of participating runs
                    merged = "".join(runs[k].text for k in range(start_idx, end_idx + 1))
                    replaced = merged.replace(placeholder, val, 1)

                    # Put replaced text in the FIRST run (keeps its formatting)
                    runs[start_idx].text = replaced
                    # Clear the rest
                    for k in range(start_idx + 1, end_idx + 1):
                        runs[k].text = ""

            def replace_in_paragraph(para):
                """Replace all placeholders in a paragraph while preserving
                each run's original font properties."""
                for placeholder, value in placeholders.items():
                    if not value:
                        continue
                    if placeholder in para.text:
                        _replace_in_runs(list(para.runs), placeholder, value)

            def replace_in_cell_preserving_style(cell):
                """Replace placeholders inside every paragraph of a table cell,
                preserving run-level formatting."""
                for para in cell.paragraphs:
                    replace_in_paragraph(para)

            # Replace in document body paragraphs
            for para in doc.paragraphs:
                replace_in_paragraph(para)

            # Replace in document body tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        replace_in_cell_preserving_style(cell)

            # Replace in headers and footers
            for section in doc.sections:
                for para in section.header.paragraphs:
                    replace_in_paragraph(para)
                for table in section.header.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            replace_in_cell_preserving_style(cell)
                for para in section.footer.paragraphs:
                    replace_in_paragraph(para)
                for table in section.footer.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            replace_in_cell_preserving_style(cell)

            # Smart [Dir-name] / [Din-num] & Attendance List replacement — each occurrence gets filled
            # Uses run-level replacement to preserve formatting
            if all_directors:
                director_index = 0
                total_directors = len(all_directors)
                for para in doc.paragraphs:
                    while '[Dir-name]' in para.text or '[Din-num]' in para.text:
                        if director_index < total_directors:
                            d = all_directors[director_index]
                            if '[Dir-name]' in para.text:
                                _replace_in_runs(list(para.runs), '[Dir-name]', d.get('name', ''))
                            if '[Din-num]' in para.text:
                                _replace_in_runs(list(para.runs), '[Din-num]', d.get('din', ''))
                            director_index += 1
                        else:
                            _replace_in_runs(list(para.runs), '[Dir-name]', '')
                            _replace_in_runs(list(para.runs), '[Din-num]', '')
                            break

            # ── 6. SMART TRANSFORM FOR HARDCODED TEXT (DATES, TIMES, ATTENDANCE, RESOLUTIONS) ──
            comp_name_upper = request.companyName.upper() if request.companyName else ""
            day_upper = request.meetingDay.upper() if request.meetingDay else ""
            
            # Format start time e.g. "10:11" -> "10:11 AM" & "10.11 A.M."
            start_time_str = request.meetingStartTime or ""
            start_time_dot_str = ""
            if start_time_str:
                try:
                    clean_time = start_time_str.strip()
                    if ":" in clean_time or "." in clean_time:
                        delim = ":" if ":" in clean_time else "."
                        parts = clean_time.split(delim)
                        hh = int(parts[0])
                        mm = parts[1][:2]
                        ampm = "AM" if hh < 12 else "PM"
                        ampm_dot = "A.M." if hh < 12 else "P.M."
                        hh12 = hh if hh <= 12 else hh - 12
                        if hh12 == 0: hh12 = 12
                        start_time_str = f"{hh12:02d}:{mm} {ampm}"
                        start_time_dot_str = f"{hh12:02d}.{mm} {ampm_dot}"
                except Exception:
                    pass

            # Format end time e.g. "11:11" -> "11:11 AM" & "11.11 A.M."
            end_time_str = request.meetingEndTime or ""
            end_time_dot_str = ""
            if end_time_str:
                try:
                    clean_etime = end_time_str.strip()
                    if ":" in clean_etime or "." in clean_etime:
                        delim = ":" if ":" in clean_etime else "."
                        parts = clean_etime.split(delim)
                        hh = int(parts[0])
                        mm = parts[1][:2]
                        ampm = "AM" if hh < 12 else "PM"
                        ampm_dot = "A.M." if hh < 12 else "P.M."
                        hh12 = hh if hh <= 12 else hh - 12
                        if hh12 == 0: hh12 = 12
                        end_time_str = f"{hh12:02d}:{mm} {ampm}"
                        end_time_dot_str = f"{hh12:02d}.{mm} {ampm_dot}"
                except Exception:
                    pass

            def format_date_ordinal(date_str):
                if not date_str:
                    return ""
                try:
                    dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    day = dt.day
                    suffix = "TH" if 11 <= day <= 13 else {1: "ST", 2: "ND", 3: "RD"}.get(day % 10, "TH")
                    month_name = dt.strftime("%B").upper()
                    return f"{day}{suffix} {month_name} {dt.year}"
                except Exception:
                    return date_str

            m_date_formatted = format_date_ordinal(request.meetingDate)
            rec_date_formatted = format_date_ordinal(request.recordingDate)
            sign_date_formatted = format_date_ordinal(request.signingDate)
            prev_date_formatted = format_date_ordinal(request.previousMeetingDate) or m_date_formatted

            # Build Global Director List from Website Input
            directors = all_directors

            def transform_text(text):
                if not text or not text.strip():
                    return text
                
                # 1. Generic Company Name Replacement (matches any company ending in LIMITED, LTD, PVT LTD, PRIVATE LIMITED or acronyms)
                if comp_name_upper:
                    text = re.sub(r'\b[A-Z0-9\s\(\)\&\.\-]{3,60}\s+(?:LIMITED|PVT\s+LTD|PRIVATE\s+LIMITED|LTD)\b', comp_name_upper, text, flags=re.IGNORECASE)
                    text = re.sub(r'\b(?:AGE\(UP\)L|AGE25BL|AGEL)\b', comp_name_upper, text, flags=re.IGNORECASE)
                
                # 2. Replace day names in headings (MONDAY..SUNDAY)
                if day_upper:
                    text = re.sub(r'\b(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b', day_upper, text, flags=re.IGNORECASE)
                
                # 3. Replace ALL internal meeting & financial dates (e.g. 22ND JULY 2025, 30TH SEPTEMBER 2025)
                if m_date_formatted:
                    text = re.sub(r'\b\d{1,2}(?:ST|ND|RD|TH)\s+(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)(?:,\s*|\s+)\d{4}\b', m_date_formatted, text, flags=re.IGNORECASE)

                # 4. Replace Commencement Time
                if start_time_str:
                    target_start = start_time_dot_str if ("." in text and ("P.M." in text or "A.M." in text or "p.m." in text)) else start_time_str
                    text = re.sub(r'(?:commenced|held)\s+at\s+\d{1,2}[\.:]\d{2}\s*(?:AM|PM|a\.m\.|p\.m\.|P\.M\.|A\.M\.)', f'commenced at {target_start}', text, flags=re.IGNORECASE)
                    text = re.sub(r'AT\s+\d{1,2}[\.:]\d{2}\s*(?:AM|PM|a\.m\.|p\.m\.|P\.M\.|A\.M\.)\s+AT', f'AT {target_start} AT', text, flags=re.IGNORECASE)

                # 5. Replace Conclusion Time (Vote of thanks)
                if end_time_str:
                    target_end = end_time_dot_str if ("." in text and ("P.M." in text or "A.M." in text or "p.m." in text)) else end_time_str
                    text = re.sub(r'(?:concluded|thanks\s+to\s+the\s+chair)\s+at\s+\d{1,2}[\.:]\d{2}\s*(?:AM|PM|a\.m\.|p\.m\.|P\.M\.|A\.M\.)', f'concluded with a vote of thanks to the chair at {target_end}', text, flags=re.IGNORECASE)

                # 6. Generic Director Replacement in internal committee tables & paragraphs
                if directors:
                    # Dynamically match honorific + name patterns (e.g. Mr. Ravi Kapoor, Mrs. Nayana Gadhvi, Mr. Vneet S. Jaain)
                    matched_names = set(re.findall(r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-zA-Z\.]+(?:\s+[A-Z][a-zA-Z\.]+)+)\b', text))
                    for idx, old_name in enumerate(matched_names):
                        mapped_d = directors[idx % len(directors)]
                        mapped_name = mapped_d.get('name', '')
                        if mapped_name:
                            text = text.replace(old_name, mapped_name)

                # 7. Replace sample signing places
                if request.signingPlace:
                    text = re.sub(r'\b[A-Z][a-z]{2,20}\b(?=\s+CHAIRMAN|\s*Date)', request.signingPlace, text)

                # 8. Handle Date of Entry & Date of Signing specifically
                if "Date of entry" in text or "Date of Recording" in text or "Date of Entry" in text:
                    if rec_date_formatted:
                        text = re.sub(r'(Date of entry|Date of Recording|Date of Entry):?\s*.*', f'Date of entry:\t{rec_date_formatted}', text, flags=re.IGNORECASE)

                if "Date of signing" in text or "Date of Signing" in text:
                    if sign_date_formatted:
                        text = re.sub(r'(Date of signing|Date of Signing):?\s*.*', f'Date of signing:\t{sign_date_formatted}', text, flags=re.IGNORECASE)
                    
                return text

            for para in doc.paragraphs:
                if para.text:
                    new_text = transform_text(para.text)
                    if new_text != para.text:
                        para.text = new_text

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            if para.text:
                                new_text = transform_text(para.text)
                                if new_text != para.text:
                                    para.text = new_text

            for section in doc.sections:
                for hp in section.header.paragraphs:
                    if hp.text:
                        hp.text = transform_text(hp.text)
                for ht in section.header.tables:
                    for r in ht.rows:
                        for c in r.cells:
                            for p in c.paragraphs:
                                if p.text:
                                    p.text = transform_text(p.text)
                for fp in section.footer.paragraphs:
                    if fp.text:
                        fp.text = transform_text(fp.text)

            # Ensure Chairman occupied the chair text matches request.chairmanName
            if request.chairmanName:
                for para in doc.paragraphs:
                    if "occupied the Chair" in para.text or "occupied the chair" in para.text:
                        para.text = re.sub(r'^.*?\boccupied the [Cc]hair', f"{request.chairmanName} occupied the Chair", para.text)

            # Rebuild Attendance Tables & Director lists dynamically
            if directors:
                # 1. Update Word Tables containing director rows
                for table in doc.tables:
                    headers = [cell.text.lower() for cell in table.rows[0].cells] if table.rows else []
                    if any("director" in h or "din" in h or "name" in h for h in headers):
                        row_idx = 1
                        for d_idx, d in enumerate(directors):
                            d_name = d.get('name', '')
                            d_din = d.get('din', '')
                            d_role = "Chairman" if d_name == request.chairmanName else (d.get('designation') or d.get('role') or "Director")

                            if row_idx < len(table.rows):
                                row = table.rows[row_idx]
                                if len(row.cells) >= 3:
                                    row.cells[0].text = str(d_idx + 1)
                                    row.cells[1].text = d_name
                                    row.cells[2].text = d_din or d_role
                                    if len(row.cells) >= 4:
                                        row.cells[3].text = d_role
                                elif len(row.cells) >= 2:
                                    row.cells[0].text = d_name
                                    row.cells[1].text = d_din or d_role
                                row_idx += 1
                            else:
                                new_row = table.add_row()
                                if len(new_row.cells) >= 3:
                                    new_row.cells[0].text = str(d_idx + 1)
                                    new_row.cells[1].text = d_name
                                    new_row.cells[2].text = d_din or d_role
                                    if len(new_row.cells) >= 4:
                                        new_row.cells[3].text = d_role
                                elif len(new_row.cells) >= 2:
                                    new_row.cells[0].text = d_name
                                    new_row.cells[1].text = d_din or d_role
                                row_idx += 1

                        while row_idx < len(table.rows):
                            for cell in table.rows[row_idx].cells:
                                cell.text = ""
                            row_idx += 1

                # 2. Update Paragraph-based attendance lists & remove extra XML nodes
                in_present_section = False
                dir_paras = []
                next_para = None

                for para in doc.paragraphs:
                    t = para.text.strip()
                    if "where the following directors were present" in t.lower() or "present physically" in t.lower():
                        in_present_section = True
                        continue
                    if in_present_section:
                        if "invitee" in t.lower() or "chairman" in t.lower() or "leave of absence" in t.lower():
                            in_present_section = False
                            next_para = para
                            break
                        elif re.match(r'^\d+\.\s*', t):
                            dir_paras.append(para)

                existing_count = len(dir_paras)
                for idx in range(max(len(directors), existing_count)):
                    if idx < len(directors):
                        d = directors[idx]
                        d_name = d.get('name', '')
                        d_role = "Chairman" if d_name == request.chairmanName else (d.get('designation') or d.get('role') or "Director")
                        formatted_line = f"{idx + 1}.\t{d_name}\t\t-\t{d_role}"
                        if idx < existing_count:
                            dir_paras[idx].text = formatted_line
                        else:
                            if next_para:
                                next_para.insert_paragraph_before(formatted_line)
                            else:
                                doc.add_paragraph(formatted_line)
                    else:
                        if idx < existing_count:
                            try:
                                p_elem = dir_paras[idx]._element
                                p_elem.getparent().remove(p_elem)
                            except Exception:
                                dir_paras[idx].text = ""

            # 3. Dynamic Resolutions Replacement (structure-preserving: text + tables)
            if request.resolutions and request.resolutions.strip():
                anchor = None
                for para in doc.paragraphs:
                    if "[Resolutions]" in para.text or "[resolutions]" in para.text or "[RESOLUTIONS]" in para.text:
                        para.text = para.text.replace("[Resolutions]", "").replace("[resolutions]", "").replace("[RESOLUTIONS]", "")
                        anchor = para
                        break

                if anchor is None:
                    doc.add_paragraph("\nMEETING RESOLUTIONS & BUSINESS TRANSACTED:\n")
                    render_resolutions_into_doc(doc, request.resolutions)
                else:
                    render_resolutions_into_doc(doc, request.resolutions, anchor_para=anchor)

            # Save generated document (kept separate from templates for production)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"meeting_minutes_{request.template}_{timestamp}.docx"
            generated_dir = os.path.join(os.path.dirname(__file__), "..", "public", "generated")
            os.makedirs(generated_dir, exist_ok=True)
            output_path = os.path.join(generated_dir, filename)
            doc.save(output_path)

            # BRD Req #7: Save to Structured Path Repository
            # Hierarchy: Vertical (BU) -> Company Name -> Meeting -> Type of Meeting -> Date(year)
            def _clean_str(s: str) -> str:
                return "".join(c for c in s if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')

            v_name = _clean_str(request.vertical_name or "Energy")
            c_name = _clean_str(request.companyName or "General_Company")
            m_name = _clean_str(f"Meeting_{request.meetingNumber}") if request.meetingNumber else "Meeting"
            t_name = _clean_str(request.meetingType or "Board_Meeting")
            y_name = request.meetingDate.split('-')[0] if (request.meetingDate and '-' in request.meetingDate) else str(datetime.now().year)

            structured_dir = os.path.join(
                os.path.dirname(__file__), "..", "public", "repository",
                v_name, c_name, m_name, t_name, y_name
            )
            os.makedirs(structured_dir, exist_ok=True)
            doc.save(os.path.join(structured_dir, filename))
            logger.info(f"Saved copy to structured directory: {structured_dir}")

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
                        "INSERT INTO generated_minutes (company_name, meeting_type, meeting_date, file_path) VALUES (%s, %s, %s, %s) RETURNING id",
                        (request.companyName, request.meetingType, request.meetingDate, filename)
                    )
                    row = cursor.fetchone()
                    minutes_id = row["id"] if row else None

                    # Persist per-director attendance for meeting/person-wise reports
                    attendees = request.presentDirectors or request.directors or []
                    for d in attendees:
                        d_name = (d.get('name') or '').strip()
                        if not d_name:
                            continue
                        cursor.execute("""
                            INSERT INTO meeting_attendance
                            (minutes_id, company_name, meeting_type, meeting_date, director_name, din, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (minutes_id, request.companyName, request.meetingType, request.meetingDate,
                              d_name, (d.get('din') or '').strip(), d.get('status') or 'Present'))
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
async def create_resolution(payload: ResolutionCreate, user: dict = Depends(require_session)):
    try:
        def insert():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("DB connection failed")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute(
                    "INSERT INTO resolution_templates (template_name, resolution_text) VALUES (%s, %s) RETURNING id, template_name, resolution_text, created_at",
                    (payload.template_name, payload.resolution_text))
                row = cursor.fetchone()
                conn.commit()
                return ResolutionTemplateResponse(id=row['id'], template_name=row['template_name'], resolution_text=row['resolution_text'], created_at=str(row['created_at']))
            finally:
                conn.close()
        return await asyncio.get_event_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/resolutions/{id}")
async def delete_resolution(id: int, user: dict = Depends(require_session)):
    try:
        def delete():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("DB connection failed")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("DELETE FROM resolution_templates WHERE id = %s", (id,))
                conn.commit()
                return {"message": "Resolution template deleted successfully"}
            finally:
                conn.close()
        return await asyncio.get_event_loop().run_in_executor(thread_pool, delete)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- New Verticals, Companies and Sourced Directors API ---

class VerticalResponse(BaseModel):
    id: int
    name: str
    code: str

class CompanyResponse(BaseModel):
    id: int
    name: str
    cin: Optional[str] = None
    type: Optional[str] = None
    vertical_id: Optional[int] = None
    status: Optional[str] = None

class VerticalsListResponse(BaseModel):
    data: List[VerticalResponse]
    count: int

class CompaniesListResponse(BaseModel):
    data: List[CompanyResponse]
    count: int

@router.get("/verticals", response_model=VerticalsListResponse)
async def get_verticals():
    """List all Verticals (Business Units)."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, name, code FROM verticals ORDER BY name")
                rows = cursor.fetchall()
                return [VerticalResponse(id=r['id'], name=r['name'], code=r['code']) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        return VerticalsListResponse(data=data, count=len(data))
    except Exception as e:
        logger.error(f"Error listing verticals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verticals/{vertical_id}/companies", response_model=CompaniesListResponse)
async def get_vertical_companies(vertical_id: int, q: Optional[str] = None, limit: int = 100, offset: int = 0):
    """List companies belonging to a Vertical, with query search and pagination."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                if q:
                    cursor.execute("""
                        SELECT id, name, cin, type, vertical_id, status FROM companies 
                        WHERE vertical_id = %s AND UPPER(name) LIKE UPPER(%s)
                        ORDER BY name
                        LIMIT %s OFFSET %s
                    """, (vertical_id, f"%{q}%", limit, offset))
                else:
                    cursor.execute("""
                        SELECT id, name, cin, type, vertical_id, status FROM companies 
                        WHERE vertical_id = %s
                        ORDER BY name
                        LIMIT %s OFFSET %s
                    """, (vertical_id, limit, offset))
                rows = cursor.fetchall()
                
                # Get total count for pagination info
                if q:
                    cursor.execute("SELECT COUNT(*) as count FROM companies WHERE vertical_id = %s AND UPPER(name) LIKE UPPER(%s)", (vertical_id, f"%{q}%"))
                else:
                    cursor.execute("SELECT COUNT(*) as count FROM companies WHERE vertical_id = %s", (vertical_id,))
                total = cursor.fetchone()['count'] or 0

                return [CompanyResponse(id=r['id'], name=r['name'], cin=r['cin'], type=r['type'], vertical_id=r['vertical_id'], status=r['status']) for r in rows], total
            finally:
                conn.close()
        data, count = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        return CompaniesListResponse(data=data, count=count)
    except Exception as e:
        logger.error(f"Error listing vertical companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/companies/{company_name}/directors")
async def get_company_directors(company_name: str):
    """Fetch directors for a company: read-only from Director Disclosure DB, merged with local manual overlay."""
    try:
        def fetch():
            term = company_name.strip()
            results = []
            seen = set()

            # 1. Read-only source: Director Disclosure DB (never written to from minutes pages)
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
            if conn:
                cursor = get_pg_cursor(conn)
                try:
                    cursor.execute("""
                        SELECT DISTINCT name, din
                        FROM directors_master.external_board_members
                        WHERE UPPER(company_name) = UPPER(%s) OR UPPER(company_name) LIKE UPPER(%s)
                        LIMIT 50
                    """, (term, f"%{term}%"))
                    rows = cursor.fetchall()
                except Exception as ex:
                    logger.warning(f"External board members query failed for {term}: {ex}")
                    rows = []

                if not rows:
                    try:
                        cursor.execute("""
                            SELECT DISTINCT d.name, d.din 
                            FROM directors_data.directorships ds
                            JOIN directors_data.directors d ON ds.din = d.din
                            JOIN directors_data.companies c ON ds.company_id = c.id
                            WHERE UPPER(c.name) = UPPER(%s) OR UPPER(c.name) LIKE UPPER(%s)
                            LIMIT 50
                        """, (term, f"%{term}%"))
                        rows = cursor.fetchall()
                    except Exception as ex:
                        logger.warning(f"Directorships query failed for {term}: {ex}")

                for r in rows:
                    key = (r["din"] or "").strip() or r["name"].strip().upper()
                    if key not in seen:
                        seen.add(key)
                        results.append({"name": r["name"], "din": r["din"], "source": "disclosure", "id": None})
                conn.close()

            # 2. Local overlay: manual entries stored in minutes DB only
            try:
                m_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
                if m_conn:
                    m_cursor = get_pg_cursor(m_conn)
                    try:
                        m_cursor.execute("""
                            SELECT id, name, din FROM company_directors
                            WHERE UPPER(company_name) = UPPER(%s)
                            ORDER BY name
                        """, (term,))
                        for r in m_cursor.fetchall():
                            key = (r["din"] or "").strip() or r["name"].strip().upper()
                            if key not in seen:
                                seen.add(key)
                                results.append({"name": r["name"], "din": r["din"], "source": "local", "id": r["id"]})
                    finally:
                        m_conn.close()
            except Exception as ex:
                logger.warning(f"Local overlay directors query failed: {ex}")

            if results:
                return results

            # Dynamic fallback to master directors database list if company specific directors returned 0 rows

            # Fallback to master directors database list if company specific directors returned 0 rows
            try:
                db_path = os.path.join(os.path.dirname(__file__), "..", "public", "local_fallback.db")
                if os.path.exists(db_path):
                    s_conn = sqlite3.connect(db_path)
                    s_conn.row_factory = sqlite3.Row
                    c = s_conn.cursor()
                    c.execute("SELECT name, din FROM directors_master LIMIT 10")
                    master_rows = c.fetchall()
                    s_conn.close()
                    if master_rows:
                        return [{"name": r["name"], "din": r["din"]} for r in master_rows]
            except Exception as ex:
                logger.warning(f"Fallback directors query failed: {ex}")

            return []

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(thread_pool, fetch)
        return {"data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching company directors: {e}")
        return {"data": [], "count": 0}


# --- Local Company Director Overlay CRUD (never writes to Director Disclosure DB) ---

class CompanyDirectorCreate(BaseModel):
    name: str
    din: Optional[str] = ""


@router.post("/companies/{company_name}/directors")
async def add_company_director(company_name: str, payload: CompanyDirectorCreate, user: dict = Depends(require_session)):
    """Add a manual director entry for a company in the local minutes DB only."""
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Director name is required")
    try:
        def insert():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    INSERT INTO company_directors (company_name, name, din)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, din, created_at
                """, (company_name.strip(), payload.name.strip(), (payload.din or "").strip()))
                row = cursor.fetchone()
                conn.commit()
                return {"id": row["id"], "name": row["name"], "din": row["din"],
                        "source": "local", "created_at": str(row["created_at"])}
            finally:
                conn.close()
        return await asyncio.get_running_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        logger.error(f"Error adding company director: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/companies/{company_name}/directors/{director_id}")
async def update_company_director(company_name: str, director_id: int, payload: CompanyDirectorCreate, user: dict = Depends(require_session)):
    """Update a manual (local) director entry. Disclosure-DB directors cannot be edited from here."""
    try:
        def update():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    UPDATE company_directors SET name = %s, din = %s
                    WHERE id = %s AND UPPER(company_name) = UPPER(%s)
                    RETURNING id, name, din, created_at
                """, (payload.name.strip(), (payload.din or "").strip(), director_id, company_name.strip()))
                row = cursor.fetchone()
                conn.commit()
                if not row:
                    return None
                return {"id": row["id"], "name": row["name"], "din": row["din"],
                        "source": "local", "created_at": str(row["created_at"])}
            finally:
                conn.close()
        result = await asyncio.get_running_loop().run_in_executor(thread_pool, update)
        if result is None:
            raise HTTPException(status_code=404, detail="Local director entry not found (registry directors are read-only)")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company director: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/companies/{company_name}/directors/{director_id}")
async def delete_company_director(company_name: str, director_id: int, user: dict = Depends(require_session)):
    """Delete a manual (local) director entry. Disclosure-DB directors cannot be deleted from here."""
    try:
        def delete():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    DELETE FROM company_directors
                    WHERE id = %s AND UPPER(company_name) = UPPER(%s)
                    RETURNING id
                """, (director_id, company_name.strip()))
                row = cursor.fetchone()
                conn.commit()
                return row is not None
            finally:
                conn.close()
        deleted = await asyncio.get_running_loop().run_in_executor(thread_pool, delete)
        if not deleted:
            raise HTTPException(status_code=404, detail="Local director entry not found (registry directors are read-only)")
        return {"message": "Director removed", "id": director_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company director: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resolutions/search")
async def search_resolutions(q: str = ""):
    """Keyword search for resolution templates by title or content."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn: raise RuntimeError("Database connection unavailable")
            cursor = get_pg_cursor(conn)
            try:
                term = f"%{q}%"
                cursor.execute("""
                    SELECT id, template_name, resolution_text, created_at 
                    FROM resolution_templates 
                    WHERE UPPER(template_name) LIKE UPPER(%s) OR UPPER(resolution_text) LIKE UPPER(%s)
                    ORDER BY template_name
                """, (term, term))
                rows = cursor.fetchall()
                return [ResolutionTemplateResponse(id=r['id'], template_name=r['template_name'], resolution_text=r['resolution_text'], created_at=str(r['created_at'])) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        return {"data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error searching resolutions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Structured Repository Explorer & Search APIs (BRD Requirements #7 & #10) ---

@router.get("/repository/tree")
async def get_repository_tree():
    """BRD Requirement #7: Return structured directory tree of generated minutes.
    Hierarchy: Vertical (BU) -> Company Name -> Meeting -> Type of Meeting -> Date(year)
    """
    repo_dir = os.path.join(os.path.dirname(__file__), "..", "public", "repository")
    
    def build_tree(path):
        tree = []
        if not os.path.exists(path):
            return tree
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            rel_path = os.path.relpath(full_path, repo_dir).replace('\\', '/')
            if os.path.isdir(full_path):
                tree.append({
                    "name": entry,
                    "type": "folder",
                    "path": rel_path,
                    "children": build_tree(full_path)
                })
            elif entry.endswith('.docx') or entry.endswith('.pdf'):
                stats = os.stat(full_path)
                tree.append({
                    "name": entry,
                    "type": "file",
                    "path": rel_path,
                    "size": stats.st_size,
                    "lastModified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "download_url": f"/api/generated-minutes/download/{entry}"
                })
        return tree

    try:
        loop = asyncio.get_running_loop()
        tree_data = await loop.run_in_executor(thread_pool, build_tree, repo_dir)
        return {"data": tree_data, "count": len(tree_data)}
    except Exception as e:
        logger.error(f"Error building repository tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repository/search")
async def search_repository(q: str = ""):
    """BRD Requirement #10: Keyword & Title Search for generated minutes documents across DB and Repository."""
    if not q or not q.strip():
        return await get_history()

    search_term = q.strip().upper()
    results = []

    try:
        # Search PostgreSQL DB records
        def search_db():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                return []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT id, company_name, meeting_type, meeting_date, file_path, created_at 
                    FROM generated_minutes 
                    WHERE UPPER(company_name) LIKE %s 
                       OR UPPER(meeting_type) LIKE %s 
                       OR UPPER(file_path) LIKE %s 
                    ORDER BY id DESC
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                rows = cursor.fetchall()
                return [GeneratedMinuteResponse(
                    id=r['id'],
                    company_name=r['company_name'],
                    meeting_type=r['meeting_type'],
                    meeting_date=str(r['meeting_date']),
                    file_path=r['file_path'],
                    created_at=str(r['created_at']),
                    download_url=f"/api/generated-minutes/download/{r['file_path']}"
                ) for r in rows]
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        db_results = await loop.run_in_executor(thread_pool, search_db)
        return {"data": db_results, "count": len(db_results)}
    except Exception as e:
        logger.error(f"Error searching repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repository/upload")
async def upload_repository_document(
    file: UploadFile = File(...),
    vertical_name: str = Form("Energy"),
    company_name: str = Form("General_Company"),
    meeting_number: str = Form("1"),
    meeting_type: str = Form("Board_Meeting"),
    meeting_year: str = Form("2026")
):
    """BRD Requirement #8: Upload PDF/Word document into structured repository folder path.
    Now also extracts text + tables from uploaded documents and stores parsed content in DB."""
    if not file.filename or not (file.filename.endswith('.pdf') or file.filename.endswith('.docx') or file.filename.endswith('.pptx')):
        raise HTTPException(status_code=400, detail="Only .pdf, .docx and .pptx files are supported")

    def _clean_str(s: str) -> str:
        return "".join(c for c in s if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')

    try:
        v_name = _clean_str(vertical_name)
        c_name = _clean_str(company_name)
        m_name = _clean_str(f"Meeting_{meeting_number}")
        t_name = _clean_str(meeting_type)
        y_name = _clean_str(meeting_year)

        target_dir = os.path.join(
            os.path.dirname(__file__), "..", "public", "repository",
            v_name, c_name, m_name, t_name, y_name
        )
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, file.filename)
        file_bytes = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # --- Extract text + tables from uploaded document ---
        extracted = {"text": "", "paragraph_count": 0, "tables": [], "table_count": 0}
        try:
            if file.filename.endswith('.docx') and DOCX_AVAILABLE:
                extracted = extract_text_from_docx(file_bytes)
            elif file.filename.endswith('.pdf'):
                extracted = extract_text_from_pdf(file_bytes)
        except Exception as parse_err:
            logger.warning(f"Content extraction failed for {file.filename}: {parse_err}")

        # Record in PostgreSQL history + store extracted content
        def record_db():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if conn:
                cursor = get_pg_cursor(conn)
                try:
                    # Ensure document_contents table exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS document_contents (
                            id SERIAL PRIMARY KEY,
                            filename VARCHAR(500) NOT NULL,
                            company_name VARCHAR(500),
                            vertical_name VARCHAR(200),
                            meeting_type VARCHAR(200),
                            meeting_year VARCHAR(10),
                            file_type VARCHAR(10),
                            extracted_text TEXT,
                            tables_json JSONB,
                            paragraph_count INTEGER DEFAULT 0,
                            table_count INTEGER DEFAULT 0,
                            file_path VARCHAR(1000),
                            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()

                    # Insert extracted content
                    file_ext = os.path.splitext(file.filename)[1].lstrip('.')
                    rel_path = f"{v_name}/{c_name}/{m_name}/{t_name}/{y_name}/{file.filename}"
                    cursor.execute("""
                        INSERT INTO document_contents 
                        (filename, company_name, vertical_name, meeting_type, meeting_year, file_type,
                         extracted_text, tables_json, paragraph_count, table_count, file_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        file.filename, company_name, vertical_name, meeting_type, meeting_year,
                        file_ext, extracted["text"], json.dumps(extracted["tables"]),
                        extracted["paragraph_count"], extracted["table_count"], rel_path
                    ))
                    doc_id = cursor.fetchone()["id"]

                    # Also insert into generated_minutes for repository tree listing
                    cursor.execute("""
                        INSERT INTO generated_minutes (company_name, meeting_type, meeting_date, file_path)
                        VALUES (%s, %s, %s, %s)
                    """, (company_name, meeting_type, f"{meeting_year}-01-01", file.filename))
                    conn.commit()
                    return doc_id
                except Exception as db_err:
                    logger.error(f"DB error during document content save: {db_err}")
                    conn.rollback()
                    return None
                finally:
                    conn.close()
            return None

        loop = asyncio.get_running_loop()
        doc_id = await loop.run_in_executor(thread_pool, record_db)

        logger.info(f"Repository file uploaded and parsed: {file_path} (text: {extracted['paragraph_count']} paragraphs, tables: {extracted['table_count']})")
        return {
            "message": "File uploaded and parsed successfully",
            "filename": file.filename,
            "document_id": doc_id,
            "path": f"{v_name}/{c_name}/{m_name}/{t_name}/{y_name}/{file.filename}",
            "extraction_summary": {
                "paragraphs": extracted["paragraph_count"],
                "tables": extracted["table_count"],
                "ocr_used": extracted.get("ocr_used", False),
                "text_preview": extracted["text"][:300] + "..." if len(extracted["text"]) > 300 else extracted["text"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading repository document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.get("/repository/documents")
async def get_repository_documents(q: str = "", vertical: str = "", limit: int = 50):
    """List all uploaded documents with extracted content metadata. Supports keyword search."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                return []
            cursor = get_pg_cursor(conn)
            try:
                if q:
                    cursor.execute("""
                        SELECT id, filename, company_name, vertical_name, meeting_type, meeting_year,
                               file_type, paragraph_count, table_count, file_path, uploaded_at
                        FROM document_contents
                        WHERE LOWER(filename) LIKE %s OR LOWER(extracted_text) LIKE %s 
                              OR LOWER(company_name) LIKE %s
                        ORDER BY uploaded_at DESC LIMIT %s
                    """, (f"%{q.lower()}%", f"%{q.lower()}%", f"%{q.lower()}%", limit))
                elif vertical:
                    cursor.execute("""
                        SELECT id, filename, company_name, vertical_name, meeting_type, meeting_year,
                               file_type, paragraph_count, table_count, file_path, uploaded_at
                        FROM document_contents
                        WHERE LOWER(vertical_name) = %s
                        ORDER BY uploaded_at DESC LIMIT %s
                    """, (vertical.lower(), limit))
                else:
                    cursor.execute("""
                        SELECT id, filename, company_name, vertical_name, meeting_type, meeting_year,
                               file_type, paragraph_count, table_count, file_path, uploaded_at
                        FROM document_contents
                        ORDER BY uploaded_at DESC LIMIT %s
                    """, (limit,))
                rows = cursor.fetchall()
                return [{
                    "id": r["id"],
                    "filename": r["filename"],
                    "company_name": r["company_name"],
                    "vertical_name": r["vertical_name"],
                    "meeting_type": r["meeting_type"],
                    "meeting_year": r["meeting_year"],
                    "file_type": r["file_type"],
                    "paragraph_count": r["paragraph_count"],
                    "table_count": r["table_count"],
                    "file_path": r["file_path"],
                    "uploaded_at": str(r["uploaded_at"])
                } for r in rows]
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        docs = await loop.run_in_executor(thread_pool, fetch)
        return {"data": docs, "count": len(docs)}
    except Exception as e:
        logger.error(f"Error fetching repository documents: {e}")
        return {"data": [], "count": 0}


@router.get("/repository/document-content/{doc_id}")
async def get_document_content(doc_id: int):
    """Retrieve full extracted text and tables for a document (queries document_contents DB or parses file on-the-fly)."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                raise HTTPException(status_code=503, detail="Database unavailable")
            cursor = get_pg_cursor(conn)
            try:
                # 1. Try fetching from document_contents table
                cursor.execute("""
                    SELECT id, filename, company_name, vertical_name, meeting_type, meeting_year,
                           file_type, extracted_text, tables_json, paragraph_count, table_count, 
                           file_path, uploaded_at
                    FROM document_contents WHERE id = %s
                """, (doc_id,))
                row = cursor.fetchone()
                if row:
                    tables = row["tables_json"]
                    if isinstance(tables, str):
                        tables = json.loads(tables)
                    return {
                        "id": row["id"],
                        "filename": row["filename"],
                        "company_name": row["company_name"],
                        "vertical_name": row["vertical_name"],
                        "meeting_type": row["meeting_type"],
                        "meeting_year": row["meeting_year"],
                        "file_type": row["file_type"],
                        "extracted_text": row["extracted_text"],
                        "tables": tables,
                        "paragraph_count": row["paragraph_count"],
                        "table_count": row["table_count"],
                        "file_path": row["file_path"],
                        "uploaded_at": str(row["uploaded_at"])
                    }

                # 2. Fallback: Query generated_minutes table and parse file from disk on-the-fly
                cursor.execute("""
                    SELECT id, company_name, meeting_type, meeting_date, file_path, created_at
                    FROM generated_minutes WHERE id = %s
                """, (doc_id,))
                gm_row = cursor.fetchone()
                if not gm_row:
                    return None

                filename = gm_row["file_path"]
                # Search disk locations
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), "..", "public", "templates", filename),
                    os.path.join(os.path.dirname(__file__), "..", "public", "repository", filename)
                ]
                
                # Search recursively in repository directory if needed
                repo_base = os.path.join(os.path.dirname(__file__), "..", "public", "repository")
                if os.path.exists(repo_base):
                    for root, _, files in os.walk(repo_base):
                        if filename in files:
                            possible_paths.append(os.path.join(root, filename))

                found_path = None
                for p in possible_paths:
                    if os.path.exists(p):
                        found_path = p
                        break

                extracted = {"text": "Document file not found on server disk.", "paragraph_count": 0, "tables": [], "table_count": 0}
                file_ext = os.path.splitext(filename)[1].lstrip('.')

                if found_path:
                    try:
                        with open(found_path, "rb") as f:
                            file_bytes = f.read()
                        if filename.endswith('.docx') and DOCX_AVAILABLE:
                            extracted = extract_text_from_docx(file_bytes)
                        elif filename.endswith('.pdf'):
                            extracted = extract_text_from_pdf(file_bytes)
                    except Exception as p_err:
                        logger.warning(f"On-the-fly extraction error for {filename}: {p_err}")

                return {
                    "id": gm_row["id"],
                    "filename": filename,
                    "company_name": gm_row["company_name"],
                    "vertical_name": "General",
                    "meeting_type": gm_row["meeting_type"],
                    "meeting_year": str(gm_row["meeting_date"])[:4] if gm_row["meeting_date"] else "2026",
                    "file_type": file_ext,
                    "extracted_text": extracted["text"],
                    "tables": extracted["tables"],
                    "paragraph_count": extracted["paragraph_count"],
                    "table_count": extracted["table_count"],
                    "file_path": filename,
                    "uploaded_at": str(gm_row["created_at"]) if gm_row.get("created_at") else "N/A"
                }
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(thread_pool, fetch)
        if result is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document content {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/compliances/kpis")
async def get_compliance_kpis():
    """Compute secretarial compliance KPI analytics from PostgreSQL."""
    try:
        def compute():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                return {
                    "total_compliances": 6,
                    "completed": 3,
                    "pending": 3,
                    "critical": 1,
                    "completion_rate": 50.0
                }
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT COUNT(*) as count FROM compliances")
                total = cursor.fetchone()['count'] or 0

                cursor.execute("SELECT COUNT(*) as count FROM compliances WHERE LOWER(status) = 'completed'")
                completed = cursor.fetchone()['count'] or 0

                cursor.execute("SELECT COUNT(*) as count FROM compliances WHERE LOWER(status) = 'pending'")
                pending = cursor.fetchone()['count'] or 0

                cursor.execute("SELECT COUNT(*) as count FROM compliances WHERE LOWER(priority) = 'critical'")
                critical = cursor.fetchone()['count'] or 0

                rate = round((completed / total * 100), 1) if total > 0 else 0.0

                # MOM #17: compliance evidence derived from uploaded/OCR-extracted documents
                documents_analysis = {"documents_processed": 0, "meetings_detected": 0, "meeting_dates": [], "companies_covered": []}
                try:
                    cursor.execute("""
                        SELECT id, filename, company_name, meeting_type, meeting_year, extracted_text
                        FROM document_contents ORDER BY id DESC LIMIT 200
                    """)
                    docs = cursor.fetchall()
                    date_pattern = re.compile(
                        r'\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+\d{4}'
                        r'|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}[,\s]+\d{4}'
                        r'|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', re.IGNORECASE)
                    all_dates = set()
                    companies = set()
                    meetings = 0
                    for d in docs:
                        text = d['extracted_text'] or ''
                        found = date_pattern.findall(text[:20000])
                        if found:
                            meetings += 1
                            all_dates.update(found[:5])
                        if d['company_name']:
                            companies.add(d['company_name'])
                    documents_analysis = {
                        "documents_processed": len(docs),
                        "meetings_detected": meetings,
                        "meeting_dates": sorted(all_dates)[:25],
                        "companies_covered": sorted(companies)
                    }
                except Exception as doc_err:
                    logger.warning(f"Document-based compliance analysis skipped: {doc_err}")

                return {
                    "total_compliances": total,
                    "completed": completed,
                    "pending": pending,
                    "critical": critical,
                    "completion_rate": rate,
                    "documents_analysis": documents_analysis
                }
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        kpi_data = await loop.run_in_executor(thread_pool, compute)
        return kpi_data
    except Exception as e:
        logger.error(f"Error computing compliance KPIs: {e}")
        return {
            "total_compliances": 6,
            "completed": 3,
            "pending": 3,
            "critical": 1,
            "completion_rate": 50.0
        }


@router.get("/reports/attendance")
async def get_attendance_report(company_name: Optional[str] = None):
    """BRD Requirement #4: Return person-wise and meeting-wise attendance tracking data (real data)."""
    try:
        def fetch_report():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                return {"person_wise": [], "meeting_wise": []}
            cursor = get_pg_cursor(conn)
            try:
                params = []
                company_filter = ""
                if company_name:
                    company_filter = " WHERE UPPER(company_name) = UPPER(%s)"
                    params.append(company_name)

                # Meeting-wise: real attendee counts per generated meeting
                cursor.execute(f"""
                    SELECT gm.id, gm.company_name, gm.meeting_type, gm.meeting_date, gm.file_path,
                           COALESCE(SUM(CASE WHEN ma.status = 'Present' THEN 1 ELSE 0 END), 0) AS present_count,
                           COUNT(ma.id) AS total_directors
                    FROM generated_minutes gm
                    LEFT JOIN meeting_attendance ma ON ma.minutes_id = gm.id
                    {company_filter.replace('company_name', 'gm.company_name') if company_filter else ''}
                    GROUP BY gm.id, gm.company_name, gm.meeting_type, gm.meeting_date, gm.file_path
                    ORDER BY gm.id DESC LIMIT 100
                """, tuple(params))
                rows = cursor.fetchall()

                meeting_wise = [{
                    "company_name": r["company_name"],
                    "meeting_type": r["meeting_type"],
                    "meeting_date": str(r["meeting_date"]),
                    "total_attendees": r["present_count"],
                    "total_directors": r["total_directors"],
                    "file_path": r["file_path"]
                } for r in rows]

                # Person-wise: per-director attended vs invited across recorded meetings
                cursor.execute(f"""
                    SELECT director_name, MAX(din) AS din,
                           SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS attended,
                           COUNT(*) AS invited
                    FROM meeting_attendance
                    {company_filter}
                    GROUP BY director_name
                    ORDER BY attended DESC, director_name
                """, tuple(params))
                p_rows = cursor.fetchall()

                person_wise = [{
                    "director_name": p["director_name"],
                    "din": p["din"],
                    "meetings_attended": p["attended"],
                    "meetings_invited": p["invited"],
                    "attendance_rate": f"{round((p['attended'] / p['invited']) * 100)}%" if p["invited"] else "0%"
                } for p in p_rows]

                return {
                    "meeting_wise": meeting_wise,
                    "person_wise": person_wise
                }
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        report_data = await loop.run_in_executor(thread_pool, fetch_report)
        return report_data
    except Exception as e:
        logger.error(f"Error building attendance report: {e}")
        return {"person_wise": [], "meeting_wise": []}


# --- MOM Email Delivery ---

class EmailDeliveryRequest(BaseModel):
    to_emails: List[str]
    subject: str = "Meeting Minutes"
    body: str = "Please find the attached Meeting Minutes document."
    filename: str  # File name from public/templates/ directory


@router.post("/email/send-mom")
async def send_mom_email(request: EmailDeliveryRequest):
    """BRD Requirement: Send generated MOM as email attachment via SMTP."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    # Locate the file (generated outputs first, templates for legacy files)
    if os.path.basename(request.filename) != request.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    base = os.path.join(os.path.dirname(__file__), "..", "public")
    file_path = None
    for sub in ("generated", "templates"):
        candidate = os.path.join(base, sub, request.filename)
        if os.path.exists(candidate):
            file_path = candidate
            break
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File not found: {request.filename}")

    # Read SMTP config from environment
    smtp_host = os.getenv("SMTP_HOST", "smtp.office365.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        raise HTTPException(
            status_code=503,
            detail="SMTP credentials not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM in .env"
        )

    try:
        def send_email():
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = ", ".join(request.to_emails)
            msg['Subject'] = request.subject

            msg.attach(MIMEText(request.body, 'html'))

            # Attach the file
            with open(file_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{request.filename}"')
                msg.attach(part)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            return True

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(thread_pool, send_email)

        logger.info(f"MOM email sent to {request.to_emails} with attachment {request.filename}")
        return {"message": "Email sent successfully", "recipients": request.to_emails}
    except smtplib.SMTPException as smtp_err:
        logger.error(f"SMTP error: {smtp_err}")
        raise HTTPException(status_code=502, detail=f"Failed to send email: {str(smtp_err)}")
    except Exception as e:
        logger.error(f"Email delivery error: {e}")
        raise HTTPException(status_code=500, detail=f"Email delivery failed: {str(e)}")


# --- Place Master CRUD (Update & Delete) ---

class PlaceUpdateRequest(BaseModel):
    name: str
    address: str
    is_default: bool = False


@router.put("/places/{place_id}")
async def update_place(place_id: int, request: PlaceUpdateRequest, user: dict = Depends(require_session)):
    """Update an existing meeting place."""
    try:
        def update():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                raise HTTPException(status_code=503, detail="Database unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    UPDATE places SET name = %s, address = %s, is_default = %s WHERE id = %s
                    RETURNING id, name, address, is_default, created_at
                """, (request.name, request.address, request.is_default, place_id))
                row = cursor.fetchone()
                conn.commit()
                if not row:
                    return None
                return {
                    "id": row["id"], "name": row["name"],
                    "address": row["address"], "is_default": row["is_default"],
                    "created_at": str(row["created_at"])
                }
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(thread_pool, update)
        if result is None:
            raise HTTPException(status_code=404, detail="Place not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating place {place_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/places/{place_id}")
async def delete_place(place_id: int, user: dict = Depends(require_session)):
    """Delete a meeting place by ID."""
    try:
        def delete():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                raise HTTPException(status_code=503, detail="Database unavailable")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("DELETE FROM places WHERE id = %s RETURNING id", (place_id,))
                row = cursor.fetchone()
                conn.commit()
                return row is not None
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        deleted = await loop.run_in_executor(thread_pool, delete)
        if not deleted:
            raise HTTPException(status_code=404, detail="Place not found")
        return {"message": "Place deleted successfully", "id": place_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting place {place_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Attendance Report CSV Export ---

@router.get("/reports/attendance/export")
async def export_attendance_csv():
    """Export attendance report as downloadable CSV."""
    from fastapi.responses import StreamingResponse

    try:
        def build_csv():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_MINUTES'))
            if not conn:
                return "No Data"
            cursor = get_pg_cursor(conn)
            try:
                lines = ["Section,Company Name,Meeting Type,Meeting Date,Director Name,DIN,Status,File Name"]

                # Detailed per-director attendance rows
                cursor.execute("""
                    SELECT ma.company_name, ma.meeting_type, ma.meeting_date,
                           ma.director_name, ma.din, ma.status, gm.file_path
                    FROM meeting_attendance ma
                    LEFT JOIN generated_minutes gm ON gm.id = ma.minutes_id
                    ORDER BY ma.id DESC LIMIT 1000
                """)
                for r in cursor.fetchall():
                    lines.append(f'"Attendance","{r["company_name"]}","{r["meeting_type"]}","{r["meeting_date"]}","{r["director_name"]}","{r["din"] or ""}","{r["status"]}","{r["file_path"] or ""}"')

                # Meeting list (also covers minutes generated before attendance tracking)
                cursor.execute("""
                    SELECT company_name, meeting_type, meeting_date, file_path 
                    FROM generated_minutes ORDER BY id DESC LIMIT 200
                """)
                for r in cursor.fetchall():
                    lines.append(f'"Meeting","{r["company_name"]}","{r["meeting_type"]}","{r["meeting_date"]}","","","","{r["file_path"]}"')
                return "\n".join(lines)
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        csv_content = await loop.run_in_executor(thread_pool, build_csv)

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendance_report.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting attendance CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

