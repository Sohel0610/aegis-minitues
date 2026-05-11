# Directors Disclosure Route Module
# This module handles directors disclosure functionality exclusively using PostgreSQL.
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
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
from routes.director_changes import log_director_change
from routes.director_family_info import get_family_info_for_director, update_director_family_info

# Import our PostgreSQL service
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for directors disclosure endpoints
router = APIRouter()

def _normalize_empty(value: Any) -> str:
    return str(value).strip() if value is not None else ""

def _is_meaningful(value: Any) -> bool:
    s = _normalize_empty(value).lower()
    return bool(s) and s not in {"n/a", "na", "none", "nil", "null", "0"}

# Response models for directors disclosure
class DirectorMasterResponse(BaseModel):
    id: int
    name: str
    din: str
    pan: Optional[str] = None
    din_status: Optional[str] = None
    gender: Optional[str] = None
    is_kmp: bool = False
    created_at: str

class DirectorsMasterResponse(BaseModel):
    data: List[DirectorMasterResponse]
    count: int

class DisclosureResponse(BaseModel):
    id: int
    director_name: str
    din: str
    pan: Optional[str] = None
    din_status: Optional[str] = None
    disclosure_date: str
    disclosure_type: str
    is_kmp: bool = False
    file_path: str
    all_files: Optional[List[Dict[str, Any]]] = None

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

class DocumentSummaryResponse(BaseModel):
    id: int
    director_name: str
    din: str
    file_path: str
    full_text: str
    summary: str
    created_at: str
    updated_at: str

class SummaryGenerationResponse(BaseModel):
    success: bool
    message: str
    summary: Optional[str] = None

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

class UpdateFamilyInfoRequest(BaseModel):
    section_2_77_i: Optional[str] = None
    section_2_77_ii: Optional[str] = None
    section_2_77_iii: Optional[str] = None
    family_members: List[FamilyMemberInfo]

class DirectorProfileResponse(BaseModel):
    name: str
    din: str
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    pan: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None

class DirectorProfileUpdateRequest(BaseModel):
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    pan: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None

class ImageUploadResponse(BaseModel):
    success: bool
    message: str
    image_url: Optional[str] = None

class ImageDeleteResponse(BaseModel):
    success: bool
    message: str

from pathlib import Path
import re

# Base path for generated documents (sync with disclosure_downloader.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "Director_Disclosure" / "Output_Disclosures"

def _get_all_physical_files_map() -> dict[str, list[dict]]:
    """
    Scans Output_Disclosures ONCE and returns a map of DIN -> [Files].
    This is much faster than scanning per-director.
    """
    din_map = {}
    if not BASE_DIR.exists():
        return din_map
        
    # Walk the current year's directory only to prevent duplicates from older years
    current_year_dir = BASE_DIR / "2024-25"
    if not current_year_dir.exists():
        return din_map

    for file_path in current_year_dir.rglob("*.docx"):
        fname = file_path.name
        # Process both MBP-1 and DIR-8 forms for the repository
        is_mbp1 = "MBP1" in fname.upper()
        is_dir8 = "DIR8" in fname.upper()
        if not (is_mbp1 or is_dir8):
            continue
            
        # Extract DIN using regex (looks for 8 digits in the filename)
        match = re.search(r'(\d{8})', fname)
        if match:
            din = match.group(1)
            rel_path = str(file_path.relative_to(BASE_DIR))
            mtime = file_path.stat().st_mtime
            
            # Extract company name from folder structure
            # Path is: 2024-25/Company/Type/File.docx (since we start from current_year_dir)
            # file_path.parent is Type (MBP-1/DIR-8), file_path.parent.parent is Company
            folder_name = file_path.parent.parent.name
            
            parts = fname.replace(".docx", "").split("_")
            company_hint = parts[-2] if len(parts) >= 3 else folder_name
            
            file_info = {
                "type": "MBP-1" if is_mbp1 else "DIR-8",
                "company_hint": company_hint,
                "folder_name": folder_name.replace("_", " "),
                "path": rel_path,
                "date": datetime.fromtimestamp(mtime).strftime("%d/%m/%Y"),
                "mtime": mtime
            }
            
            if din not in din_map:
                din_map[din] = []
            din_map[din].append(file_info)
            
    return din_map

