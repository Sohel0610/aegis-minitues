# Visit Tracking Route Module
# This module handles visit counting and place management using PostgreSQL
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for visit tracking endpoints
router = APIRouter()

# --- Models ---

class VisitCountResponse(BaseModel):
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

# --- API Endpoints ---

@router.post("/visits/increment")
async def increment_visit_count():
    """Increment visit count in PostgreSQL exclusively."""
    try:
        def increment():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_VISITS'))
            if conn:
                try:
                    cursor = get_pg_cursor(conn)
                    cursor.execute("UPDATE visits SET count = count + 1, last_updated = CURRENT_TIMESTAMP WHERE id = 1")
                    conn.commit()
                finally:
                    conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, increment)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visits/count", response_model=VisitCountResponse)
async def get_visit_count():
    """Get total visits from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_VISITS'))
            if conn:
                try:
                    cursor = get_pg_cursor(conn)
                    cursor.execute("SELECT count FROM visits WHERE id = 1")
                    row = cursor.fetchone()
                    return row["count"] if row else 0
                finally:
                    conn.close()
            return 0
        
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(thread_pool, fetch)
        return VisitCountResponse(count=count)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visits/places", response_model=PlacesListResponse)
async def get_places():
    """Get places from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_VISITS'))
            if conn:
                try:
                    cursor = get_pg_cursor(conn)
                    cursor.execute("SELECT id, name, address, is_default, created_at FROM places ORDER BY name")
                    rows = cursor.fetchall()
                    data = []
                    for row in rows:
                        data.append({
                            'id': row['id'],
                            'name': row['name'],
                            'address': row['address'],
                            'is_default': row['is_default'],
                            'created_at': str(row['created_at'])
                        })
                    return data, len(data)
                finally:
                    conn.close()
            return [], 0
        
        loop = asyncio.get_event_loop()
        data, count = await loop.run_in_executor(thread_pool, fetch)
        return PlacesListResponse(data=data, count=count)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
