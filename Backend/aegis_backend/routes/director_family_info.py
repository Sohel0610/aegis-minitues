from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import concurrent.futures
import logging
import os
import sqlite3
from datetime import datetime

# Import our enhanced matching algorithm
from routes.EnhancedIndianNameMatcher import indian_name_similarity

# Import our PostgreSQL service
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for director family info endpoints
router = APIRouter()

def _is_meaningful(value) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    return bool(s) and s.lower() not in {"n/a", "na", "none", "nil", "null"}

def _family_sqlite_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "public", "Director_Family_Information.db")

def _sqlite_fetch_family_info(director_name: str):
    db_path = _family_sqlite_path()
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT Name FROM Sheet1 WHERE Name IS NOT NULL ORDER BY Name")
        names = [r["Name"] for r in cur.fetchall() if r and r["Name"]]

        best_match = None
        best_score = 0
        for name in names:
            score = indian_name_similarity(director_name, name)
            if score > best_score and score >= 0.5:
                best_score = score
                best_match = name

        if not best_match:
            return None

        cur.execute("""
            SELECT
                Name AS director_name,
                "Section_2(77)(i)"   AS section_2_77_i,
                "Section_2(77)(ii)"  AS section_2_77_ii,
                "Section_2(77)(iii)" AS section_2_77_iii,
                Father AS father,
                Mother AS mother,
                Son AS son,
                "Son's_Wife" AS sons_wife,
                Daughter AS daughter,
                "Daughter's_husband" AS daughters_husband,
                Brother AS brother,
                Sister AS sister,
                Father_PAN AS father_pan,
                Mother_PAN AS mother_pan,
                Father_PAN_File AS father_pan_file,
                Mother_PAN_File AS mother_pan_file,
                Is_Submitted AS is_submitted
            FROM Sheet1
            WHERE Name = ?
            LIMIT 1
        """, (best_match,))
        row = cur.fetchone()
        if not row:
            return None

        relationships = [
            ("Father", row["father"], row["father_pan"], row["father_pan_file"]),
            ("Mother", row["mother"], row["mother_pan"], row["mother_pan_file"]),
            ("Son", row["son"], None, None),
            ("Son's Wife", row["sons_wife"], None, None),
            ("Daughter", row["daughter"], None, None),
            ("Daughter's Husband", row["daughters_husband"], None, None),
            ("Brother", row["brother"], None, None),
            ("Sister", row["sister"], None, None),
        ]

        family_members: List[Dict[str, Any]] = []
        for relationship, details, pan, pan_file in relationships:
            if _is_meaningful(details) or _is_meaningful(pan) or _is_meaningful(pan_file):
                family_members.append({
                    "relationship": relationship,
                    "details": str(details).strip() if details is not None else "",
                    "pan": str(pan).strip() if _is_meaningful(pan) else None,
                    "pan_file": str(pan_file).strip() if _is_meaningful(pan_file) else None,
                })

        is_submitted_val = row["is_submitted"]
        try:
            is_submitted = bool(int(is_submitted_val)) if is_submitted_val is not None else False
        except Exception:
            is_submitted = str(is_submitted_val).strip().lower() in {"true", "yes", "y", "submitted"}

        return {
            "director_name": director_name,
            "matched_family_name": best_match,
            "match_score": round(best_score, 2),
            "section_2_77_i": row["section_2_77_i"],
            "section_2_77_ii": row["section_2_77_ii"],
            "section_2_77_iii": row["section_2_77_iii"],
            "family_members": family_members,
            "is_submitted": is_submitted,
        }
    finally:
        try:
            cur.close()
        finally:
            conn.close()

