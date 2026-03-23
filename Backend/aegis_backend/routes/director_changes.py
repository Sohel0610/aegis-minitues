
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import logging
from datetime import datetime
import threading

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "director_changes.db")
db_lock = threading.Lock()

def init_db():
    """Initialize the director changes database"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create changes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS director_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                director_id INTEGER,
                director_name TEXT,
                change_type TEXT,
                description TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Director changes database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize director changes database: {e}")

# Initialize DB on import
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
    """Log a change to the database"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO director_changes (director_id, director_name, change_type, description, changed_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (director_id, director_name, change_type, description, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            logger.info(f"Logged change for {director_name}: {change_type}")
    except Exception as e:
        logger.error(f"Failed to log director change: {e}")

# API Endpoints
@router.get("/director-disclosure-changes", response_model=ChangesResponse)
async def get_director_changes():
    """Get all director disclosure changes ordered by date (newest first)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM director_changes ORDER BY changed_at DESC")
        rows = cursor.fetchall()
        
        changes = []
        for row in rows:
            changes.append({
                "id": row["id"],
                "director_name": row["director_name"],
                "change_type": row["change_type"],
                "description": row["description"],
                "changed_at": row["changed_at"]
            })
            
        conn.close()
        
        return {
            "data": changes,
            "count": len(changes)
        }
    except Exception as e:
        logger.error(f"Error fetching director changes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch changes: {e}")
