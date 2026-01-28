from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import concurrent.futures
import logging
import sqlite3
import os
from datetime import datetime

# Import our enhanced matching algorithm
from EnhancedIndianNameMatcher import indian_name_similarity

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for director family info endpoints
router = APIRouter()

# Response models
class FamilyMemberInfo(BaseModel):
    relationship: str
    details: str

class DirectorFamilyInfoResponse(BaseModel):
    director_name: str
    matched_family_name: str
    match_score: float
    section_2_77_i: Optional[str] = None
    section_2_77_ii: Optional[str] = None
    section_2_77_iii: Optional[str] = None
    family_members: List[FamilyMemberInfo]
    created_at: str = datetime.now().isoformat()

class FamilyInfoListResponse(BaseModel):
    data: List[DirectorFamilyInfoResponse]
    count: int

# Database paths
directors_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "directors.db")
family_db_path = os.path.join(os.path.dirname(__file__), "..", "public", "Director_Family_Information.db")

def get_family_info_for_director(director_name: str):
    """Get family information for a specific director using enhanced matching"""
    try:
        if not os.path.exists(directors_db_path) or not os.path.exists(family_db_path):
            raise HTTPException(status_code=404, detail="Required databases not found")
        
        # Connect to both databases
        directors_conn = sqlite3.connect(directors_db_path)
        family_conn = sqlite3.connect(family_db_path)
        
        try:
            # Get all family members
            family_cursor = family_conn.cursor()
            family_cursor.execute("SELECT Name FROM Sheet1 ORDER BY Name")
            family_rows = family_cursor.fetchall()
            family_list = [row[0] for row in family_rows]
            
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
                family_cursor.execute("""
                    SELECT Name, "Section_2(77)(i)", "Section_2(77)(ii)", "Section_2(77)(iii)", 
                           Father, Mother, Son, "Son's_Wife", Daughter, "Daughter's_husband", Brother, Sister 
                    FROM Sheet1 
                    WHERE Name = ?
                """, (best_match,))
                
                family_data = family_cursor.fetchone()
                
                if family_data:
                    # Create family members list
                    family_members = []
                    
                    # Add section information
                    section_2_77_i = family_data[1] if family_data[1] else None
                    section_2_77_ii = family_data[2] if family_data[2] else None
                    section_2_77_iii = str(family_data[3]) if family_data[3] is not None else None
                    
                    # Add family members
                    relationships = [
                        ("Father", family_data[4]),
                        ("Mother", family_data[5]),
                        ("Son", family_data[6]),
                        ("Son's Wife", family_data[7]),
                        ("Daughter", family_data[8]),
                        ("Daughter's Husband", family_data[9]),
                        ("Brother", family_data[10]),
                        ("Sister", family_data[11])
                    ]
                    
                    for relationship, details in relationships:
                        if details and str(details).strip().lower() not in ['n/a', 'none', '', 'nil']:
                            family_members.append({
                                "relationship": relationship,
                                "details": str(details)
                            })
                    
                    return {
                        "director_name": director_name,
                        "matched_family_name": best_match,
                        "match_score": round(best_score, 2),
                        "section_2_77_i": section_2_77_i,
                        "section_2_77_ii": section_2_77_ii,
                        "section_2_77_iii": section_2_77_iii,
                        "family_members": family_members
                    }
            
            # No match found
            return None
            
        finally:
            directors_conn.close()
            family_conn.close()
            
    except Exception as e:
        logger.error(f"Error getting family info for director {director_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get family info: {str(e)}")

def get_all_directors_with_family_info():
    """Get family information for all directors"""
    try:
        if not os.path.exists(directors_db_path) or not os.path.exists(family_db_path):
            raise HTTPException(status_code=404, detail="Required databases not found")
        
        # Connect to directors database
        directors_conn = sqlite3.connect(directors_db_path)
        directors_cursor = directors_conn.cursor()
        
        try:
            # Get all directors
            directors_cursor.execute("SELECT id, name, din FROM directors ORDER BY name")
            directors_rows = directors_cursor.fetchall()
            
            directors_with_family = []
            
            # For each director, try to find family information
            for row in directors_rows:
                director_name = row[1]
                family_info = get_family_info_for_director(director_name)
                
                if family_info:
                    directors_with_family.append(family_info)
            
            return directors_with_family
            
        finally:
            directors_conn.close()
            
    except Exception as e:
        logger.error(f"Error getting all directors with family info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get directors with family info: {str(e)}")

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