def _sqlite_upsert_family_info(director_name: str, payload: Dict[str, Any]):
    db_path = _family_sqlite_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # Ensure table exists (pre-bundled DB should already have it, but make it robust).
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Sheet1 (
                Name TEXT
            )
        """)
        # Ensure expected columns exist for fresh DBs.
        for col_name, col_type in [
            ("Section_2(77)(i)", "TEXT"),
            ("Section_2(77)(ii)", "TEXT"),
            ("Section_2(77)(iii)", "TEXT"),
            ("Father", "TEXT"),
            ("Mother", "TEXT"),
            ("Son", "TEXT"),
            ("Son's_Wife", "TEXT"),
            ("Daughter", "TEXT"),
            ("Daughter's_husband", "TEXT"),
            ("Brother", "TEXT"),
            ("Sister", "TEXT"),
            ("Father_PAN", "TEXT"),
            ("Mother_PAN", "TEXT"),
            ("Father_PAN_File", "TEXT"),
            ("Mother_PAN_File", "TEXT"),
            ("Is_Submitted", "INTEGER"),
        ]:
            try:
                cur.execute(f'ALTER TABLE Sheet1 ADD COLUMN "{col_name}" {col_type}')
            except Exception:
                pass

        cur.execute("SELECT rowid FROM Sheet1 WHERE Name = ? LIMIT 1", (director_name,))
        existing = cur.fetchone()

        section_2_77_i = payload.get("section_2_77_i")
        section_2_77_ii = payload.get("section_2_77_ii")
        section_2_77_iii = payload.get("section_2_77_iii")
        is_submitted = payload.get("is_submitted")

        if existing:
            cur.execute("""
                UPDATE Sheet1 SET
                    "Section_2(77)(i)" = ?,
                    "Section_2(77)(ii)" = ?,
                    "Section_2(77)(iii)" = ?,
                    Is_Submitted = ?
                WHERE Name = ?
            """, (section_2_77_i, section_2_77_ii, section_2_77_iii, 1 if is_submitted else 0, director_name))
        else:
            cur.execute("""
                INSERT INTO Sheet1 (Name, "Section_2(77)(i)", "Section_2(77)(ii)", "Section_2(77)(iii)", Is_Submitted)
                VALUES (?, ?, ?, ?, ?)
            """, (director_name, section_2_77_i, section_2_77_ii, section_2_77_iii, 1 if is_submitted else 0))

        column_map = {
            "Father": ("Father", "Father_PAN", "Father_PAN_File"),
            "Mother": ("Mother", "Mother_PAN", "Mother_PAN_File"),
            "Son": ("Son", None, None),
            "Son's Wife": ("Son's_Wife", None, None),
            "Daughter": ("Daughter", None, None),
            "Daughter's Husband": ("Daughter's_husband", None, None),
            "Brother": ("Brother", None, None),
            "Sister": ("Sister", None, None),
        }

        for member in payload.get("family_members", []) or []:
            rel = (member or {}).get("relationship")
            if not rel or rel not in column_map:
                continue
            details_col, pan_col, pan_file_col = column_map[rel]

            details = (member or {}).get("details")
            cur.execute(f'UPDATE Sheet1 SET "{details_col}" = ? WHERE Name = ?', (details, director_name))

            if pan_col:
                cur.execute(f'UPDATE Sheet1 SET "{pan_col}" = ? WHERE Name = ?', ((member or {}).get("pan"), director_name))
            if pan_file_col:
                cur.execute(f'UPDATE Sheet1 SET "{pan_file_col}" = ? WHERE Name = ?', ((member or {}).get("pan_file"), director_name))

        conn.commit()
    finally:
        try:
            cur.close()
        finally:
            conn.close()

    # Return best-effort normalized response (exact match)
    return _sqlite_fetch_family_info(director_name) or {
        "director_name": director_name,
        "matched_family_name": director_name,
        "match_score": 1.0,
        "section_2_77_i": payload.get("section_2_77_i"),
        "section_2_77_ii": payload.get("section_2_77_ii"),
        "section_2_77_iii": payload.get("section_2_77_iii"),
        "family_members": payload.get("family_members", []) or [],
        "is_submitted": bool(payload.get("is_submitted", False)),
    }

# Response models
class FamilyMemberInfo(BaseModel):
    relationship: str
    details: str
    pan: Optional[str] = None
    pan_file: Optional[str] = None

class DirectorFamilyInfoResponse(BaseModel):
    director_name: str
    matched_family_name: str
    match_score: float
    section_2_77_i: Optional[str] = None
    section_2_77_ii: Optional[str] = None
    section_2_77_iii: Optional[str] = None
    family_members: List[FamilyMemberInfo]
    is_submitted: bool = False
    created_at: str = datetime.now().isoformat()

class FamilyInfoListResponse(BaseModel):
    data: List[DirectorFamilyInfoResponse]
    count: int

def get_family_info_for_director(director_name: str):
    """Get family information for a specific director (PostgreSQL primary, SQLite fallback)."""
    pg_conn = None
    try:
        pg_conn = get_pg_connection()
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            # Get all family information records from PG
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
                        father_pan, mother_pan, father_pan_file, mother_pan_file, is_submitted
                    FROM family_information.director_family 
                    WHERE director_name = %s
                """, (best_match,))

                row = cursor.fetchone()
                if row:
                    relationships = [
                        ("Father", row["father"], row["father_pan"], row["father_pan_file"]),
                        ("Mother", row["mother"], row["mother_pan"], row["mother_pan_file"]),
                        ("Son", row["son"], None, None),
                        ("Son's Wife", row["sons_wife"], None, None),
                        ("Daughter", row["daughter"], None, None),
                        ("Daughter's Husband", row["daughters_husband"], None, None),
                        ("Brother", row["brother"], None, None),
                        ("Sister", row["sister"], None, None),
                    ]

                    family_members = []
                    for relationship, details, pan, pan_file in relationships:
                        if _is_meaningful(details) or _is_meaningful(pan) or _is_meaningful(pan_file):
                            family_members.append({
                                "relationship": relationship,
                                "details": str(details).strip() if details is not None else "",
                                "pan": str(pan).strip() if _is_meaningful(pan) else None,
                                "pan_file": str(pan_file).strip() if _is_meaningful(pan_file) else None,
                            })

                    return {
                        "director_name": director_name,
                        "matched_family_name": best_match,
                        "match_score": round(best_score, 2),
                        "section_2_77_i": row["section_2_77_i"],
                        "section_2_77_ii": row["section_2_77_ii"],
                        "section_2_77_iii": row["section_2_77_iii"],
                        "family_members": family_members,
                        "is_submitted": bool(row["is_submitted"]),
                    }

            return None
    except Exception as e:
        logger.warning(f"PG family info fetch failed, falling back to SQLite: {e}")
        return _sqlite_fetch_family_info(director_name)
    finally:
        if pg_conn:
            try:
                pg_conn.close()
            except Exception:
                pass

