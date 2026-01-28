# Analytics Route Module
# This module provides analytics endpoints for various financial data sources
from fastapi import APIRouter, HTTPException
import os
import sqlite3
import logging
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for analytics endpoints
router = APIRouter()

# Endpoint to get the count of BSE notifications for the current month
@router.get("/bse-monthly-count")
async def get_bse_monthly_count():
    """Get the count of BSE notifications for the current month"""
    try:
        # Define path to the notifications database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "notifications.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Notifications database file not found")
        
        # Connect to the database and fetch count
        def fetch_bse_monthly_count():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get count of records for current month where Link is not NULL and not 'NIL'
            cursor.execute("""
                SELECT COUNT(*) 
                FROM DailyLogs 
                WHERE Date >= date('now', 'start of month') 
                AND Date < date('now', 'start of month', '+1 month')
                AND Link IS NOT NULL AND Link != 'NIL'
            """)
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return {"count": count}
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(thread_pool, fetch_bse_monthly_count)
        
        return result
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching BSE monthly count: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE monthly count: {error_message}")

# Endpoint to get monthly count of BSE alerts from the notifications database
@router.get("/api/bse-alerts-monthly-count")
async def get_bse_alerts_monthly_count():
    """Get monthly count of BSE alerts from the notifications database"""
    try:
        # Define path to the notifications database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "notifications.db")
       
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="BSE alerts database file not found")
       
        # Connect to the database and fetch data
        def fetch_counts():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
           
            # Get count of records grouped by month
            cursor.execute("""
                SELECT
                    strftime('%Y-%m', Date) as month,
                    COUNT(*) as count
                FROM DailyLogs
                WHERE Link IS NOT NULL AND Link != 'NIL'
                GROUP BY strftime('%Y-%m', Date)
                ORDER BY month DESC
            """)
           
            rows = cursor.fetchall()
           
            # Convert to list of dictionaries
            monthly_data = []
            for row in rows:
                monthly_data.append({
                    'month': row[0],
                    'count': row[1]
                })
           
            # Get total count of all BSE notifications
            cursor.execute("""
                SELECT COUNT(*)
                FROM DailyLogs
                WHERE Link IS NOT NULL AND Link != 'NIL'
            """)
           
            total_count = cursor.fetchone()[0]
           
            # Calculate average notifications per month
            average_count = 0
            if len(monthly_data) > 0:
                total_notifications = sum(item['count'] for item in monthly_data)
                average_count = round(total_notifications / len(monthly_data))
           
            conn.close()
            return monthly_data, total_count, average_count
       
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        monthly_data, total_count, average_count = await loop.run_in_executor(thread_pool, fetch_counts)
       
        return {"monthly_data": monthly_data, "total_count": total_count, "average_count": average_count}
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching BSE alerts monthly count: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE alerts monthly count: {error_message}")

# Endpoint to get total count of BSE alerts for the current month
@router.get("/api/bse-alerts-monthly-total")
async def get_bse_alerts_monthly_total():
    """Get total count of BSE alerts for the current month"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "notifications.db")

        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="BSE alerts database file not found")

        def fetch_total_count():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*)
                FROM DailyLogs
                WHERE Date >= date('now', 'start of month')
                AND Date < date('now', 'start of month', '+1 month')
                AND Link IS NOT NULL AND Link != 'NIL'
            """)

            count = cursor.fetchone()[0]
            conn.close()
            return count

        loop = asyncio.get_event_loop()
        total_count = await loop.run_in_executor(thread_pool, fetch_total_count)

        return {"count": total_count}
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching BSE alerts monthly total count: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE alerts monthly total count: {error_message}")

# Endpoint to get total count of RBI notifications
@router.get("/api/rbi-total-count")
async def get_rbi_total_count():
    """Get total count of RBI notifications"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "rbi.db")

        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="RBI database file not found")

        def fetch_total_count():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) 
                FROM master_summaries 
                WHERE NOT (pdf_link = 'NIL' AND summary = 'NIL')
            """)

            count = cursor.fetchone()[0]
            conn.close()
            return count

        loop = asyncio.get_event_loop()
        total_count = await loop.run_in_executor(thread_pool, fetch_total_count)

        return {"count": total_count}
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching RBI total count: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch RBI total count: {error_message}")

# Endpoint to get total count of SEBI notifications
@router.get("/api/sebi-total-count")
async def get_sebi_total_count():
    """Get total count of SEBI notifications"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "sebi_excel_master.db")

        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="SEBI database file not found")

        def fetch_total_count():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*)  
                FROM excel_summaries 
                WHERE NOT (pdf_link = 'NIL' AND summary = 'NIL')
            """)

            count = cursor.fetchone()[0]
            conn.close()
            return count

        loop = asyncio.get_event_loop()
        total_count = await loop.run_in_executor(thread_pool, fetch_total_count)

        return {"count": total_count}
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching SEBI total count: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch SEBI total count: {error_message}")