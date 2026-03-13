from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
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

def _get_notifications_sqlite_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "public", "notifications.db")

def _fetch_bse_data_sqlite(limit: int, offset: int):
    """SQLite fallback for BSE alerts (uses public/notifications.db DailyLogs)."""
    db_path = _get_notifications_sqlite_path()
    if not os.path.exists(db_path):
        # Create an empty DB with the expected schema so the API can still respond.
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS DailyLogs (
                    SrNo TEXT,
                    EntityName TEXT,
                    Link TEXT,
                    Nature TEXT,
                    Summary TEXT,
                    Date TEXT
                )
            """)
            conn.commit()
        finally:
            try:
                cur.close()
            finally:
                conn.close()
        return [], 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM DailyLogs
            WHERE Link IS NOT NULL AND Link != 'NIL'
        """)
        total_count = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT
                rowid AS id,
                SrNo AS sr_no,
                EntityName AS entity_name,
                Link AS link,
                Nature AS nature,
                Summary AS summary,
                Date AS record_date
            FROM DailyLogs
            WHERE Link IS NOT NULL AND Link != 'NIL'
            ORDER BY Date DESC, rowid ASC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cur.fetchall()

        data = []
        for row in rows:
            sr_no = row["sr_no"]
            try:
                row_index = int(sr_no) if sr_no is not None else 0
            except Exception:
                row_index = 0

            record_date = row["record_date"]
            record = {
                "id": int(row["id"]),
                "date_key": str(record_date) if record_date is not None else "",
                "row_index": row_index,
                "pdf_link": row["link"],
                "summary": row["summary"],
                "inserted_at": str(record_date) if record_date is not None else "",
                "entity_name": row["entity_name"],
                "nature": row["nature"],
            }
            data.append(record)

        return data, int(total_count)
    finally:
        try:
            cur.close()
        finally:
            conn.close()

# Endpoint to get BSE alerts data from the notifications database
@router.get("/bse-alerts", response_model=SEBIAnalysisDataResponse)
async def get_bse_alerts_data(limit: int = 10000, offset: int = 0):
    """Get BSE alerts data from PostgreSQL (fallback to local SQLite)."""
    try:
        def fetch_bse_data():
            try:
                # Get database name from environment
                db_name = os.getenv("POSTGRES_DATABASE_BSE", "aegis_bse_notification")
                conn = get_pg_connection(database=db_name)
                if conn:
                    cursor = get_pg_cursor(conn)
                    try:
                        # First, get the total count of records
                        # New schema uses 'link' and table 'daily_logs'
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM daily_logs
                            WHERE link IS NOT NULL AND link != 'NIL'
                        """)
                        total_count = cursor.fetchone()["count"]

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
                            sr_no = row["sr_no"]
                            try:
                                row_index = int(sr_no) if sr_no is not None else 0
                            except Exception:
                                row_index = 0

                            record_date = row["record_date"]
                            record = {
                                "id": row["id"],
                                "date_key": str(record_date),
                                "row_index": row_index,
                                "pdf_link": row["link"],
                                "summary": row["summary"],
                                "inserted_at": str(record_date),
                                "entity_name": row["entity_name"],
                                "nature": row["nature"],
                            }
                            data.append(record)

                        return data, int(total_count)
                    finally:
                        try:
                            cursor.close()
                        finally:
                            conn.close()
            except Exception as e:
                logger.warning(f"BSE PG fetch failed, falling back to SQLite: {e}")

            return _fetch_bse_data_sqlite(limit=limit, offset=offset)
        
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
