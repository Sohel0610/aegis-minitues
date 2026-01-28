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

# PostgreSQL connection function
def get_db_connection():
    """Get a connection to the PostgreSQL database"""
    # Set default values for Azure PostgreSQL if environment variables are not set
    host = os.getenv('POSTGRES_HOST', 'az10psqldmrcbtp01.postgres.database.azure.com')
    user = os.getenv('POSTGRES_USER', 'psqladmin')
    password = os.getenv('POSTGRES_PASSWORD', '1k8h02grUu+qJ2uHZb<{lB3LF%+Yj-Ar')
    port = int(os.getenv('POSTGRES_PORT', 5432))
    database = os.getenv('POSTGRES_DATABASE', 'visit_tracking_system')
    
    return psycopg2.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        database=database
    )

# Endpoint to get the current visit count
@router.get("/visits/count", response_model=VisitCountResponse)
async def get_visit_count():
    """Get the current visit count from PostgreSQL"""
    try:
        def fetch_visit_count():
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT count FROM visit_tracking.visits WHERE id = 1")
            result = cursor.fetchone()
            conn.close()
            return result['count'] if result else 0
        
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
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("UPDATE visit_tracking.visits SET count = count + 1, last_updated = NOW() WHERE id = 1 RETURNING count")
            result = cursor.fetchone()
            new_count = result['count'] if result else 0
            conn.commit()
            conn.close()
            return new_count
        
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