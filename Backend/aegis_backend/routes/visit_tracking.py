from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import logging
import asyncio
import concurrent.futures
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
router = APIRouter()

# Postgres Schema
DB_SCHEMA = "tracking"

class VisitCountResponse(BaseModel):
    count: int
    message: str

class VisitIncrementResponse(BaseModel):
    success: bool
    new_count: int
    message: str

@router.get("/visits/count", response_model=VisitCountResponse)
async def get_visit_count():
    """Get visit count from PostgreSQL exclusively."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE'))
            if not conn: return 0
            cursor = get_pg_cursor(conn)
            try:
                # Table is tracking.visits
                cursor.execute(f"SELECT count FROM {DB_SCHEMA}.visits WHERE id = 1")
                row = cursor.fetchone()
                return row['count'] if row else 0
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(thread_pool, fetch)
        return VisitCountResponse(count=count, message="Success")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visits/increment", response_model=VisitIncrementResponse)
async def increment_visit_count():
    """Increment visit count in PostgreSQL exclusively."""
    try:
        def update():
            conn = get_pg_connection()
            if not conn: return 0
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute(f"UPDATE {DB_SCHEMA}.visits SET count = count + 1, last_updated = CURRENT_TIMESTAMP WHERE id = 1 RETURNING count")
                res = cursor.fetchone()
                if not res:
                    cursor.execute(f"INSERT INTO {DB_SCHEMA}.visits (id, count) VALUES (1, 1) RETURNING count")
                    res = cursor.fetchone()
                conn.commit()
                return res['count'] if res else 0
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        new_count = await loop.run_in_executor(thread_pool, update)
        return VisitIncrementResponse(success=True, new_count=new_count, message="Success")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
