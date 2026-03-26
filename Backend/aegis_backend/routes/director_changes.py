from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from datetime import datetime

# Import our PostgreSQL service
from utils.pgsql_service import get_pg_connection, get_pg_cursor

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

def init_db():
    """Verify/Initialize the director changes PG table"""
    pg_conn = None
    try:
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            
            # Create changes table in directors_master schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS directors_master.director_changes (
                    id SERIAL PRIMARY KEY,
                    director_id INTEGER,
                    director_name TEXT,
                    change_type TEXT,
                    description TEXT,
                    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            pg_conn.commit()
            logger.info("Director changes PostgreSQL table verified")
    except Exception as e:
        logger.error(f"Failed to initialize director changes PG table: {e}")
    finally:
        if pg_conn:
            pg_conn.close()

# Initialize on import
init_db()

# Models
class ChangeLog(BaseModel):
    id: int
    director_name: str
    change_type: str
    description: str
    changed_at: str

class ChangesResponse(BaseModel):
    data: List[ChangeLog]
    count: int

# Utility function to log a change
def log_director_change(director_id: Optional[int], director_name: str, change_type: str, description: str):
    """Log a change to the PostgreSQL database"""
    pg_conn = None
    try:
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            
            cursor.execute('''
                INSERT INTO directors_master.director_changes (director_id, director_name, change_type, description, changed_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (director_id, director_name, change_type, description, datetime.now()))
            
            pg_conn.commit()
    except Exception as e:
        logger.error(f"Failed to log director change to PG: {e}")
    finally:
        if pg_conn:
            pg_conn.close()

# API Endpoints
@router.get("/director-disclosure-changes", response_model=ChangesResponse)
async def get_director_changes():
    """Get all director disclosure changes ordered by date from PG"""
    pg_conn = None
    try:
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if pg_conn:
            cursor = get_pg_cursor(pg_conn)
            
            cursor.execute("SELECT * FROM directors_master.director_changes ORDER BY changed_at DESC")
            rows = cursor.fetchall()
            
            changes = []
            for row in rows:
                changes.append({
                    "id": row["id"],
                    "director_name": row["director_name"],
                    "change_type": row["change_type"],
                    "description": row["description"],
                    "changed_at": row["changed_at"].isoformat() if hasattr(row["changed_at"], 'isoformat') else str(row["changed_at"])
                })
            
            return {
                "data": changes,
                "count": len(changes)
            }
        else:
            raise HTTPException(status_code=500, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Error fetching director changes from PG: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch changes: {e}")
    finally:
        if pg_conn:
            pg_conn.close()