@router.get("/directors-disclosures", response_model=DisclosuresResponse)
async def get_directors_disclosures():
    """
    Primary data source endpoint — pulls directly from the Falconebiz API-enriched
    directors_master.directors registry. Each director appears exactly once with
    their verified DIN, sync status, and profile details.
    MBP-1 document_summaries are preserved for summary/download features only.
    """
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not pg_conn: raise HTTPException(status_code=500, detail="DB connection failed")
    cursor = get_pg_cursor(pg_conn)
    try:
        cursor.execute("""
            SELECT
                d.id,
                d.name                                          AS director_name,
                d.din,
                COALESCE(d.din_status, 'Sync Pending')         AS din_status,
                d.gender,
                p.pan,
                d.last_api_sync,
                d.created_at,
                ds.file_path,
                ds.id                                           AS doc_id,
                EXISTS (
                    SELECT 1 FROM directors_master.external_board_members ea
                    WHERE TRIM(ea.din) = TRIM(d.din)
                    AND TRIM(UPPER(ea.designation)) IN (
                        'MANAGING DIRECTOR', 'CEO', 'CFO', 'COMPANY SECRETARY', 
                        'MANAGER', 'WHOLE-TIME DIRECTOR', 'WHOLETIME DIRECTOR'
                    )
                ) as is_kmp
            FROM directors_master.directors d
            LEFT JOIN directors_profile.directors_profile p
                   ON TRIM(p.din) = TRIM(d.din)
            LEFT JOIN LATERAL (
                SELECT id, file_path
                FROM directors_data.document_summaries
                WHERE TRIM(UPPER(director_name)) = TRIM(UPPER(d.name))
                   OR TRIM(din) = TRIM(d.din)
                ORDER BY created_at DESC
                LIMIT 1
            ) ds ON TRUE
            WHERE EXISTS (
                SELECT 1 FROM directors_master.external_board_members ea
                WHERE TRIM(ea.din) = TRIM(d.din)
            )
            ORDER BY d.name ASC
        """)
        rows = cursor.fetchall()

        # 1. Build a map of all physical files once
        physical_files_map = _get_all_physical_files_map()

        data = []
        for r in rows:
            din = r["din"]
            
            # 1. Determine base sync date
            sync_date = "N/A"
            if r["last_api_sync"]:
                sync_date = str(r["last_api_sync"])[:10]
            elif r["created_at"]:
                sync_date = str(r["created_at"])[:10]

            # 2. Check for physical MBP-1 file
            rel_path = ""
            doc_type = "Registry Sync"
            display_date = sync_date

            all_files = []
            if din and din in physical_files_map:
                # Get the latest MBP-1 file for this director for the main download button
                # Sort by mtime descending to get newest first
                sorted_files = sorted(physical_files_map[din], key=lambda x: x.get("mtime", 0), reverse=True)
                latest_file = sorted_files[0]
                rel_path = latest_file["path"]
                doc_type = "MBP-1"
                display_date = latest_file["date"]
                all_files = sorted_files

            # 3. Add exactly ONE entry per director
            data.append({
                "id":               r["id"],
                "director_name":    r["director_name"],
                "din":              din or "Pending Sync",
                "pan":              r["pan"] or "–",
                "din_status":       r["din_status"],
                "disclosure_date":  display_date,
                "disclosure_type":  doc_type,
                "is_kmp":           bool(r["is_kmp"]),
                "file_path":        rel_path,
                "all_files":        all_files
            })
        
        # Sort alphabetically by director name
        data.sort(key=lambda x: x["director_name"])

        return DisclosuresResponse(data=data, count=len(data))

    except Exception as e:
        logger.error(f"Error in disclosures fetch: {e}")
        import traceback; traceback.print_exc()
        return DisclosuresResponse(data=[], count=0)
    finally:
        cursor.close(); pg_conn.close()

