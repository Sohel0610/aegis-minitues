# Director Family Information Route Module
# This module handles director family information exclusively using PostgreSQL.
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import concurrent.futures
import logging
import os
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
    """Get family information for a specific director using PostgreSQL."""
    pg_conn = None
    try:
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            # Get all family information records from PG for matching
            cursor.execute("SELECT director_name FROM  director_family ORDER BY director_name")
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
                    FROM  director_family 
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
        logger.error(f"PostgreSQL family info fetch failed: {e}")
        return None
    finally:
        if pg_conn:
            try:
                pg_conn.close()
            except Exception:
                pass

def get_all_directors_with_family_info():
    """Get family information for all directors via PostgreSQL."""
    pg_conn = None
    try:
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute("SELECT name FROM  directors ORDER BY name")
            directors_rows = cursor.fetchall()

            directors_with_family = []
            for row in directors_rows:
                director_name = row["name"]
                family_info = get_family_info_for_director(director_name)
                if family_info:
                    directors_with_family.append(family_info)
            return directors_with_family
    except Exception as e:
        logger.error(f"PostgreSQL comprehensive family-info fetch failed: {e}")
        return []
    finally:
        if pg_conn:
            try:
                pg_conn.close()
            except Exception:
                pass
    return []

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
    """Update family information for a director exclusively in PostgreSQL."""
    try:
        def update_family_info():
            pg_conn = None
            try:
                pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)

                    cursor.execute(
                        "SELECT director_name FROM  director_family WHERE director_name = %s",
                        (director_name,),
                    )
                    exists = cursor.fetchone()
                    if not exists:
                        cursor.execute(
                            "INSERT INTO  director_family (director_name) VALUES (%s)",
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
                            f"UPDATE  director_family SET {', '.join(update_fields)} WHERE director_name = %s",
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
                            f"UPDATE  director_family SET {details_col} = %s WHERE director_name = %s",
                            ((member or {}).get("details"), director_name),
                        )
                        if pan_col:
                            cursor.execute(
                                f"UPDATE  director_family SET {pan_col} = %s WHERE director_name = %s",
                                ((member or {}).get("pan"), director_name),
                            )
                        if pan_file_col:
                            cursor.execute(
                                f"UPDATE  director_family SET {pan_file_col} = %s WHERE director_name = %s",
                                ((member or {}).get("pan_file"), director_name),
                            )

                    pg_conn.commit()

                    # Return the updated record (exact match)
                    updated = get_family_info_for_director(director_name)
                    return updated
                else:
                    raise Exception("No PostgreSQL connection available")
            except Exception as e:
                logger.error(f"PostgreSQL family info update failed: {e}")
                if pg_conn:
                    pg_conn.rollback()
                raise
            finally:
                if pg_conn:
                    try:
                        pg_conn.close()
                    except Exception:
                        pass

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
