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
from routes.director_changes import log_director_change

# Import our PostgreSQL service
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for directors disclosure endpoints
router = APIRouter()

def _sqlite_public_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "..", "public", filename)

def _sqlite_directors_db_path() -> str:
    return _sqlite_public_path("directors.db")

def _sqlite_directors_profile_db_path() -> str:
    return _sqlite_public_path("directors_profile.db")

def _sqlite_family_info_db_path() -> str:
    return _sqlite_public_path("Director_Family_Information.db")

def _sqlite_directors_data_db_path() -> str:
    # This SQLite DB lives alongside fastapi_server.py (not under public/)
    return os.path.join(os.path.dirname(__file__), "..", "directors_data.db")

def _normalize_empty(value: Any) -> str:
    return str(value).strip() if value is not None else ""

def _sqlite_row_get(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    try:
        return row[key]
    except Exception:
        return default

def _is_meaningful(value: Any) -> bool:
    s = _normalize_empty(value).lower()
    return bool(s) and s not in {"n/a", "na", "none", "nil", "null", "0"}

def _ensure_sqlite_directors_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS directors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                din TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_directors_din ON directors(din)")
        conn.commit()
    finally:
        cur.close()

def _fetch_directors_master_sqlite() -> List[Dict[str, Any]]:
    directors_db_path = _sqlite_directors_db_path()
    profile_db_path = _sqlite_directors_profile_db_path()

    if not os.path.exists(directors_db_path):
        return []

    # Load PANs from directors_profile.db (if present)
    pans_by_din: Dict[str, Optional[str]] = {}
    if os.path.exists(profile_db_path):
        pconn = sqlite3.connect(profile_db_path)
        pconn.row_factory = sqlite3.Row
        pcur = pconn.cursor()
        try:
            pcur.execute("SELECT DIN, PAN FROM directors_profile WHERE DIN IS NOT NULL")
            for r in pcur.fetchall():
                din = _normalize_empty(r["DIN"])
                if din:
                    pans_by_din[din] = r["PAN"]
        except Exception:
            # Best-effort: if the profile DB/table isn't available, we still return directors without PAN.
            pans_by_din = {}
        finally:
            try:
                pcur.close()
            finally:
                pconn.close()

    conn = sqlite3.connect(directors_db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_sqlite_directors_schema(conn)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, din, created_at FROM directors ORDER BY name")
            rows = cur.fetchall()
            directors: List[Dict[str, Any]] = []
            for row in rows:
                din = _normalize_empty(row["din"])
                directors.append({
                    "id": int(row["id"]),
                    "name": row["name"],
                    "din": din,
                    "pan": pans_by_din.get(din),
                    "created_at": _normalize_empty(row["created_at"]) or datetime.now().isoformat(),
                })
            return directors
        finally:
            cur.close()
    finally:
        conn.close()

def _upsert_director_pan_sqlite(din: str, pan: str, director_name: Optional[str] = None) -> None:
    profile_db_path = _sqlite_directors_profile_db_path()
    if not os.path.exists(profile_db_path):
        raise HTTPException(status_code=500, detail="SQLite directors_profile.db not found")

    conn = sqlite3.connect(profile_db_path)
    try:
        cur = conn.cursor()
        try:
            cur.execute("UPDATE directors_profile SET PAN = ? WHERE DIN = ?", (pan, din))
            if cur.rowcount == 0:
                # Insert minimal profile row if DIN doesn't exist yet.
                cur.execute(
                    "INSERT INTO directors_profile (DIN, PAN, Name_of_Director) VALUES (?, ?, ?)",
                    (din, pan, director_name or ""),
                )
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()

def _get_director_row_sqlite(director_id: int) -> Optional[sqlite3.Row]:
    directors_db_path = _sqlite_directors_db_path()
    if not os.path.exists(directors_db_path):
        return None
    conn = sqlite3.connect(directors_db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_sqlite_directors_schema(conn)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, din, created_at FROM directors WHERE id = ?", (director_id,))
            return cur.fetchone()
        finally:
            cur.close()
    finally:
        conn.close()

def _create_director_sqlite(name: str, din: str) -> Dict[str, Any]:
    directors_db_path = _sqlite_directors_db_path()
    conn = sqlite3.connect(directors_db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_sqlite_directors_schema(conn)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM directors WHERE din = ?", (din,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Director with this DIN already exists")
            cur.execute(
                "INSERT INTO directors (name, din, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (name, din),
            )
            new_id = cur.lastrowid
            conn.commit()
            cur.execute("SELECT id, name, din, created_at FROM directors WHERE id = ?", (new_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to create director")
            return {
                "id": int(row["id"]),
                "name": row["name"],
                "din": _normalize_empty(row["din"]),
                "pan": None,
                "created_at": _normalize_empty(row["created_at"]) or datetime.now().isoformat(),
            }
        finally:
            cur.close()
    finally:
        conn.close()

def _update_director_sqlite(director_id: int, name: str, din: str) -> Dict[str, Any]:
    directors_db_path = _sqlite_directors_db_path()
    if not os.path.exists(directors_db_path):
        raise HTTPException(status_code=404, detail="Director not found")
    conn = sqlite3.connect(directors_db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_sqlite_directors_schema(conn)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM directors WHERE id = ?", (director_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Director not found")
            cur.execute("SELECT id FROM directors WHERE din = ? AND id != ?", (din, director_id))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Another director with this DIN already exists")
            cur.execute("UPDATE directors SET name = ?, din = ? WHERE id = ?", (name, din, director_id))
            conn.commit()
            cur.execute("SELECT id, name, din, created_at FROM directors WHERE id = ?", (director_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Director not found")
            return {
                "id": int(row["id"]),
                "name": row["name"],
                "din": _normalize_empty(row["din"]),
                "pan": None,
                "created_at": _normalize_empty(row["created_at"]) or datetime.now().isoformat(),
            }
        finally:
            cur.close()
    finally:
        conn.close()

def _delete_director_sqlite(director_id: int) -> None:
    directors_db_path = _sqlite_directors_db_path()
    if not os.path.exists(directors_db_path):
        raise HTTPException(status_code=404, detail="Director not found")
    conn = sqlite3.connect(directors_db_path)
    try:
        _ensure_sqlite_directors_schema(conn)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM directors WHERE id = ?", (director_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Director not found")
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()

def _fetch_family_info_sqlite(director_name: str) -> Optional[Dict[str, Any]]:
    db_path = _sqlite_family_info_db_path()
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute('SELECT Name FROM Sheet1 WHERE Name IS NOT NULL ORDER BY Name')
        names = [r["Name"] for r in cur.fetchall() if _is_meaningful(r["Name"])]
        best_match = None
        best_score = 0.0
        for n in names:
            score = indian_name_similarity(director_name, n)
            if score > best_score and score >= 0.5:
                best_score = score
                best_match = n

        if not best_match:
            return None

        cur.execute('SELECT * FROM Sheet1 WHERE Name = ? LIMIT 1', (best_match,))
        row = cur.fetchone()
        if not row:
            return None

        relationships = [
            ("Father", _sqlite_row_get(row, "Father"), _sqlite_row_get(row, "Father_PAN")),
            ("Mother", _sqlite_row_get(row, "Mother"), _sqlite_row_get(row, "Mother_PAN")),
            ("Son", _sqlite_row_get(row, "Son"), None),
            ("Son's Wife", _sqlite_row_get(row, "Son's_Wife"), None),
            ("Daughter", _sqlite_row_get(row, "Daughter"), None),
            ("Daughter's Husband", _sqlite_row_get(row, "Daughter's_husband"), None),
            ("Brother", _sqlite_row_get(row, "Brother"), None),
            ("Sister", _sqlite_row_get(row, "Sister"), None),
        ]

        family_members: List[Dict[str, Any]] = []
        for rel, details, pan_no in relationships:
            if _is_meaningful(details) or _is_meaningful(pan_no):
                family_members.append({
                    "relationship": rel,
                    "details": _normalize_empty(details),
                    "pan_number": _normalize_empty(pan_no) if _is_meaningful(pan_no) else None,
                })

        section_2_77_iii = _sqlite_row_get(row, "Section_2(77)(iii)")
        return {
            "director_name": director_name,
            "matched_family_name": best_match,
            "match_score": round(float(best_score), 2),
            "section_2_77_i": _sqlite_row_get(row, "Section_2(77)(i)"),
            "section_2_77_ii": _sqlite_row_get(row, "Section_2(77)(ii)"),
            "section_2_77_iii": str(section_2_77_iii) if section_2_77_iii is not None else None,
            "family_members": family_members,
        }
    except Exception as e:
        logger.warning(f"SQLite family info fetch failed: {e}")
        return None
    finally:
        try:
            cur.close()
        finally:
            conn.close()

def _upsert_family_info_sqlite(director_name: str, request: "UpdateFamilyInfoRequest") -> Optional[Dict[str, Any]]:
    db_path = _sqlite_family_info_db_path()
    if not os.path.exists(db_path):
        raise HTTPException(status_code=500, detail="SQLite Director_Family_Information.db not found")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # Find best match first (same behavior as GET)
        cur.execute('SELECT Name FROM Sheet1 WHERE Name IS NOT NULL ORDER BY Name')
        names = [r["Name"] for r in cur.fetchall() if _is_meaningful(r["Name"])]
        best_match = None
        best_score = 0.0
        for n in names:
            score = indian_name_similarity(director_name, n)
            if score > best_score and score >= 0.5:
                best_score = score
                best_match = n

        target_name = best_match or director_name

        # Ensure row exists
        cur.execute('SELECT 1 FROM Sheet1 WHERE Name = ? LIMIT 1', (target_name,))
        if not cur.fetchone():
            cur.execute('INSERT INTO Sheet1 ("Name") VALUES (?)', (target_name,))

        # Update sections
        cur.execute(
            'UPDATE Sheet1 SET "Section_2(77)(i)" = ?, "Section_2(77)(ii)" = ?, "Section_2(77)(iii)" = ? WHERE "Name" = ?',
            (
                request.section_2_77_i,
                request.section_2_77_ii,
                request.section_2_77_iii,
                target_name,
            ),
        )

        rel_to_col = {
            "Father": ("Father", "Father_PAN"),
            "Mother": ("Mother", "Mother_PAN"),
            "Son": ("Son", None),
            "Son's Wife": ("Son's_Wife", None),
            "Daughter": ("Daughter", None),
            "Daughter's Husband": ("Daughter's_husband", None),
            "Brother": ("Brother", None),
            "Sister": ("Sister", None),
        }

        for member in request.family_members:
            mapping = rel_to_col.get(member.relationship)
            if not mapping:
                continue
            details_col, pan_col = mapping

            cur.execute(f'UPDATE Sheet1 SET "{details_col}" = ? WHERE "Name" = ?', (member.details, target_name))
            if pan_col and member.pan_number is not None:
                cur.execute(f'UPDATE Sheet1 SET "{pan_col}" = ? WHERE "Name" = ?', (member.pan_number, target_name))

        conn.commit()

        # Return updated view (reuse GET-like output but for target row)
        cur.execute('SELECT * FROM Sheet1 WHERE Name = ? LIMIT 1', (target_name,))
        row = cur.fetchone()
        if not row:
            return None

        relationships = [
            ("Father", _sqlite_row_get(row, "Father"), _sqlite_row_get(row, "Father_PAN")),
            ("Mother", _sqlite_row_get(row, "Mother"), _sqlite_row_get(row, "Mother_PAN")),
            ("Son", _sqlite_row_get(row, "Son"), None),
            ("Son's Wife", _sqlite_row_get(row, "Son's_Wife"), None),
            ("Daughter", _sqlite_row_get(row, "Daughter"), None),
            ("Daughter's Husband", _sqlite_row_get(row, "Daughter's_husband"), None),
            ("Brother", _sqlite_row_get(row, "Brother"), None),
            ("Sister", _sqlite_row_get(row, "Sister"), None),
        ]
        family_members: List[Dict[str, Any]] = []
        for rel, details, pan_no in relationships:
            if _is_meaningful(details) or _is_meaningful(pan_no):
                family_members.append({
                    "relationship": rel,
                    "details": _normalize_empty(details),
                    "pan_number": _normalize_empty(pan_no) if _is_meaningful(pan_no) else None,
                })

        section_2_77_iii = _sqlite_row_get(row, "Section_2(77)(iii)")
        return {
            "director_name": director_name,
            "matched_family_name": target_name,
            "match_score": round(float(best_score if best_match else 1.0), 2),
            "section_2_77_i": _sqlite_row_get(row, "Section_2(77)(i)"),
            "section_2_77_ii": _sqlite_row_get(row, "Section_2(77)(ii)"),
            "section_2_77_iii": str(section_2_77_iii) if section_2_77_iii is not None else None,
            "family_members": family_members,
        }
    finally:
        try:
            cur.close()
        finally:
            conn.close()

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

# Endpoint to get all directors from PostgreSQL database
@router.get("/directors-master", response_model=DirectorsMasterResponse)
async def get_directors_master():
    """Get all directors from PostgreSQL master table (fallback to SQLite)."""
    try:
        def fetch_directors():
            pg_conn = None
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        # Fetch directors with their latest PAN from profiles if available
                        cursor.execute("""
                            SELECT 
                                d.id, d.name, d.din, d.created_at,
                                p.pan
                            FROM directors_master.directors d
                            LEFT JOIN directors_profile.directors_profile p ON d.din = p.din
                            ORDER BY d.name
                        """)

                        rows = cursor.fetchall()
                        directors = []
                        for row in rows:
                            directors.append({
                                "id": row["id"],
                                "name": row["name"],
                                "din": row["din"],
                                "pan": row["pan"],
                                "created_at": row["created_at"].isoformat() if row["created_at"] else datetime.now().isoformat(),
                            })
                        return directors
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except Exception as e:
                logger.warning(f"Directors master PG fetch failed, falling back to SQLite: {e}")
            finally:
                if pg_conn:
                    try:
                        pg_conn.close()
                    except Exception:
                        pass

            return _fetch_directors_master_sqlite()
        
        loop = asyncio.get_event_loop()
        directors = await loop.run_in_executor(thread_pool, fetch_directors)
        
        return DirectorsMasterResponse(
            data=[DirectorMasterResponse(**d) for d in directors],
            count=len(directors)
        )
    except Exception as e:
        logger.error(f"Error fetching directors master from PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch directors: {str(e)}")

# Endpoint to create a new director in PostgreSQL
@router.post("/directors-master", response_model=DirectorMasterResponse)
async def create_director(request: DirectorCreateRequest):
    """Create a new director in PostgreSQL master table (fallback to SQLite)."""
    try:
        def insert_director():
            pg_conn = None
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        # Check if director with same DIN already exists
                        cursor.execute("SELECT id FROM directors_master.directors WHERE din = %s", (request.din,))
                        if cursor.fetchone():
                            raise HTTPException(status_code=400, detail="Director with this DIN already exists")

                        # Insert new director
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
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Create director PG insert failed, falling back to SQLite: {e}")
            finally:
                if pg_conn:
                    try:
                        pg_conn.close()
                    except Exception:
                        pass

            return _create_director_sqlite(request.name, request.din)
        
        loop = asyncio.get_event_loop()
        director_data = await loop.run_in_executor(thread_pool, insert_director)
        
        return DirectorMasterResponse(**director_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating director in PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create director: {str(e)}")

# Endpoint to update an existing director in PostgreSQL
@router.put("/directors-master/{director_id}", response_model=DirectorMasterResponse)
async def update_director(director_id: int, request: DirectorUpdateRequest):
    """Update an existing director in PostgreSQL master table (fallback to SQLite)."""
    try:
        def update_director_data():
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
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
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Update director PG update failed, falling back to SQLite: {e}")

            return _update_director_sqlite(director_id, request.name, request.din)
        
        loop = asyncio.get_event_loop()
        director = await loop.run_in_executor(thread_pool, update_director_data)
        
        return DirectorMasterResponse(**director)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating director in PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update director: {str(e)}")

# Endpoint to update PAN for a director
@router.put("/directors-master/{director_id}/pan")
async def update_director_pan(director_id: int, request: DirectorPanUpdateRequest):
    """Update PAN for a director in PostgreSQL (fallback to SQLite)."""
    try:
        def upsert_pan():
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        cursor.execute("SELECT din FROM directors_master.directors WHERE id = %s", (director_id,))
                        row = cursor.fetchone()
                        if not row:
                            raise HTTPException(status_code=404, detail="Director not found")

                        din = (row["din"] or "").strip()
                        if not din:
                            raise HTTPException(status_code=400, detail="Director DIN is empty; cannot set PAN")

                        cursor.execute("""
                            INSERT INTO directors_profile.directors_profile (din, pan)
                            VALUES (%s, %s)
                            ON CONFLICT (din) DO UPDATE SET pan = EXCLUDED.pan
                        """, (din, request.pan.strip()))

                        pg_conn.commit()
                        return
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Update PAN PG upsert failed, falling back to SQLite: {e}")

            director_row = _get_director_row_sqlite(director_id)
            if not director_row:
                raise HTTPException(status_code=404, detail="Director not found")
            din = _normalize_empty(director_row["din"])
            if not din:
                raise HTTPException(status_code=400, detail="Director DIN is empty; cannot set PAN")
            _upsert_director_pan_sqlite(din=din, pan=request.pan.strip(), director_name=_normalize_empty(director_row["name"]))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, upsert_pan)
        return {"message": "PAN updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating director PAN: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update director PAN: {str(e)}")

# Endpoint to delete a director from PostgreSQL
@router.delete("/directors-master/{director_id}")
async def delete_director(director_id: int):
    """Delete a director from PostgreSQL master table (fallback to SQLite)."""
    try:
        def delete_director_data():
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        cursor.execute("SELECT id FROM directors_master.directors WHERE id = %s", (director_id,))
                        if not cursor.fetchone():
                            raise HTTPException(status_code=404, detail="Director not found")

                        cursor.execute("DELETE FROM directors_master.directors WHERE id = %s", (director_id,))
                        pg_conn.commit()
                        return
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Delete director PG delete failed, falling back to SQLite: {e}")

            _delete_director_sqlite(director_id)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, delete_director_data)
        
        return {"message": "Director deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting director from PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete director: {str(e)}")

# Endpoint to get all directors' disclosures from Word files
@router.get("/directors-disclosures", response_model=DisclosuresResponse)
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
@router.get("/directors-disclosures/{disclosure_id}/content", response_model=DisclosureContentResponse)
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
@router.get("/directors-disclosures/{disclosure_id}/download")
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
@router.get("/directors-disclosures/analytics", response_model=DisclosureAnalyticsResponse)
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
@router.post("/directors-disclosures/{disclosure_id}/generate-summary", response_model=SummaryGenerationResponse)
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
@router.get("/directors-disclosures/{disclosure_id}/summary", response_model=DocumentSummaryResponse)
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

            # Try PostgreSQL first
            pg_conn = None
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        cursor.execute("""
                            SELECT id, director_name, din, file_path, full_text, summary, created_at, updated_at
                            FROM directors_data.document_summaries
                            WHERE file_path = %s
                        """, (filename,))
                        result = cursor.fetchone()
                        if result and result.get("full_text") and result.get("summary"):
                            return {
                                "id": result["id"],
                                "director_name": result["director_name"],
                                "din": result["din"],
                                "file_path": result["file_path"],
                                "full_text": result["full_text"],
                                "summary": result["summary"],
                                "created_at": result["created_at"].isoformat() if result.get("created_at") else None,
                                "updated_at": result["updated_at"].isoformat() if result.get("updated_at") else None,
                            }
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except Exception as e:
                logger.warning(f"Disclosure summary PG fetch failed, falling back to SQLite: {e}")
            finally:
                if pg_conn:
                    try:
                        pg_conn.close()
                    except Exception:
                        pass

            # SQLite fallback (directors_data.db)
            sqlite_db_path = _sqlite_directors_data_db_path()
            if os.path.exists(sqlite_db_path):
                sconn = sqlite3.connect(sqlite_db_path)
                sconn.row_factory = sqlite3.Row
                scur = sconn.cursor()
                try:
                    scur.execute("""
                        SELECT id, director_name, din, file_path, full_text, summary, created_at, updated_at
                        FROM document_summaries
                        WHERE file_path = ?
                    """, (filename,))
                    row = scur.fetchone()
                    if row and row["full_text"] and row["summary"]:
                        return {
                            "id": int(row["id"]),
                            "director_name": row["director_name"],
                            "din": row["din"],
                            "file_path": row["file_path"],
                            "full_text": row["full_text"],
                            "summary": row["summary"],
                            "created_at": _normalize_empty(row["created_at"]) or None,
                            "updated_at": _normalize_empty(row["updated_at"]) or None,
                        }
                except Exception as e:
                    logger.warning(f"Disclosure summary SQLite read failed: {e}")
                finally:
                    try:
                        scur.close()
                    finally:
                        sconn.close()

            # If no record exists or it's incomplete, generate it automatically
            file_path = os.path.join(disclosures_dir, filename)

            # Extract director name from filename
            director_name = filename.replace('_MBP.docx', '').replace('.docx', '').strip()
            din = 'N/A'  # Default value

            # Try to generate full text and summary
            try:
                # Generate and save full text and summary (Note: generate_and_save_summary might still use SQLite internally)
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
                    'created_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'updated_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
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
                    'created_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'updated_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
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
@router.get("/directors/{director_name}/family-info", response_model=DirectorFamilyInfoResponse)
async def get_director_family_info(director_name: str):
    """Get family information for a specific director (PostgreSQL, fallback to SQLite)."""
    try:
        def fetch_family_info():
            pg_conn = None
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        cursor.execute("SELECT director_name FROM family_information.director_family ORDER BY director_name")
                        family_rows = cursor.fetchall()
                        family_list = [row["director_name"] for row in family_rows]

                        best_match = None
                        best_score = 0
                        for family_member in family_list:
                            score = indian_name_similarity(director_name, family_member)
                            if score > best_score and score >= 0.5:
                                best_score = score
                                best_match = family_member

                        if best_match:
                            cursor.execute("""
                                SELECT 
                                    director_name, section_2_77_i, section_2_77_ii, section_2_77_iii, 
                                    father, mother, son, sons_wife, daughter, daughters_husband, brother, sister,
                                    father_pan, mother_pan, father_pan_file, mother_pan_file
                                FROM family_information.director_family 
                                WHERE director_name = %s
                            """, (best_match,))

                            row = cursor.fetchone()
                            if row:
                                relationships = [
                                    ("Father", row["father"], row["father_pan"]),
                                    ("Mother", row["mother"], row["mother_pan"]),
                                    ("Son", row["son"], None),
                                    ("Son's Wife", row["sons_wife"], None),
                                    ("Daughter", row["daughter"], None),
                                    ("Daughter's Husband", row["daughters_husband"], None),
                                    ("Brother", row["brother"], None),
                                    ("Sister", row["sister"], None),
                                ]

                                family_members = []
                                for relationship, details, pan_no in relationships:
                                    if _is_meaningful(details) or _is_meaningful(pan_no):
                                        family_members.append({
                                            "relationship": relationship,
                                            "details": _normalize_empty(details),
                                            "pan_number": _normalize_empty(pan_no) if _is_meaningful(pan_no) else None,
                                        })

                                return {
                                    "director_name": director_name,
                                    "matched_family_name": best_match,
                                    "match_score": round(best_score, 2),
                                    "section_2_77_i": row["section_2_77_i"],
                                    "section_2_77_ii": row["section_2_77_ii"],
                                    "section_2_77_iii": row["section_2_77_iii"],
                                    "family_members": family_members,
                                }
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except Exception as e:
                logger.warning(f"Family info PG fetch failed, falling back to SQLite: {e}")
            finally:
                if pg_conn:
                    try:
                        pg_conn.close()
                    except Exception:
                        pass

            return _fetch_family_info_sqlite(director_name)
        
        loop = asyncio.get_event_loop()
        family_info = await loop.run_in_executor(thread_pool, fetch_family_info)
        
        if not family_info:
            raise HTTPException(status_code=404, detail="No family information found for this director")
        
        return DirectorFamilyInfoResponse(**family_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family info for director {director_name} in PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch family info: {str(e)}")

@router.put("/directors/{director_name}/family-info", response_model=DirectorFamilyInfoResponse)
async def update_director_family_info(director_name: str, request: UpdateFamilyInfoRequest):
    """Update family information for a specific director (PostgreSQL, fallback to SQLite)."""
    try:
        def update_family_info():
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        cursor.execute(
                            "SELECT director_name FROM family_information.director_family WHERE director_name = %s",
                            (director_name,),
                        )
                        existing_record = cursor.fetchone()

                        if not existing_record:
                            cursor.execute("""
                                INSERT INTO family_information.director_family (director_name, section_2_77_i, section_2_77_ii, section_2_77_iii)
                                VALUES (%s, %s, %s, %s)
                            """, (
                                director_name,
                                request.section_2_77_i,
                                request.section_2_77_ii,
                                request.section_2_77_iii,
                            ))
                        else:
                            cursor.execute("""
                                UPDATE family_information.director_family SET 
                                    section_2_77_i = %s,
                                    section_2_77_ii = %s,
                                    section_2_77_iii = %s
                                WHERE director_name = %s
                            """, (
                                request.section_2_77_i,
                                request.section_2_77_ii,
                                request.section_2_77_iii,
                                director_name,
                            ))

                        column_map = {
                            "Father": "father",
                            "Mother": "mother",
                            "Son": "son",
                            "Son's Wife": "sons_wife",
                            "Daughter": "daughter",
                            "Daughter's Husband": "daughters_husband",
                            "Brother": "brother",
                            "Sister": "sister",
                        }

                        for member in request.family_members:
                            column_name = column_map.get(member.relationship)
                            if not column_name:
                                continue
                            cursor.execute(
                                f"UPDATE family_information.director_family SET {column_name} = %s WHERE director_name = %s",
                                (member.details, director_name),
                            )
                            if member.pan_number is not None and column_name in ["father", "mother"]:
                                cursor.execute(
                                    f"UPDATE family_information.director_family SET {column_name}_pan = %s WHERE director_name = %s",
                                    (member.pan_number, director_name),
                                )

                        pg_conn.commit()

                        cursor.execute("""
                            SELECT 
                                director_name, section_2_77_i, section_2_77_ii, section_2_77_iii, 
                                father, mother, son, sons_wife, daughter, daughters_husband, brother, sister,
                                father_pan, mother_pan, father_pan_file, mother_pan_file
                            FROM family_information.director_family 
                            WHERE director_name = %s
                        """, (director_name,))

                        row = cursor.fetchone()
                        if row:
                            relationships = [
                                ("Father", row["father"], row["father_pan"]),
                                ("Mother", row["mother"], row["mother_pan"]),
                                ("Son", row["son"], None),
                                ("Son's Wife", row["sons_wife"], None),
                                ("Daughter", row["daughter"], None),
                                ("Daughter's Husband", row["daughters_husband"], None),
                                ("Brother", row["brother"], None),
                                ("Sister", row["sister"], None),
                            ]

                            family_members = []
                            for rel, det, p in relationships:
                                if _is_meaningful(det) or _is_meaningful(p):
                                    family_members.append({
                                        "relationship": rel,
                                        "details": _normalize_empty(det),
                                        "pan_number": _normalize_empty(p) if _is_meaningful(p) else None,
                                    })

                            return {
                                "director_name": director_name,
                                "matched_family_name": director_name,
                                "match_score": 1.0,
                                "section_2_77_i": row["section_2_77_i"],
                                "section_2_77_ii": row["section_2_77_ii"],
                                "section_2_77_iii": row["section_2_77_iii"],
                                "family_members": family_members,
                            }
                        return None
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Family info PG update failed, falling back to SQLite: {e}")

            return _upsert_family_info_sqlite(director_name, request)
        
        loop = asyncio.get_event_loop()
        updated_info = await loop.run_in_executor(thread_pool, update_family_info)
        
        if not updated_info:
            raise HTTPException(status_code=404, detail="Failed to update family information")
        
        # Log the change
        log_director_change(None, director_name, "Family Info Update", "Updated family information details")

        return DirectorFamilyInfoResponse(**updated_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating family info for director {director_name} in PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update family info: {str(e)}")


@router.get("/directors-profile/{din}", response_model=DirectorProfileResponse)
async def get_director_profile(din: str):
    """Get director profile information (PostgreSQL, fallback to SQLite)."""
    try:
        def fetch_profile():
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        cursor.execute("""
                            SELECT name_of_director, din, address, date_of_birth, pan, qualification, experience
                            FROM directors_profile.directors_profile 
                            WHERE din = %s
                        """, (din,))

                        row = cursor.fetchone()
                        if not row:
                            raise HTTPException(status_code=404, detail="Director profile not found")

                        return {
                            "name": row["name_of_director"] or "",
                            "din": row["din"] or "",
                            "address": row["address"],
                            "date_of_birth": row["date_of_birth"].strftime("%Y-%m-%d") if row["date_of_birth"] else None,
                            "pan": row["pan"],
                            "qualification": row["qualification"],
                            "experience": row["experience"],
                        }
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Director profile PG fetch failed, falling back to SQLite: {e}")

            profile_db_path = _sqlite_directors_profile_db_path()
            if not os.path.exists(profile_db_path):
                raise HTTPException(status_code=404, detail="Director profile database not found")

            sconn = sqlite3.connect(profile_db_path)
            sconn.row_factory = sqlite3.Row
            scur = sconn.cursor()
            try:
                scur.execute("""
                    SELECT
                        Name_of_Director,
                        DIN,
                        Address,
                        Date_of_Birth,
                        PAN,
                        Qualification,
                        Nature_of_Experience_in_specific_Functional_Areas
                    FROM directors_profile
                    WHERE DIN = ?
                    LIMIT 1
                """, (din,))
                row = scur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Director profile not found")

                dob = _normalize_empty(row["Date_of_Birth"])
                dob = dob.split(" ")[0] if " " in dob else dob

                return {
                    "name": _normalize_empty(row["Name_of_Director"]),
                    "din": _normalize_empty(row["DIN"]),
                    "address": row["Address"],
                    "date_of_birth": dob or None,
                    "pan": row["PAN"],
                    "qualification": row["Qualification"],
                    "experience": row["Nature_of_Experience_in_specific_Functional_Areas"],
                }
            finally:
                try:
                    scur.close()
                finally:
                    sconn.close()
        
        loop = asyncio.get_event_loop()
        profile = await loop.run_in_executor(thread_pool, fetch_profile)
        
        return DirectorProfileResponse(**profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching director profile for DIN {din} from PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch director profile: {str(e)}")

@router.put("/directors-profile/{din}", response_model=DirectorProfileResponse)
async def update_director_profile(din: str, request: DirectorProfileUpdateRequest):
    """Update director profile information (PostgreSQL, fallback to SQLite)."""
    try:
        def update_profile():
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        update_fields = []
                        values = []

                        if request.address is not None:
                            update_fields.append("address = %s")
                            values.append(request.address)
                        if request.date_of_birth is not None:
                            update_fields.append("date_of_birth = %s")
                            values.append(request.date_of_birth)
                        if request.pan is not None:
                            update_fields.append("pan = %s")
                            values.append(request.pan)
                        if request.qualification is not None:
                            update_fields.append("qualification = %s")
                            values.append(request.qualification)
                        if request.experience is not None:
                            update_fields.append("experience = %s")
                            values.append(request.experience)

                        if not update_fields:
                            raise HTTPException(status_code=400, detail="No fields to update")

                        values.append(din)
                        query = f"UPDATE directors_profile.directors_profile SET {', '.join(update_fields)} WHERE din = %s"
                        cursor.execute(query, values)

                        if cursor.rowcount == 0:
                            pg_conn.commit()
                            raise HTTPException(status_code=404, detail="Director profile not found")

                        pg_conn.commit()

                        cursor.execute("""
                            SELECT name_of_director, din, address, date_of_birth, pan, qualification, experience
                            FROM directors_profile.directors_profile 
                            WHERE din = %s
                        """, (din,))

                        row = cursor.fetchone()
                        if not row:
                            raise HTTPException(status_code=404, detail="Director profile not found after update")

                        return {
                            "name": row["name_of_director"] or "",
                            "din": row["din"] or "",
                            "address": row["address"],
                            "date_of_birth": row["date_of_birth"].strftime("%Y-%m-%d") if row["date_of_birth"] else None,
                            "pan": row["pan"],
                            "qualification": row["qualification"],
                            "experience": row["experience"],
                        }
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Director profile PG update failed, falling back to SQLite: {e}")

            update_fields = []
            values: List[Any] = []

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

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            profile_db_path = _sqlite_directors_profile_db_path()
            if not os.path.exists(profile_db_path):
                raise HTTPException(status_code=404, detail="Director profile database not found")

            sconn = sqlite3.connect(profile_db_path)
            sconn.row_factory = sqlite3.Row
            scur = sconn.cursor()
            try:
                values.append(din)
                scur.execute(
                    f"UPDATE directors_profile SET {', '.join(update_fields)} WHERE DIN = ?",
                    values,
                )
                if scur.rowcount == 0:
                    sconn.commit()
                    raise HTTPException(status_code=404, detail="Director profile not found")

                sconn.commit()
                scur.execute("""
                    SELECT
                        Name_of_Director,
                        DIN,
                        Address,
                        Date_of_Birth,
                        PAN,
                        Qualification,
                        Nature_of_Experience_in_specific_Functional_Areas
                    FROM directors_profile
                    WHERE DIN = ?
                    LIMIT 1
                """, (din,))
                row = scur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Director profile not found after update")

                dob = _normalize_empty(row["Date_of_Birth"])
                dob = dob.split(" ")[0] if " " in dob else dob

                return {
                    "name": _normalize_empty(row["Name_of_Director"]),
                    "din": _normalize_empty(row["DIN"]),
                    "address": row["Address"],
                    "date_of_birth": dob or None,
                    "pan": row["PAN"],
                    "qualification": row["Qualification"],
                    "experience": row["Nature_of_Experience_in_specific_Functional_Areas"],
                }
            finally:
                try:
                    scur.close()
                finally:
                    sconn.close()
        
        loop = asyncio.get_event_loop()
        updated_profile = await loop.run_in_executor(thread_pool, update_profile)
        
        # Log the change
        log_director_change(None, updated_profile['name'], "Profile Update", f"Updated profile for DIN {din}")

        return DirectorProfileResponse(**updated_profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating director profile for DIN {din} in PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update director profile: {str(e)}")

# Endpoint to upload director profile image
@router.post("/directors-profile/{din}/image", response_model=ImageUploadResponse)
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
        
        # Log the change
        log_director_change(None, f"Director (DIN: {din})", "Profile Photo Update", "Uploaded new profile photo")

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
@router.get("/directors-profile/{din}/image")
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
@router.delete("/directors-profile/{din}/image", response_model=ImageDeleteResponse)
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

# Endpoint to get all directors from PostgreSQL database for Minutes Preparation
@router.get("/directors-for-minutes", response_model=DirectorsMasterResponse)
async def get_directors_for_minutes():
    """Get all directors for Minutes Preparation (PostgreSQL, fallback to SQLite)."""
    try:
        def fetch_directors():
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    try:
                        cursor.execute("SELECT id, name, din, created_at FROM directors_master.directors ORDER BY name")
                        rows = cursor.fetchall()

                        return [{
                            "id": row["id"],
                            "name": row["name"],
                            "din": row["din"],
                            "created_at": row["created_at"].isoformat() if row["created_at"] else datetime.now().isoformat(),
                        } for row in rows]
                    finally:
                        try:
                            cursor.close()
                        finally:
                            pg_conn.close()
            except Exception as e:
                logger.warning(f"Directors list for minutes PG fetch failed, falling back to SQLite: {e}")
            
            return _fetch_directors_master_sqlite()
        
        loop = asyncio.get_event_loop()
        directors = await loop.run_in_executor(thread_pool, fetch_directors)
        
        return DirectorsMasterResponse(
            data=[DirectorMasterResponse(**d) for d in directors],
            count=len(directors)
        )
    except Exception as e:
        logger.error(f"Error fetching directors for minutes from PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch directors: {str(e)}")

# Endpoint to download template files
@router.get("/directors-disclosures/templates/{template_name}")
async def download_disclosure_template(template_name: str):
    """Download a disclosure template file"""
    try:
        # Define the templates directory
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")
        
        # Valid template filenames
        # For simplicity, allow any file in templates dir
        potential_path = os.path.join(templates_dir, template_name)
        
        if not os.path.exists(potential_path):
             # Fallback logic if needed, or error
             logger.error(f"Template not found: {potential_path}")
             raise HTTPException(status_code=404, detail="Template not found")
            
        return FileResponse(
            path=potential_path,
            filename=template_name,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading template {template_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download template: {str(e)}")
