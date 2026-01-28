# RBI Data Route Module
# This module handles RBI (Reserve Bank of India) data processing and retrieval operations
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
    """Get RBI analysis data from the RBI database"""
    try:
        # Define the path to the RBI database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "rbi.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="RBI database file not found")
        
        # Connect to the database and fetch data
        def fetch_rbi_data():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # First, get the total count of records that match our criteria
            cursor.execute("""
                SELECT COUNT(*) 
                FROM master_summaries 
                WHERE NOT (pdf_link = 'NIL' AND summary = 'NIL')
            """)
            total_count = cursor.fetchone()[0]
            
            # Fetch data from master_summaries table with limit and offset for pagination
            # Only exclude records where both pdf_link and summary are 'NIL'
            cursor.execute("""
                SELECT id, run_date, pdf_link, summary, created_at 
                FROM master_summaries 
                WHERE NOT (pdf_link = 'NIL' AND summary = 'NIL')
                ORDER BY run_date DESC, id ASC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                record = {
                    'id': row[0],
                    'date_key': row[1],  # Using date_key to match frontend expectations
                    'row_index': row[0],  # Using id as row_index
                    'pdf_link': row[2],
                    'summary': row[3],
                    'inserted_at': row[4]
                }
                data.append(record)
            
            conn.close()
            return data, total_count
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        data, total_count = await loop.run_in_executor(thread_pool, fetch_rbi_data)
        
        return SEBIAnalysisDataResponse(
            data=data,
            count=total_count
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching RBI analysis data: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch RBI analysis data: {error_message}")