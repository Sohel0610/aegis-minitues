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
    spouse_pan: Optional[str] = None # Added for spouse PAN
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
                        father_pan, mother_pan, father_pan_file, mother_pan_file, is_submitted,
                        spouse_pan
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
                        "spouse_pan": row.get("spouse_pan") or ""
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
        logger.error(f"PostgreSQL comprehensive family-info fetch failed: {e}")
        return []
    finally:
        if pg_conn:
            try:
                pg_conn.close()
            except Exception:
                pass
    return []

# Endpoint to get family information for a specific director (By DIN or Name fallback)
@router.get("/directors/{identifier}/family-info", response_model=DirectorFamilyInfoResponse)
async def get_director_family_info(identifier: str):
    """Get family information for a specific director by DIN or Name"""
    try:
        def fetch_family_info():
            pg_conn = None
            try:
                pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    
                    target_din = None
                    target_name = identifier
                    
                    # 1. Resolve Identity: If it looks like a DIN, find the name
                    if identifier.isdigit() and len(identifier) >= 7:
                        target_din = identifier
                        cursor.execute("SELECT name FROM directors_master.directors WHERE TRIM(din) = TRIM(%s)", (target_din,))
                        res = cursor.fetchone()
                        if res: target_name = res["name"]
                    
                    # 2. Try exact DIN match in family table
                    if target_din:
                        cursor.execute("SELECT * FROM family_information.director_family WHERE TRIM(din) = TRIM(%s)", (target_din,))
                        row = cursor.fetchone()
                        if row: return _format_family_response(row, target_din)
                    
                    # 3. Try exact Name match in family table
                    cursor.execute("SELECT * FROM family_information.director_family WHERE TRIM(director_name) = TRIM(%s)", (target_name,))
                    row = cursor.fetchone()
                    if row: return _format_family_response(row, target_din or target_name)
                    
                    # 4. Fallback to Fuzzy Name Matching (The platform's smartest logic)
                    return get_family_info_for_director(target_name)
                return None
            finally:
                if pg_conn: pg_conn.close()
        
        loop = asyncio.get_event_loop()
        family_info = await loop.run_in_executor(thread_pool, fetch_family_info)
        
        if not family_info:
            # Return a default empty structure instead of 404 so frontend can show the empty form
            return {
                "director_name": identifier,
                "matched_family_name": identifier,
                "match_score": 0.0,
                "section_2_77_i": "",
                "section_2_77_ii": "",
                "spouse_pan": "",
                "section_2_77_iii": "",
                "family_members": [],
                "is_submitted": False
            }
        
        return DirectorFamilyInfoResponse(**family_info)
    except Exception as e:
        logger.error(f"Error fetching family info for {identifier}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _format_family_response(row, identifier):
    # Base response from the master table
    response = {
        "director_name": row["director_name"],
        "matched_family_name": row["director_name"],
        "match_score": 1.0,
        "section_2_77_i": row["section_2_77_i"],
        "section_2_77_ii": row["section_2_77_ii"],
        "spouse_pan": row.get("spouse_pan") or row.get("section_2_77_ii_pan"), # Handle both naming conventions
        "section_2_77_iii": row["section_2_77_iii"],
        "family_members": [],
        "is_submitted": bool(row["is_submitted"]),
    }

    # 1. Fetch individual members from the relational table (Priority)
    pg_conn = None
    try:
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute("""
                SELECT relationship, full_name, pan 
                FROM family_information.director_family_members 
                WHERE TRIM(din) = TRIM(%s) OR TRIM(din) = (SELECT TRIM(din) FROM family_information.director_family WHERE TRIM(director_name) = TRIM(%s) LIMIT 1)
                ORDER BY relationship, pairing_group
            """, (identifier, identifier))
            
            members = cursor.fetchall()
            for m in members:
                response["family_members"].append({
                    "relationship": m["relationship"],
                    "details": m["full_name"],
                    "pan": m["pan"]
                })

            # 2. Fallback/Supplement from Master Row Columns (Legacy)
            # This ensures Gautam Adani's data shows up!
            legacy_fields = [
                ("Father", row.get("father")),
                ("Mother", row.get("mother")),
                ("Son", row.get("son")),
                ("Son's Wife", row.get("sons_wife")),
                ("Daughter", row.get("daughter")),
                ("Daughter's Husband", row.get("daughters_husband")),
                ("Brother", row.get("brother")),
                ("Sister", row.get("sister"))
            ]
            
            for rel, val in legacy_fields:
                if val and str(val).lower() not in ["nil", "none", "n/a", ""]:
                    # Split multi-names (common in legacy data)
                    names = []
                    if "," in str(val): names = [n.strip() for n in str(val).split(",")]
                    elif "  " in str(val): names = [n.strip() for n in str(val).split("  ")]
                    else: names = [str(val).strip()]
                    
                    for name in names:
                        if name:
                            # Avoid duplicates if already in relational list
                            if not any(m["details"].lower() == name.lower() for m in response["family_members"]):
                                response["family_members"].append({
                                    "relationship": rel,
                                    "details": name,
                                    "pan": row.get(f"{rel.lower().replace(' ', '_')}_pan") # Check for legacy PAN columns
                                })
    finally:
        if pg_conn: pg_conn.close()

    return response

# Endpoint to update family information for a director
@router.put("/directors/{identifier}/family-info", response_model=DirectorFamilyInfoResponse)
async def update_director_family_info(identifier: str, family_info: Dict[str, Any]):
    """Update family information by DIN or Name"""
    try:
        def update_logic():
            pg_conn = None
            try:
                pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
                if pg_conn:
                    cursor = get_pg_cursor(pg_conn)
                    
                    # 0. Schema Migration (Ensure spouse_pan exists)
                    cursor.execute("ALTER TABLE family_information.director_family ADD COLUMN IF NOT EXISTS spouse_pan TEXT")
                    cursor.execute("ALTER TABLE family_information.director_family ADD COLUMN IF NOT EXISTS din TEXT")
                    pg_conn.commit()

                    # 1. Resolve DIN
                    is_din = identifier.isdigit() and len(identifier) >= 8
                    resolved_din = identifier if is_din else None
                    
                    if not resolved_din:
                        cursor.execute("SELECT din FROM family_information.director_family WHERE TRIM(director_name) = TRIM(%s)", (identifier,))
                        res = cursor.fetchone()
                        resolved_din = res['din'] if res else None

                    if not resolved_din:
                        raise Exception(f"Cannot resolve DIN for {identifier}")

                    # 2. Update Master Record
                    update_fields = []
                    params = []
                    for f in ("section_2_77_i", "section_2_77_ii", "section_2_77_iii", "spouse_pan"):
                        # Accept both spouse_pan and section_2_77_ii_pan from frontend
                        val = family_info.get(f) or (family_info.get("section_2_77_ii_pan") if f == "spouse_pan" else None)
                        if val is not None:
                            update_fields.append(f"{f} = %s")
                            params.append(val)
                    
                    if update_fields:
                        params.append(resolved_din)
                        cursor.execute(f"UPDATE family_information.director_family SET {', '.join(update_fields)} WHERE TRIM(din) = TRIM(%s)", params)

                    # 3. Update Individual Members (Relational)
                    # Clear existing and re-insert for consistency
                    cursor.execute("DELETE FROM family_information.director_family_members WHERE TRIM(din) = TRIM(%s)", (resolved_din,))
                    
                    members_list = family_info.get("family_members", []) or []
                    for i, member in enumerate(members_list):
                        cursor.execute("""
                            INSERT INTO family_information.director_family_members 
                            (din, relationship, full_name, pan, pairing_group)
                            VALUES (TRIM(%s), TRIM(%s), TRIM(%s), TRIM(%s), %s)
                        """, (
                            resolved_din, 
                            member.get("relationship"), 
                            member.get("details"), 
                            member.get("pan"),
                            i # Simple pairing group for now
                        ))

                    pg_conn.commit()
                    return True
                return False
            finally:
                if pg_conn: pg_conn.close()

        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(thread_pool, update_logic)
        
        # Return the updated record
        return await get_director_family_info(identifier)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))