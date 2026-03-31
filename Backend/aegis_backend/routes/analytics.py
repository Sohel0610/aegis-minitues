from fastapi import APIRouter, HTTPException
import os
import logging
import asyncio
import concurrent.futures
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for analytics endpoints
router = APIRouter()

# Endpoint to get the count of BSE notifications for the current month
@router.get("/bse-monthly-count")
async def get_bse_monthly_count():
    """Get the count of BSE notifications for the current month using PostgreSQL."""
    try:
        def fetch_bse_monthly_count():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_BSE'))
            if not conn:
                raise RuntimeError("Failed to connect to PostgreSQL")
            
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT COUNT(*) AS count
                    FROM daily_logs
                    WHERE record_date >= DATE_TRUNC('month', CURRENT_DATE)
                    AND record_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                    AND link IS NOT NULL AND link != 'NIL'
                """)
                row = cursor.fetchone()
                return {"count": row["count"] if row else 0}
            finally:
                cursor.close()
                conn.close()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, fetch_bse_monthly_count)
    except Exception as e:
        logger.error(f"Error fetching BSE monthly count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE monthly count: {str(e)}")

# Endpoint to get monthly count of BSE alerts
@router.get("/bse-alerts-monthly-count")
async def get_bse_alerts_monthly_count():
    """Get monthly count of BSE alerts using PostgreSQL."""
    try:
        def fetch_counts():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_BSE'))
            if not conn:
                raise RuntimeError("Failed to connect to PostgreSQL")
            
            cursor = get_pg_cursor(conn)
            try:
                # Use default public schema
                cursor.execute("""
                    SELECT
                        TO_CHAR(record_date, 'YYYY-MM') as month,
                        COUNT(*) as count
                    FROM daily_logs
                    WHERE link IS NOT NULL AND link != 'NIL'
                    GROUP BY TO_CHAR(record_date, 'YYYY-MM')
                    ORDER BY month DESC
                """)
                rows = cursor.fetchall()
                monthly_data = [{"month": row["month"], "count": int(row["count"])} for row in rows]

                cursor.execute("SELECT COUNT(*) AS count FROM daily_logs WHERE link IS NOT NULL AND link != 'NIL'")
                row_total = cursor.fetchone()
                total_count = row_total["count"] if row_total else 0

                average_count = 0
                if monthly_data:
                    total_notifications = sum(item["count"] for item in monthly_data)
                    average_count = round(total_notifications / len(monthly_data))

                return monthly_data, int(total_count), int(average_count)
            finally:
                cursor.close()
                conn.close()
        
        loop = asyncio.get_event_loop()
        monthly_data, total_count, average_count = await loop.run_in_executor(thread_pool, fetch_counts)
        return {"monthly_data": monthly_data, "total_count": total_count, "average_count": average_count}
    except Exception as e:
        logger.error(f"Error fetching BSE monthly counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get total count of BSE alerts for the current month
@router.get("/bse-alerts-monthly-total")
async def get_bse_alerts_monthly_total():
    """Get total count of BSE alerts for the current month using PostgreSQL."""
    try:
        def fetch_total_count():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_BSE'))
            if not conn: return 0
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT COUNT(*) AS count
                    FROM daily_logs
                    WHERE record_date >= DATE_TRUNC('month', CURRENT_DATE)
                    AND record_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                    AND link IS NOT NULL AND link != 'NIL'
                """)
                row = cursor.fetchone()
                return int(row["count"]) if row else 0
            finally:
                cursor.close()
                conn.close()

        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(thread_pool, fetch_total_count)
        return {"count": count}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get total count of RBI notifications
@router.get("/rbi-total-count")
async def get_rbi_total_count():
    """Get total count of RBI notifications from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBI'))
            if not conn: return 0
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM master_summaries 
                    WHERE pdf_link IS NOT NULL AND pdf_link != 'NIL'
                """)
                row = cursor.fetchone()
                return int(row["count"]) if row else 0
            finally:
                cursor.close()
                conn.close()
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(thread_pool, fetch)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get total count of SEBI notifications
@router.get("/sebi-total-count")
async def get_sebi_total_count():
    """Get total count of SEBI notifications from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_BSE'))
            if not conn: return 0
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM excel_summaries 
                    WHERE pdf_link IS NOT NULL AND pdf_link != 'NIL'
                """)
                row = cursor.fetchone()
                return int(row["count"]) if row else 0
            finally:
                cursor.close()
                conn.close()
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(thread_pool, fetch)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
