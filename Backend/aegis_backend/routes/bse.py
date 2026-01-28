# BSE Data Route Module
# This module handles BSE (Bombay Stock Exchange) alerts data processing and retrieval operations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
from collections import defaultdict

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for BSE data endpoints
router = APIRouter()

# Model for BSE alerts data
class SEBIExcelSummary(BaseModel):
    id: int
    date_key: str
    row_index: int
    pdf_link: Optional[str]
    summary: Optional[str]
    inserted_at: str
    entity_name: Optional[str] = None
    nature: Optional[str] = None

# Response model for BSE analysis data
class SEBIAnalysisDataResponse(BaseModel):
    data: List[SEBIExcelSummary]
    count: int

# Endpoint to get BSE alerts data from the notifications database
@router.get("/bse-alerts", response_model=SEBIAnalysisDataResponse)
async def get_bse_alerts_data(limit: int = 10000, offset: int = 0):
    """Get BSE alerts data from the notifications database"""
    try:
        # Define path to the notifications database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "notifications.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="BSE alerts database file not found")
        
        # Connect to the database and fetch data
        def fetch_bse_data():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # First, get the total count of records that match our criteria
            cursor.execute("""
                SELECT COUNT(*) 
                FROM DailyLogs 
                WHERE Link IS NOT NULL AND Link != 'NIL'
            """)
            total_count = cursor.fetchone()[0]
            
            # Fetch data from DailyLogs table with limit and offset for pagination
            # Only include records where Link is not NULL and not 'NIL'
            cursor.execute("""
                SELECT SrNo, EntityName, Link, Nature, Summary, Date 
                FROM DailyLogs 
                WHERE Link IS NOT NULL AND Link != 'NIL'
                ORDER BY Date DESC, SrNo ASC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                # Create a dictionary with the expected keys for the frontend
                record = dict(zip(column_names, row))
                
                # Rename keys to match the frontend expectations
                record['id'] = record.pop('SrNo', None)
                record['date_key'] = record.pop('Date', '')
                record['row_index'] = record.pop('SrNo', 0)  # Use SrNo as row_index
                record['pdf_link'] = record.pop('Link', '')
                record['summary'] = record.pop('Summary', '')
                record['inserted_at'] = record.pop('Date', '')  # Use Date as inserted_at
                # Preserve EntityName and Nature for BSE alerts
                if 'EntityName' in record:
                    record['entity_name'] = record.pop('EntityName')
                else:
                    record['entity_name'] = None
                if 'Nature' in record:
                    record['nature'] = record.pop('Nature')
                else:
                    record['nature'] = None
                
                data.append(record)
            
            conn.close()
            
            # Debug: Log some information about the data
            logger.info(f"Fetched {len(data)} BSE alerts records out of {total_count} total records")
            
            # Group by month to show distribution
            monthly_count = defaultdict(int)
            for record in data:
                date_key = record.get('date_key', '')
                if date_key:
                    try:
                        # Extract year-month from date (YYYY-MM-DD format)
                        year_month = date_key[:7]  # First 7 characters: YYYY-MM
                        monthly_count[year_month] += 1
                    except Exception as e:
                        logger.warning(f"Error parsing date {date_key}: {e}")
            
            logger.info(f"Data distribution by month: {dict(monthly_count)}")
            
            return data, total_count
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        data, total_count = await loop.run_in_executor(thread_pool, fetch_bse_data)
        
        # Log the date range of the fetched data
        if data:
            dates = [record.get('date_key') for record in data if record.get('date_key')]
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                logger.info(f"Date range of fetched data: {min_date} to {max_date}")
        
        return SEBIAnalysisDataResponse(
            data=data,
            count=total_count
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching BSE alerts data: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE alerts data: {error_message}")