@router.get("/directors-master", response_model=DirectorsMasterResponse) 
async def get_directors_master():
    """Get the master list of directors (PostgreSQL)."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not pg_conn: raise HTTPException(status_code=500, detail="DB connection failed")
    cursor = get_pg_cursor(pg_conn)
    try:
        cursor.execute("""
            SELECT d.id, d.name, d.din, d.created_at, d.din_status, d.gender, p.pan,
                   EXISTS (
                       SELECT 1 FROM directors_master.external_board_members ea
                       WHERE TRIM(ea.din) = TRIM(d.din)
                       AND TRIM(UPPER(ea.designation)) IN (
                           'MANAGING DIRECTOR', 'CEO', 'CFO', 'COMPANY SECRETARY', 
                           'MANAGER', 'WHOLE-TIME DIRECTOR', 'WHOLETIME DIRECTOR'
                       )
                   ) as is_kmp
            FROM directors_master.directors d
            LEFT JOIN directors_profile.directors_profile p ON TRIM(d.din) = TRIM(p.din)
            ORDER BY d.name
        """)
        rows = cursor.fetchall()
        data = []
        for r in rows:
            data.append({
                "id": r["id"],
                "name": r["name"],
                "din": r["din"] or "N/A",
                "pan": r["pan"],
                "din_status": r["din_status"],
                "gender": r["gender"],
                "is_kmp": bool(r["is_kmp"]),
                "created_at": r["created_at"].isoformat() if r["created_at"] else datetime.now().isoformat()
            })
        return DirectorsMasterResponse(data=data, count=len(data))
    finally:
        cursor.close(); pg_conn.close()

@router.get("/directors-disclosures/{id}/summary", response_model=DocumentSummaryResponse)
async def get_disclosure_summary(id: int):
    """Fetch individual summary for a disclosure."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not pg_conn: raise HTTPException(status_code=500)
    cursor = get_pg_cursor(pg_conn)
    try:
        cursor.execute("SELECT * FROM directors_data.document_summaries WHERE id = %s", (id,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Disclosure not found")
        return {**row, "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}
    finally:
        cursor.close(); pg_conn.close()

@router.get("/directors-disclosures/{id}/download")
async def download_disclosure_file(id: int):
    """Download the actual disclosure DOCX file."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not pg_conn: raise HTTPException(status_code=500)
    cursor = get_pg_cursor(pg_conn)
    try:
        cursor.execute("SELECT file_path FROM directors_data.document_summaries WHERE id = %s", (id,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404)
        
        fname = os.path.basename(row["file_path"])
        
        # Primary paths
        search_paths = [
            os.path.join(os.path.dirname(__file__), "..", "uploads", fname),
            os.path.join(os.path.dirname(__file__), "..", "public", "Directors Discloser Output", fname),
            os.path.join(os.path.dirname(__file__), "..", "public", "templates", fname),
            os.path.join(os.path.dirname(__file__), "..", "..", "Director_Disclosure", "Output_Disclosures")
        ]
        
        # Try direct path matches first
        for p in search_paths:
            if os.path.exists(p) and os.path.isfile(p):
                return FileResponse(path=p, filename=fname, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        # Recursive search in Output_Disclosures if not found
        output_root = os.path.join(os.path.dirname(__file__), "..", "..", "Director_Disclosure", "Output_Disclosures")
        if os.path.exists(output_root):
            for root, dirs, files in os.walk(output_root):
                if fname in files:
                    full_path = os.path.join(root, fname)
                    return FileResponse(path=full_path, filename=fname, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        raise HTTPException(status_code=404, detail=f"Physical file {fname} not found on server")
    finally:
        cursor.close(); pg_conn.close()

@router.post("/directors-master", response_model=DirectorMasterResponse)
async def create_director(request: DirectorCreateRequest):
    """Create a new director in PostgreSQL."""
    try:
        def insert_director():
            pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
            if not pg_conn:
                 raise Exception("Database connection failed")
            cursor = get_pg_cursor(pg_conn)
            try:
                cursor.execute("SELECT id FROM directors_master.directors WHERE din = %s", (request.din,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Director with this DIN already exists")

                cursor.execute(
                    "INSERT INTO directors_master.directors (name, din) VALUES (%s, %s) RETURNING id, name, din, created_at",
                    (request.name, request.din),
                )
                row = cursor.fetchone()
                pg_conn.commit()
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "din": row["din"],
                    "pan": None,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else datetime.now().isoformat(),
                }
            finally:
                cursor.close()
                pg_conn.close()
        
        loop = asyncio.get_event_loop()
        director_data = await loop.run_in_executor(thread_pool, insert_director)
        return DirectorMasterResponse(**director_data)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Error creating director: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/directors-master/{director_id}", response_model=DirectorMasterResponse)
async def update_director(director_id: int, request: DirectorUpdateRequest):
    """Update an existing director in PostgreSQL."""
    try:
        def update_director_data():
            pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
            if not pg_conn:
                 raise Exception("Database connection failed")
            cursor = get_pg_cursor(pg_conn)
            try:
                cursor.execute("SELECT id FROM directors_master.directors WHERE id = %s", (director_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Director not found")

                cursor.execute(
                    "SELECT id FROM directors_master.directors WHERE din = %s AND id != %s",
                    (request.din, director_id),
                )
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Another director with this DIN already exists")

                cursor.execute(
                    "UPDATE directors_master.directors SET name = %s, din = %s WHERE id = %s RETURNING id, name, din, created_at",
                    (request.name, request.din, director_id),
                )
                row = cursor.fetchone()
                pg_conn.commit()
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "din": row["din"],
                    "pan": None,
                    "created_at": row["created_at"].isoformat() if row["created_at"] else datetime.now().isoformat(),
                }
            finally:
                cursor.close()
                pg_conn.close()
        
        loop = asyncio.get_event_loop()
        director = await loop.run_in_executor(thread_pool, update_director_data)
        return DirectorMasterResponse(**director)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Error updating director: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/directors-master/{director_id}")
async def delete_director(director_id: int):
    """Delete a director from PostgreSQL."""
    try:
        def delete_director_data():
            pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
            if not pg_conn:
                 raise Exception("Database connection failed")
            cursor = get_pg_cursor(pg_conn)
            try:
                cursor.execute("SELECT id FROM directors_master.directors WHERE id = %s", (director_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Director not found")
                cursor.execute("DELETE FROM directors_master.directors WHERE id = %s", (director_id,))
                pg_conn.commit()
            finally:
                cursor.close()
                pg_conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, delete_director_data)
        return {"message": "Director deleted successfully"}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Error deleting director: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/directors-master/{director_id}/pan")
async def update_director_pan(director_id: int, request: DirectorPanUpdateRequest):
    """Update PAN for a director in PostgreSQL."""
    try:
        def upsert_pan():
            pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
            if not pg_conn:
                 raise Exception("Database connection failed")
            cursor = get_pg_cursor(pg_conn)
            try:
                cursor.execute("SELECT din FROM directors_master.directors WHERE id = %s", (director_id,))
                row = cursor.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Director not found")
                din = (row["din"] or "").strip()
                if not din:
                    raise HTTPException(status_code=400, detail="Director DIN is empty")

                cursor.execute("""
                    INSERT INTO directors_profile.directors_profile (din, pan)
                    VALUES (TRIM(%s), TRIM(%s))
                    ON CONFLICT (din) DO UPDATE SET pan = EXCLUDED.pan
                """, (din, request.pan.strip()))
                pg_conn.commit()
            finally:
                cursor.close()
                pg_conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, upsert_pan)
        return {"message": "PAN updated successfully"}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Error updating PAN: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# DISCLOSURE ANALYTICS & DOCUMENTS - PG
# ---------------------------------------------------------

@router.get("/directors-disclosures/analytics", response_model=DisclosureAnalyticsResponse)
async def get_disclosure_analytics():
    """Get disclosure analytics from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not pg_conn:
        raise HTTPException(status_code=500, detail="DB connection failed")
    cursor = get_pg_cursor(pg_conn)
    try:
        cursor.execute("SELECT COUNT(*) AS total_count FROM directors_data.document_summaries")
        res = cursor.fetchone()
        total = int(res["total_count"]) if res else 0
        
        cursor.execute("SELECT 'MBP-1' as type, COUNT(*) as count FROM directors_data.document_summaries group by 1")
        by_type = [{"label": r["type"], "value": int(r["count"])} for r in cursor.fetchall()]
        
        # Real Association Trend from Registry
        cursor.execute("""
            SELECT TO_CHAR(appointment_date, 'Mon YYYY') as month, COUNT(*) as count 
            FROM directors_master.external_associations 
            WHERE appointment_date IS NOT NULL
            GROUP BY 1 ORDER BY MIN(appointment_date) DESC LIMIT 12
        """)
        rows = cursor.fetchall()
        # Ensure chronological order (ASC after DESC limit)
        by_month = [{"month": r["month"], "count": int(r["count"])} for r in reversed(rows)]
        
        cursor.execute("""
            SELECT director_name as label, COUNT(*) as count 
            FROM directors_data.document_summaries 
            GROUP BY 1 ORDER BY count DESC LIMIT 10
        """)
        by_director = [{"label": r["label"], "value": int(r["count"])} for r in cursor.fetchall()]
        
        return {
            "total_disclosures": total,
            "by_type": by_type,
            "by_month": by_month,
            "by_director": by_director
        }
    finally:
        cursor.close()
        pg_conn.close()

# ---------------------------------------------------------
# DIRECTOR PROFILE & FAMILY - PG
# ---------------------------------------------------------

@router.get("/directors-profile/{din}", response_model=DirectorProfileResponse)
async def get_director_profile(din: str):
    """Get director profile from PostgreSQL."""
    try:
        def fetch_profile():
            pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
            if not pg_conn: raise Exception("No DB connection")
            cursor = get_pg_cursor(pg_conn)
            try:
                cursor.execute("""
                    SELECT name_of_director, din, address, date_of_birth, pan, qualification, experience
                    FROM directors_profile.directors_profile WHERE din = %s
                """, (din,))
                row = cursor.fetchone()
                if not row: raise HTTPException(status_code=404, detail="Profile not found")
                return {
                    "name": row["name_of_director"] or "",
                    "din": row["din"] or "",
                    "address": row["address"],
                    "date_of_birth": row["date_of_birth"].strftime("%Y-%m-%d") if row["date_of_birth"] and hasattr(row["date_of_birth"], 'strftime') else str(row["date_of_birth"]) if row["date_of_birth"] else None,
                    "pan": row["pan"],
                    "qualification": row["qualification"],
                    "experience": row["experience"],
                }
            finally:
                cursor.close(); pg_conn.close()
        loop = asyncio.get_event_loop()
        profile = await loop.run_in_executor(thread_pool, fetch_profile)
        return DirectorProfileResponse(**profile)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/directors-profile/{din}", response_model=DirectorProfileResponse)
async def update_director_profile(din: str, request: DirectorProfileUpdateRequest):
    """Update director profile in PostgreSQL."""
    try:
        def update_profile_data():
            pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
            if not pg_conn: raise Exception("No DB connection")
            cursor = get_pg_cursor(pg_conn)
            try:
                update_fields = []
                values = []
                for field, val in (('address', request.address), ('date_of_birth', request.date_of_birth), 
                                   ('pan', request.pan), ('qualification', request.qualification), ('experience', request.experience)):
                    if val is not None:
                        update_fields.append(f"{field} = %s"); values.append(val)
                if not update_fields: raise HTTPException(status_code=400, detail="No fields to update")
                values.append(din)
                cursor.execute(f"UPDATE directors_profile.directors_profile SET {', '.join(update_fields)} WHERE din = %s", values)
                pg_conn.commit()

                cursor.execute("""
                    SELECT name_of_director, din, address, date_of_birth, pan, qualification, experience
                    FROM directors_profile.directors_profile WHERE din = %s
                """, (din,))
                row = cursor.fetchone()
                return {
                    "name": row["name_of_director"] or "",
                    "din": row["din"] or "",
                    "address": row["address"],
                    "date_of_birth": row["date_of_birth"].strftime("%Y-%m-%d") if row["date_of_birth"] and hasattr(row["date_of_birth"], 'strftime') else str(row["date_of_birth"]) if row["date_of_birth"] else None,
                    "pan": row["pan"],
                    "qualification": row["qualification"],
                    "experience": row["experience"],
                }
            finally:
                cursor.close(); pg_conn.close()
        loop = asyncio.get_event_loop()
        profile = await loop.run_in_executor(thread_pool, update_profile_data)
        return DirectorProfileResponse(**profile)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Family info is now handled exclusively in director_family_info.py to avoid route conflicts

# ---------------------------------------------------------
# DOCUMENT PROCESSING & SUMMARY - PG
# ---------------------------------------------------------

@router.get("/directors-disclosures/summaries", response_model=List[DocumentSummaryResponse])
async def get_all_summaries():
    """Get all processed document summaries from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not pg_conn: raise HTTPException(status_code=500)
    cursor = get_pg_cursor(pg_conn)
    try:
        cursor.execute("SELECT id, director_name, din, file_path, full_text, summary, created_at, updated_at FROM directors_data.document_summaries ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [{**row, "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()} for row in rows]
    finally:
        cursor.close(); pg_conn.close()

@router.post("/directors-disclosures/upload")
async def upload_disclosure_form(director_name: str, din: str, file: UploadFile = File(...)):
    """Upload and process disclosure form (PG Meta Store)."""
    try:
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{din}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Parse text (Docx context)
        doc = DocxDocument(file_path)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        
        # Store in PG
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            try:
                cursor.execute("""
                    INSERT INTO directors_data.document_summaries (director_name, din, file_path, full_text, summary)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (din) DO UPDATE SET 
                        full_text = EXCLUDED.full_text,
                        file_path = EXCLUDED.file_path,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (director_name, din, file_path, full_text, "Processing..."))
                pg_conn.commit()
            finally:
                cursor.close(); pg_conn.close()
        
        return {"id": din, "message": "File uploaded and queued for analysis"}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# IMAGES & TEMPLATES (FS BASED)
# ---------------------------------------------------------

@router.get("/directors-profile/{din}/image")
async def get_director_image(din: str):
    images_dir = os.path.join(os.path.dirname(__file__), "..", "director_images")
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        p = os.path.join(images_dir, f"{din}{ext}")
        if os.path.exists(p): return FileResponse(p)
    
    # Silent Fallback to default avatar to clean up terminal logs
    default_avatar = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Frontend", "public", "avatar.jpg")
    if os.path.exists(default_avatar):
        return FileResponse(default_avatar)
        
    raise HTTPException(status_code=404)

@router.get("/directors-disclosures/templates/{template_name}")
async def download_template(template_name: str):
    """Serve the empty templates for DIR-8 and MBP-1."""
    # Look in the newly created Templates directory
    template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Director_Disclosure", "Templates")
    p = os.path.join(template_dir, template_name)
    
    # Try with _Template suffix if direct match fails
    if not os.path.exists(p):
        fname = template_name.replace(".docx", "_Template.docx")
        p = os.path.join(template_dir, fname)
        
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="Template not found")
        
    return FileResponse(p, filename=template_name)

# Ensure legacy naming for Minutes route
@router.get("/directors-for-minutes", response_model=DirectorsMasterResponse)
async def get_directors_for_minutes():
    return await get_directors_master()
