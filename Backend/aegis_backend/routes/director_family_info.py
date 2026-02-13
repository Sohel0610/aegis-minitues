from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import concurrent.futures
import logging
import os
from datetime import datetime

# Import our enhanced matching algorithm
from EnhancedIndianNameMatcher import indian_name_similarity

# Import our PostgreSQL service
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for director family info endpoints
router = APIRouter()

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
    """Get family information for a specific director using enhanced matching against PostgreSQL"""
    try:
        # Connect to PostgreSQL
        pg_conn = get_pg_connection()
        if not pg_conn:
            raise HTTPException(status_code=500, detail="Could not connect to Azure PostgreSQL")
        
        try:
            # Get all family information records from PG
            cursor = get_pg_cursor(pg_conn)
            cursor.execute("SELECT director_name FROM family_information.director_family ORDER BY director_name")
            family_rows = cursor.fetchall()
            family_list = [row['director_name'] for row in family_rows]
            
            # Find the best match for the director
            best_match = None
            best_score = 0
            
            for family_member in family_list:
                score = indian_name_similarity(director_name, family_member)
                if score > best_score and score >= 0.5:  # Minimum threshold
                    best_score = score
                    best_match = family_member
            
            # If we found a match, get the detailed family information
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
                    # Create family members list
                    family_members = []
                    
                    # Core relationships with potential PAN details
                    # Note: father and mother have PAN, others might not yet in this schema iteration
                    relationships = [
                        ("Father", row['father'], row['father_pan'], row['father_pan_file']),
                        ("Mother", row['mother'], row['mother_pan'], row['mother_pan_file']),
                        ("Son", row['son'], None, None),
                        ("Son's Wife", row['sons_wife'], None, None),
                        ("Daughter", row['daughter'], None, None),
                        ("Daughter's Husband", row['daughters_husband'], None, None),
                        ("Brother", row['brother'], None, None),
                        ("Sister", row['sister'], None, None)
                    ]
                    
                    for relationship, details, pan, pan_file in relationships:
                        if details and str(details).strip().lower() not in ['n/a', 'none', '', 'nil']:
                            family_members.append({
                                "relationship": relationship,
                                "details": str(details),
                                "pan": pan,
                                "pan_file": pan_file
                            })
                    
                    return {
                        "director_name": director_name,
                        "matched_family_name": best_match,
                        "match_score": round(best_score, 2),
                        "section_2_77_i": row['section_2_77_i'],
                        "section_2_77_ii": row['section_2_77_ii'],
                        "section_2_77_iii": row['section_2_77_iii'],
                        "family_members": family_members,
                        "is_submitted": bool(row['is_submitted'])
                    }
            
            # No match found
            return None
            
        finally:
            pg_conn.close()
            
    except Exception as e:
        logger.error(f"Error getting family info for director {director_name} from PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get family info from PostgreSQL: {str(e)}")

def get_all_directors_with_family_info():
    """Get family information for all directors from PostgreSQL"""
    try:
        # Connect to PostgreSQL
        pg_conn = get_pg_connection()
        if not pg_conn:
            raise HTTPException(status_code=500, detail="Could not connect to Azure PostgreSQL")
        
        try:
            cursor = get_pg_cursor(pg_conn)
            
            # Get all directors from the master table in PG
            cursor.execute("SELECT name FROM directors_master.directors ORDER BY name")
            directors_rows = cursor.fetchall()
            
            directors_with_family = []
            
            # For each director, try to find family information using the same PG connection
            # We'll optimize by passing the connection if needed, but for now we follow the existing pattern
            for row in directors_rows:
                director_name = row['name']
                family_info = get_family_info_for_director(director_name)
                
                if family_info:
                    directors_with_family.append(family_info)
            
            return directors_with_family
            
        finally:
            pg_conn.close()
            
    except Exception as e:
        logger.error(f"Error getting all directors with family info from PG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get directors with family info from PostgreSQL: {str(e)}")

# Endpoint to get family information for a specific director
@router.get("/api/directors/{director_name}/family-info", response_model=DirectorFamilyInfoResponse)
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
@router.get("/api/directors/family-info", response_model=FamilyInfoListResponse)
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
@router.put("/api/directors/{director_name}/family-info")
async def update_director_family_info(director_name: str, family_info: Dict[str, Any]):
    """Update family information for a director"""
    try:
        # This would be implemented to update the family database
        # For now, we'll just return a placeholder response
        return {
            "success": True,
            "message": f"Family information update for {director_name} would be implemented here"
        }
    except Exception as e:
        logger.error(f"Error updating family info for director {director_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update family info: {str(e)}")