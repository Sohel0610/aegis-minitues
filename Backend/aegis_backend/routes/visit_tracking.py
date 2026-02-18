# Visit Tracking Route Module
# This module handles visit tracking functionality
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import logging
import asyncio
import concurrent.futures
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

# Add the parent directory to the path to import utils
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Note: We're not initializing SQLite anymore since we're using PostgreSQL

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for visit tracking endpoints
router = APIRouter()

# Pydantic models for visit tracking
class VisitCountResponse(BaseModel):
    count: int
    message: str

class VisitIncrementResponse(BaseModel):
    success: bool
    new_count: int
    message: str

# Database connection function with fallback
def get_db_connection():
    """Get a connection to the database (PostgreSQL with SQLite fallback)"""
    # 1. Try PostgreSQL if configured
    pg_host = os.getenv('POSTGRES_HOST', 'az10psqldmrcbtp01.postgres.database.azure.com')
    
    try:
        # Check if we can resolve the host first to avoid long timeouts
        import socket
        try:
            socket.gethostbyname(pg_host)
        except socket.gaierror:
             # Host invalid/unreachable, raise exception to trigger fallback
             raise Exception(f"Hostname {pg_host} could not be resolved")

        user = os.getenv('POSTGRES_USER', 'psqladmin')
        password = os.getenv('POSTGRES_PASSWORD', '1k8h02grUu+qJ2uHZb<{lB3LF%+Yj-Ar')
        port = int(os.getenv('POSTGRES_PORT', 5432))
        database = os.getenv('POSTGRES_DATABASE', 'visit_tracking_system')
        
        conn = psycopg2.connect(
            host=pg_host,
            user=user,
            password=password,
            port=port,
            database=database,
            connect_timeout=3 # fast fail
        )
        return conn, "postgres"
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed ({str(e)}). Falling back to SQLite.")
        
        # 2. Fallback to SQLite
        import sqlite3
        # Path to local SQLite db
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "visits.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        # Configure row factory to behave like RealDictCursor
        conn.row_factory = sqlite3.Row
        
        # Ensure table exists (in case db_init didn't run or file was deleted)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Initialize if empty
        cursor.execute("SELECT COUNT(*) FROM visits")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO visits (id, count) VALUES (1, 0)")
        conn.commit()
        
        return conn, "sqlite"

# Endpoint to get the current visit count
@router.get("/visits/count", response_model=VisitCountResponse)
async def get_visit_count():
    """Get the current visit count"""
    try:
        def fetch_visit_count():
            conn = None
            try:
                conn, db_type = get_db_connection()
                
                if db_type == "postgres":
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute("SELECT count FROM visit_tracking.visits WHERE id = 1")
                    result = cursor.fetchone()
                    return result['count'] if result else 0
                else: # sqlite
                    cursor = conn.cursor()
                    cursor.execute("SELECT count FROM visits WHERE id = 1")
                    row = cursor.fetchone()
                    # SQLite Row factory allows access by name, or use index
                    return row['count'] if row else 0
            finally:
                if conn:
                    conn.close()
        
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(thread_pool, fetch_visit_count)
        
        return VisitCountResponse(
            count=count,
            message="Successfully retrieved visit count"
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching visit count: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch visit count: {error_message}")

# Endpoint to increment the visit count by 1
@router.post("/visits/increment", response_model=VisitIncrementResponse)
async def increment_visit_count():
    """Increment the visit count by 1"""
    try:
        def update_visit_count():
            conn = None
            try:
                conn, db_type = get_db_connection()
                
                new_count = 0
                if db_type == "postgres":
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute("UPDATE visit_tracking.visits SET count = count + 1, last_updated = NOW() WHERE id = 1 RETURNING count")
                    result = cursor.fetchone()
                    new_count = result['count'] if result else 0
                    conn.commit()
                else: # sqlite
                    cursor = conn.cursor()
                    # SQLite doesn't support RETURNING in older versions, so we do it in two steps or update first then select
                    cursor.execute("UPDATE visits SET count = count + 1, last_updated = CURRENT_TIMESTAMP WHERE id = 1")
                    if cursor.rowcount == 0:
                        # If row doesn't exist for some reason
                        cursor.execute("INSERT INTO visits (id, count) VALUES (1, 1)")
                    conn.commit()
                    
                    # Fetch the new count
                    cursor.execute("SELECT count FROM visits WHERE id = 1")
                    row = cursor.fetchone()
                    new_count = row['count'] if row else 0
                
                return new_count
            finally:
                if conn:
                    conn.close()
        
        loop = asyncio.get_event_loop()
        new_count = await loop.run_in_executor(thread_pool, update_visit_count)
        
        return VisitIncrementResponse(
            success=True,
            new_count=new_count,
            message="Successfully incremented visit count"
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error incrementing visit count: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to increment visit count: {error_message}")