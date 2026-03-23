from fastapi import APIRouter, HTTPException
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for analytics endpoints
router = APIRouter()

# SQLite fallback path for BSE notifications
def _get_notifications_sqlite_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "public", "notifications.db")

# Helper to get the database name
def get_bse_db_name():
    return os.getenv('POSTGRES_DATABASE_BSE', 'aegis_bse_notification')

# Endpoint to get the count of BSE notifications for the current month
@router.get("/bse-monthly-count")
async def get_bse_monthly_count():
    """Get the count of BSE notifications for the current month (PostgreSQL, fallback to SQLite)."""
    try:
        def fetch_bse_monthly_count():
            try:
                db_name = get_bse_db_name()
                conn = get_pg_connection(database=db_name)
                if conn:
                    cursor = get_pg_cursor(conn)
                    try:
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM daily_logs
                            WHERE record_date >= DATE_TRUNC('month', CURRENT_DATE)
                            AND record_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                            AND link IS NOT NULL AND link != 'NIL'
                        """)
                        count = cursor.fetchone()["count"]
                        return {"count": count}
                    finally:
                        try:
                            cursor.close()
                        finally:
                            conn.close()
            except Exception as e:
                logger.warning(f"BSE monthly count PG fetch failed, falling back to SQLite: {e}")

            db_path = _get_notifications_sqlite_path()
            if not os.path.exists(db_path):
                return {"count": 0}

            sconn = sqlite3.connect(db_path)
            scur = sconn.cursor()
            try:
                scur.execute("""
                    SELECT COUNT(*)
                    FROM DailyLogs
                    WHERE Date >= date('now', 'start of month')
                      AND Date <  date('now', 'start of month', '+1 month')
                      AND Link IS NOT NULL AND Link != 'NIL'
                """)
                count = scur.fetchone()[0] or 0
                return {"count": int(count)}
            finally:
                try:
                    scur.close()
                finally:
                    sconn.close()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(thread_pool, fetch_bse_monthly_count)
        return result
    except Exception as e:
        logger.error(f"Error fetching BSE monthly count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE monthly count: {str(e)}")

# Endpoint to get monthly count of BSE alerts from PostgreSQL
@router.get("/bse-alerts-monthly-count")
async def get_bse_alerts_monthly_count():
    """Get monthly count of BSE alerts (PostgreSQL, fallback to SQLite)."""
    try:
        def fetch_counts():
            try:
                db_name = get_bse_db_name()
                conn = get_pg_connection(database=db_name)
                if conn:
                    cursor = get_pg_cursor(conn)
                    try:
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
                        monthly_data = [{"month": row["month"], "count": row["count"]} for row in rows]

                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM daily_logs
                            WHERE link IS NOT NULL AND link != 'NIL'
                        """)
                        total_count = cursor.fetchone()["count"]

                        average_count = 0
                        if monthly_data:
                            total_notifications = sum(item["count"] for item in monthly_data)
                            average_count = round(total_notifications / len(monthly_data))

                        return monthly_data, int(total_count), int(average_count)
                    finally:
                        try:
                            cursor.close()
                        finally:
                            conn.close()
            except Exception as e:
                logger.warning(f"BSE monthly counts PG fetch failed, falling back to SQLite: {e}")

            db_path = _get_notifications_sqlite_path()
            if not os.path.exists(db_path):
                return [], 0, 0

            sconn = sqlite3.connect(db_path)
            sconn.row_factory = sqlite3.Row
            scur = sconn.cursor()
            try:
                scur.execute("""
                    SELECT
                        substr(Date, 1, 7) AS month,
                        COUNT(*) AS count
                    FROM DailyLogs
                    WHERE Link IS NOT NULL AND Link != 'NIL'
                    GROUP BY substr(Date, 1, 7)
                    ORDER BY month DESC
                """)
                rows = scur.fetchall()
                monthly_data = [{"month": row["month"], "count": row["count"]} for row in rows]

                scur.execute("""
                    SELECT COUNT(*)
                    FROM DailyLogs
                    WHERE Link IS NOT NULL AND Link != 'NIL'
                """)
                total_count = scur.fetchone()[0] or 0

                average_count = 0
                if monthly_data:
                    total_notifications = sum(int(item["count"]) for item in monthly_data)
                    average_count = round(total_notifications / len(monthly_data))

                return monthly_data, int(total_count), int(average_count)
            finally:
                try:
                    scur.close()
                finally:
                    sconn.close()
        
        loop = asyncio.get_event_loop()
        monthly_data, total_count, average_count = await loop.run_in_executor(thread_pool, fetch_counts)
        return {"monthly_data": monthly_data, "total_count": total_count, "average_count": average_count}
    except Exception as e:
        logger.error(f"Error fetching BSE alerts monthly count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE alerts monthly count: {str(e)}")

# Endpoint to get total count of BSE alerts for the current month
@router.get("/bse-alerts-monthly-total")
async def get_bse_alerts_monthly_total():
    """Get total count of BSE alerts for the current month (PostgreSQL, fallback to SQLite)."""
    try:
        def fetch_total_count():
            try:
                db_name = get_bse_db_name()
                conn = get_pg_connection(database=db_name)
                if conn:
                    cursor = get_pg_cursor(conn)
                    try:
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM daily_logs
                            WHERE record_date >= DATE_TRUNC('month', CURRENT_DATE)
                            AND record_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                            AND link IS NOT NULL AND link != 'NIL'
                        """)
                        return int(cursor.fetchone()["count"])
                    finally:
                        try:
                            cursor.close()
                        finally:
                            conn.close()
            except Exception as e:
                logger.warning(f"BSE monthly total PG fetch failed, falling back to SQLite: {e}")

            db_path = _get_notifications_sqlite_path()
            if not os.path.exists(db_path):
                return 0

            sconn = sqlite3.connect(db_path)
            scur = sconn.cursor()
            try:
                scur.execute("""
                    SELECT COUNT(*)
                    FROM DailyLogs
                    WHERE Date >= date('now', 'start of month')
                      AND Date <  date('now', 'start of month', '+1 month')
                      AND Link IS NOT NULL AND Link != 'NIL'
                """)
                return int(scur.fetchone()[0] or 0)
            finally:
                try:
                    scur.close()
                finally:
                    sconn.close()

        loop = asyncio.get_event_loop()
        total_count = await loop.run_in_executor(thread_pool, fetch_total_count)
        return {"count": total_count}
    except Exception as e:
        logger.error(f"Error fetching BSE alerts monthly total count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BSE alerts monthly total count: {str(e)}")

# Endpoint to get total count of RBI notifications
@router.get("/rbi-total-count")
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
@router.get("/sebi-total-count")
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

# Endpoint to get total count of RBI notifications
@router.get("/rbi-total-count")
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
@router.get("/sebi-total-count")
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
