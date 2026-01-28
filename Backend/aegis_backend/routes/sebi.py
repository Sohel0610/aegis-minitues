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
    """Get SEBI analysis data from the SEBI database"""
    try:
        # Define the path to the SEBI database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "sebi_excel_master.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="SEBI database file not found")
        
        # Connect to the database and fetch data
        def fetch_sebi_data():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # First, get the total count of records
            cursor.execute("SELECT COUNT(*) FROM excel_summaries")
            total_count = cursor.fetchone()[0]
            
            # Fetch data from excel_summaries table with limit and offset for pagination
            cursor.execute("""
                SELECT id, date_key, row_index, pdf_link, summary, inserted_at 
                FROM excel_summaries 
                ORDER BY date_key DESC, row_index ASC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                record = {
                    'id': row[0],
                    'date_key': row[1],
                    'row_index': row[2],
                    'pdf_link': row[3],
                    'summary': row[4],
                    'inserted_at': row[5]
                }
                data.append(record)
            
            conn.close()
            return data, total_count
        
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