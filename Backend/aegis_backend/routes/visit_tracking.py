from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import logging
import asyncio
import concurrent.futures
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import sqlite3

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logger = logging.getLogger(__name__)
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
router = APIRouter()

class VisitCountResponse(BaseModel):
    count: int
    message: str

class VisitIncrementResponse(BaseModel):
    success: bool
    new_count: int
    message: str

def get_db_connection():
    pg_host = os.getenv('POSTGRES_HOST')
    if not pg_host:
        return None, "sqlite_fallback"

    try:
        import socket
        socket.gethostbyname(pg_host.strip().strip("'").strip('"'))
        
        user = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        port = int(os.getenv('POSTGRES_PORT', 5432))
        database = os.getenv('POSTGRES_DATABASE', 'visit_tracking_system')
        
        if not all([user, password]):
            return None, "sqlite_fallback"

        conn_params = {
            'host': pg_host.strip().strip("'").strip('"'),
            'user': user.strip().strip("'").strip('"').lstrip('='),
            'password': password.strip().strip("'").strip('"'),
            'port': port,
            'database': database.strip().strip("'").strip('"'),
            'connect_timeout': 3
        }
        
        if 'azure.com' in pg_host.lower():
            conn_params['sslmode'] = 'require'

        conn = psycopg2.connect(**conn_params)
        return conn, "postgres"
    except Exception as e:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "visits.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS visits (id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("SELECT COUNT(*) FROM visits")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO visits (id, count) VALUES (1, 0)")
        conn.commit()
        return conn, "sqlite"

@router.get("/visits/count", response_model=VisitCountResponse)
async def get_visit_count():
    try:
        def fetch_visit_count():
            conn = None
            try:
                conn, db_type = get_db_connection()
                if not conn and db_type == "sqlite_fallback":
                     db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "visits.db")
                     conn = sqlite3.connect(db_path)
                     conn.row_factory = sqlite3.Row
                     db_type = "sqlite"

                if db_type == "postgres":
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute("SELECT count FROM visit_tracking.visits WHERE id = 1")
                    result = cursor.fetchone()
                    return result['count'] if result else 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("SELECT count FROM visits WHERE id = 1")
                    row = cursor.fetchone()
                    return row['count'] if row else 0
            finally:
                if conn: conn.close()
        
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(thread_pool, fetch_visit_count)
        return VisitCountResponse(count=count, message="Success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visits/increment", response_model=VisitIncrementResponse)
async def increment_visit_count():
    try:
        def update_visit_count():
            conn = None
            try:
                conn, db_type = get_db_connection()
                if not conn and db_type == "sqlite_fallback":
                     db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "visits.db")
                     conn = sqlite3.connect(db_path)
                     conn.row_factory = sqlite3.Row
                     db_type = "sqlite"

                new_count = 0
                if db_type == "postgres":
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute("UPDATE visit_tracking.visits SET count = count + 1, last_updated = NOW() WHERE id = 1 RETURNING count")
                    result = cursor.fetchone()
                    new_count = result['count'] if result else 0
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE visits SET count = count + 1, last_updated = CURRENT_TIMESTAMP WHERE id = 1")
                    if cursor.rowcount == 0:
                        cursor.execute("INSERT INTO visits (id, count) VALUES (1, 1)")
                    conn.commit()
                    cursor.execute("SELECT count FROM visits WHERE id = 1")
                    row = cursor.fetchone()
                    new_count = row['count'] if row else 0
                return new_count
            finally:
                if conn: conn.close()
        
        loop = asyncio.get_event_loop()
        new_count = await loop.run_in_executor(thread_pool, update_visit_count)
        return VisitIncrementResponse(success=True, new_count=new_count, message="Success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))