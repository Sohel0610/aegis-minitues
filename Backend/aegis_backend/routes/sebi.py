# SEBI Data Route Module
# This module handles SEBI (Securities and Exchange Board of India) data processing using PostgreSQL
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import asyncio
import concurrent.futures
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
    inserted_at: str
    entity_name: Optional[str] = None
    nature: Optional[str] = None

# Response model for SEBI analysis data
class SEBIAnalysisDataResponse(BaseModel):
    data: List[SEBIExcelSummary]
    count: int

# Endpoint to get SEBI analysis data from the database
@router.get("/sebi-analysis-data", response_model=SEBIAnalysisDataResponse)
async def get_sebi_excel_data(limit: int = 100, offset: int = 0):
    """Get SEBI analysis data from PostgreSQL exclusively."""
    # Production Database Selection
    target_db = os.getenv('POSTGRES_DATABASE_SEBI') or os.getenv('POSTGRES_DATABASE_BSE')
    
    try:
        def fetch_sebi_data():
            conn = get_pg_connection(target_db)
            if not conn:
                logger.error(f"Failed to connect to PG database ({target_db}) for SEBI alerts")
                raise HTTPException(status_code=500, detail="Database connection failed")
            
            cursor = get_pg_cursor(conn)
            try:
                # First, get the total count of records
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM excel_summaries
                """)
                row = cursor.fetchone()
                total_count = row["count"] if row else 0
                
                # Fetch data from excel_summaries table
                cursor.execute("""
                    SELECT id, date_key, row_index, pdf_link, summary, inserted_at
                    FROM excel_summaries
                    ORDER BY date_key DESC, row_index ASC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries with frontend-expected keys
                data = []
                for row in rows:
                    record = {
                        'id': row['id'],
                        'date_key': str(row['date_key']),
                        'row_index': row['row_index'],
                        'pdf_link': row['pdf_link'],
                        'summary': row['summary'],
                        'inserted_at': str(row['inserted_at'])
                    }
                    data.append(record)
                
                return data, total_count
            finally:
                cursor.close()
                conn.close()
        
        loop = asyncio.get_event_loop()
        data, total_count = await loop.run_in_executor(thread_pool, fetch_sebi_data)
        
        return SEBIAnalysisDataResponse(
            data=data,
            count=total_count
        )
    except Exception as e:
        logger.error(f"Error fetching SEBI analysis data: {e}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))