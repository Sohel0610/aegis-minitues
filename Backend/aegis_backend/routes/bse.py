from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import asyncio
import concurrent.futures
from collections import defaultdict
from utils.pgsql_service import get_pg_connection, get_pg_cursor

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
    """Get BSE alerts data from the Azure PostgreSQL database"""
    try:
        def fetch_bse_data():
            # Get database name from environment
            db_name = os.getenv('POSTGRES_DATABASE_BSE', 'aegis_bse_notification')
            conn = get_pg_connection(database=db_name)
            if not conn:
                raise Exception(f"Failed to connect to PostgreSQL database: {db_name}")
            
            cursor = get_pg_cursor(conn)
            
            try:
                # First, get the total count of records
                # New schema uses 'link' and table 'daily_logs'
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM daily_logs 
                    WHERE link IS NOT NULL AND link != 'NIL'
                """)
                total_count = cursor.fetchone()['count']
                
                # Fetch data from daily_logs table with limit and offset
                # New schema columns: sr_no, entity_name, link, nature, summary, record_date
                cursor.execute("""
                    SELECT id, sr_no, entity_name, link, nature, summary, record_date 
                    FROM daily_logs 
                    WHERE link IS NOT NULL AND link != 'NIL'
                    ORDER BY record_date DESC, id ASC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries with frontend-expected keys
                data = []
                for row in rows:
                    # Map PostgreSQL columns to the format the frontend expects
                    record = {
                        'id': row['id'],
                        'date_key': str(row['record_date']),
                        'row_index': int(row['sr_no']) if row['sr_no'] and str(row['sr_no']).isdigit() else 0,
                        'pdf_link': row['link'],
                        'summary': row['summary'],
                        'inserted_at': str(row['record_date']),
                        'entity_name': row['entity_name'],
                        'nature': row['nature']
                    }
                    data.append(record)
                
                return data, total_count
            finally:
                cursor.close()
                conn.close()
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        data, total_count = await loop.run_in_executor(thread_pool, fetch_bse_data)
        
        # Log the distribution for tracking
        if data:
            monthly_count = defaultdict(int)
            for record in data:
                date_key = record.get('date_key', '')
                if date_key:
                    monthly_count[date_key[:7]] += 1
            logger.info(f"Fetched {len(data)} BSE records. Distribution: {dict(monthly_count)}")
        
        return SEBIAnalysisDataResponse(
            data=data,
            count=total_count
        )
    except Exception as e:
        logger.error(f"Error fetching BSE alerts data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE alerts data: {str(e)}")
