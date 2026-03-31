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
from docx import Document
import shutil
from utils.pgsql_service import get_pg_connection, get_pg_cursor

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

# --- Database Init ---

def init_minutes_pg():
    """Initialize minutes tables in PostgreSQL."""
    conn = get_pg_connection()
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
                    template_name TEXT,
                    resolution_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Compliance Table
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
            conn.commit()
            logger.info("Minutes PostgreSQL tables initialized")
        except Exception as e:
            conn.rollback()
            logger.error(f"Minutes init failed: {e}")
        finally:
            conn.close()

# --- Generated Minutes Endpoints ---

@router.get("/generated-minutes", response_model=MinutesHistoryResponse)
async def get_history():
    try:
        def fetch():
            conn = get_pg_connection()
            if not conn: return []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, company_name, meeting_type, meeting_date, file_path, created_at FROM generated_minutes ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [GeneratedMinuteResponse(id=r['id'], company_name=r['company_name'], meeting_type=r['meeting_type'], 
                                              meeting_date=r['meeting_date'], file_path=r['file_path'], created_at=str(r['created_at']), 
                                              download_url=f"/api/generated-minutes/download/{r['file_path']}") for r in rows]
            finally:
                conn.close()
        h = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return MinutesHistoryResponse(data=h, count=len(h))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/generated-minutes/{id}")
async def delete_minute(id: int):
    try:
        def delete():
            conn = get_pg_connection()
            if not conn: return False
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
        success = await asyncio.get_event_loop().run_in_executor(thread_pool, delete)
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
            conn = get_pg_connection()
            if not conn: return []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, name, address, is_default, created_at FROM places ORDER BY name")
                rows = cursor.fetchall()
                return [PlaceResponse(id=r['id'], name=r['name'], address=r['address'], is_default=r['is_default'], created_at=str(r['created_at'])) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return PlacesListResponse(data=data, count=len(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Compliance Endpoints ---

@router.get("/compliances", response_model=CompliancesList)
async def get_compliances():
    try:
        def fetch():
            conn = get_pg_connection()
            if not conn: return []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, form, description, due_date, status, priority, created_at FROM compliances ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [ComplianceResponse(id=r['id'], form=r['form'], description=r['description'],
                                          due_date=r['due_date'], status=r['status'], priority=r['priority'],
                                          created_at=str(r['created_at'])) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return CompliancesList(data=data, count=len(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliances", response_model=ComplianceResponse)
async def create_compliance(request: ComplianceCreate):
    try:
        def insert():
            conn = get_pg_connection()
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
        return await asyncio.get_event_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Resolution Endpoints ---

@router.get("/resolutions", response_model=ResolutionTemplatesList)
async def get_resolutions():
    try:
        def fetch():
            conn = get_pg_connection()
            if not conn: return []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, template_name, resolution_text, created_at FROM resolution_templates ORDER BY template_name")
                rows = cursor.fetchall()
                return [ResolutionTemplateResponse(id=r['id'], template_name=r['template_name'], resolution_text=r['resolution_text'], created_at=str(r['created_at'])) for r in rows]
            finally:
                conn.close()
        data = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return ResolutionTemplatesList(data=data, count=len(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))