def get_all_directors_with_family_info():
    """Get family information for all directors (PostgreSQL primary, SQLite fallback)."""
    pg_conn = None
    try:
        pg_conn = get_pg_connection()
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute("SELECT name FROM directors_master.directors ORDER BY name")
            directors_rows = cursor.fetchall()

            directors_with_family = []
            for row in directors_rows:
                director_name = row["name"]
                family_info = get_family_info_for_director(director_name)
                if family_info:
                    directors_with_family.append(family_info)
            return directors_with_family
    except Exception as e:
        logger.warning(f"PG family-info list fetch failed, falling back to SQLite: {e}")
    finally:
        if pg_conn:
            try:
                pg_conn.close()
            except Exception:
                pass

    # SQLite fallback: return all records from the family DB.
    db_path = _family_sqlite_path()
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT Name FROM Sheet1 WHERE Name IS NOT NULL ORDER BY Name")
        names = [r["Name"] for r in cur.fetchall() if r and r["Name"]]
    finally:
        try:
            cur.close()
        finally:
            conn.close()

    results = []
    for name in names:
        info = _sqlite_fetch_family_info(name)
        if info:
            # When listing all, treat it as an exact match.
            info["matched_family_name"] = info.get("matched_family_name") or name
            info["match_score"] = info.get("match_score") or 1.0
            results.append(info)

    return results

