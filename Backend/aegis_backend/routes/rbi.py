# RBI Data Route Module
# This module handles RBI (Reserve Bank of India) data processing using PostgreSQL
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

# Create a router instance for RBI data endpoints
router = APIRouter()

# Model for RBI data summaries
class SEBIExcelSummary(BaseModel):
    id: int
    date_key: str
    row_index: int
    pdf_link: Optional[str]
    summary: Optional[str]
    inserted_at: str

# Response model for RBI analysis data
class SEBIAnalysisDataResponse(BaseModel):
    data: List[SEBIExcelSummary]
    count: int

# Endpoint to get RBI analysis data from the database
@router.get("/rbi-analysis-data", response_model=SEBIAnalysisDataResponse)
async def get_rbi_excel_data(limit: int = 100, offset: int = 0):
    """Get RBI analysis data from PostgreSQL exclusively."""
    try:
        def fetch_rbi_data():
            conn = get_pg_connection()
            if not conn:
                logger.error("Failed to connect to PG database for RBI alerts")
                raise HTTPException(status_code=500, detail="Database connection failed")
            
            cursor = get_pg_cursor(conn)
            try:
                # First, get the total count
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM master_summaries 
                    WHERE NOT (pdf_link = 'NIL' AND summary = 'NIL')
                """)
                row = cursor.fetchone()
                total_count = row["count"] if row else 0
                
                # Fetch data
                cursor.execute("""
                    SELECT id, run_date, pdf_link, summary, created_at 
                    FROM master_summaries 
                    WHERE NOT (pdf_link = 'NIL' AND summary = 'NIL')
                    ORDER BY run_date DESC, id ASC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                data = []
                for row in rows:
                    record = {
                        'id': row['id'],
                        'date_key': str(row['run_date']),
                        'row_index': row['id'],
                        'pdf_link': row['pdf_link'],
                        'summary': row['summary'],
                        'inserted_at': str(row['created_at'])
                    }
                    data.append(record)
                
                return data, total_count
            finally:
                cursor.close()
                conn.close()
        
        loop = asyncio.get_event_loop()
        data, total_count = await loop.run_in_executor(thread_pool, fetch_rbi_data)
        
        return SEBIAnalysisDataResponse(
            data=data,
            count=total_count
        )
    except Exception as e:
        logger.error(f"Error fetching RBI analysis data: {e}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))