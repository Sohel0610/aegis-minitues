# SEBI Data Route Module
# This module handles SEBI (Securities and Exchange Board of India) data processing and retrieval operations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures

# Import our PostgreSQL service
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for SEBI data endpoints
router = APIRouter()

# Model for SEBI Excel summary data
class SEBIExcelSummary(BaseModel):
    id: int
    date_key: str
    row_index: int
    pdf_link: Optional[str]
    summary: Optional[str]
    inserted_at: Any # Can be datetime or str
    entity_name: Optional[str] = None
    nature: Optional[str] = None

# Response model for SEBI analysis data
class SEBIAnalysisDataResponse(BaseModel):
    data: List[SEBIExcelSummary]
    count: int

# Endpoint to get SEBI analysis data from the database
@router.get("/sebi-analysis-data", response_model=SEBIAnalysisDataResponse)
async def get_sebi_excel_data(limit: int = 100, offset: int = 0):
    """Get SEBI analysis data from the Azure PostgreSQL database"""
    try:
        # Define the target database name using environment variable
        SEBI_DB = os.getenv('POSTGRES_DATABASE_SEBI') or 'aegis_sebi_db'
        
        # Connect to the database and fetch data
        def fetch_sebi_data():
            conn = get_pg_connection(database=SEBI_DB)
            if not conn:
                raise Exception(f"Could not connect to Azure PostgreSQL database: {SEBI_DB}")
                
            try:
                cursor = get_pg_cursor(conn)
                
                # First, get the total count of records
                cursor.execute("SELECT COUNT(*) FROM aegis_sebi_data")
                total_count = cursor.fetchone()['count']
                
                # Fetch data from aegis_sebi_data table with limit and offset for pagination
                cursor.execute("""
                    SELECT id, date_key, row_index, pdf_link, summary, inserted_at 
                    FROM aegis_sebi_data 
                    ORDER BY date_key DESC, row_index ASC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                rows = cursor.fetchall()
                
                # Data is already in list of dictionaries format due to RealDictCursor
                # But we convert date objects to string for JSON serialization if needed
                for row in rows:
                    if hasattr(row['inserted_at'], 'isoformat'):
                        row['inserted_at'] = row['inserted_at'].isoformat()
                    else:
                        row['inserted_at'] = str(row['inserted_at'])
                
                return rows, total_count
            finally:
                conn.close()
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        data, total_count = await loop.run_in_executor(thread_pool, fetch_sebi_data)
        
        return SEBIAnalysisDataResponse(
            data=data,
            count=total_count
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching SEBI analysis data: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch SEBI analysis data: {error_message}")