# Endpoint to get family information for a specific director
@router.get("/directors/{director_name}/family-info", response_model=DirectorFamilyInfoResponse)
async def get_director_family_info(director_name: str):
    """Get family information for a specific director"""
    try:
        def fetch_family_info():
            return get_family_info_for_director(director_name)
        
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

# Endpoint to get family information for all directors
@router.get("/directors/family-info", response_model=FamilyInfoListResponse)
async def get_all_directors_family_info():
    """Get family information for all directors"""
    try:
        def fetch_all_family_info():
            return get_all_directors_with_family_info()
        
        loop = asyncio.get_event_loop()
        directors_with_family = await loop.run_in_executor(thread_pool, fetch_all_family_info)
        
        return FamilyInfoListResponse(
            data=[DirectorFamilyInfoResponse(**info) for info in directors_with_family],
            count=len(directors_with_family)
        )
    except Exception as e:
        logger.error(f"Error fetching family info for all directors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch family info: {str(e)}")

# Endpoint to update family information for a director
@router.put("/directors/{director_name}/family-info", response_model=DirectorFamilyInfoResponse)
async def update_director_family_info(director_name: str, family_info: Dict[str, Any]):
    """Update family information for a director (PostgreSQL primary, SQLite fallback)."""
    try:
        def update_family_info():
            pg_conn = None
            try:
                pg_conn = get_pg_connection()
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)

                    cursor.execute(
                        "SELECT director_name FROM family_information.director_family WHERE director_name = %s",
                        (director_name,),
                    )
                    exists = cursor.fetchone()
                    if not exists:
                        cursor.execute(
                            "INSERT INTO family_information.director_family (director_name) VALUES (%s)",
                            (director_name,),
                        )

                    update_fields = []
                    params = []
                    for field in ("section_2_77_i", "section_2_77_ii", "section_2_77_iii"):
                        if field in family_info:
                            update_fields.append(f"{field} = %s")
                            params.append(family_info.get(field))
                    if "is_submitted" in family_info:
                        update_fields.append("is_submitted = %s")
                        params.append(1 if family_info.get("is_submitted") else 0)
                    if update_fields:
                        params.append(director_name)
                        cursor.execute(
                            f"UPDATE family_information.director_family SET {', '.join(update_fields)} WHERE director_name = %s",
                            params,
                        )

                    column_map = {
                        "Father": ("father", "father_pan", "father_pan_file"),
                        "Mother": ("mother", "mother_pan", "mother_pan_file"),
                        "Son": ("son", None, None),
                        "Son's Wife": ("sons_wife", None, None),
                        "Daughter": ("daughter", None, None),
                        "Daughter's Husband": ("daughters_husband", None, None),
                        "Brother": ("brother", None, None),
                        "Sister": ("sister", None, None),
                    }

                    for member in family_info.get("family_members", []) or []:
                        rel = (member or {}).get("relationship")
                        if not rel or rel not in column_map:
                            continue
                        details_col, pan_col, pan_file_col = column_map[rel]
                        cursor.execute(
                            f"UPDATE family_information.director_family SET {details_col} = %s WHERE director_name = %s",
                            ((member or {}).get("details"), director_name),
                        )
                        if pan_col:
                            cursor.execute(
                                f"UPDATE family_information.director_family SET {pan_col} = %s WHERE director_name = %s",
                                ((member or {}).get("pan"), director_name),
                            )
                        if pan_file_col:
                            cursor.execute(
                                f"UPDATE family_information.director_family SET {pan_file_col} = %s WHERE director_name = %s",
                                ((member or {}).get("pan_file"), director_name),
                            )

                    pg_conn.commit()

                    # Return the updated record (exact match)
                    updated = get_family_info_for_director(director_name)
                    return updated
            except Exception as e:
                logger.warning(f"PG family info update failed, falling back to SQLite: {e}")
                try:
                    if pg_conn:
                        pg_conn.rollback()
                except Exception:
                    pass
            finally:
                if pg_conn:
                    try:
                        pg_conn.close()
                    except Exception:
                        pass

            return _sqlite_upsert_family_info(director_name, family_info)

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
