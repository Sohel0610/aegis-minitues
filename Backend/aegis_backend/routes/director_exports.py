import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import asyncio
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

from datetime import datetime
from services.director_export_service import generate_director_excel, create_bulk_zip
from utils.pgsql_service import get_pg_connection, get_pg_cursor

# We reuse the logic from director_full.py by importing its components or re-implementing safely
# Since director_full.py is a script, we'll implement a clean version here for API use

router = APIRouter(prefix="/export", tags=["Director Exports"])
thread_pool = ThreadPoolExecutor(max_workers=5)
export_semaphore = asyncio.Semaphore(10) # Limit concurrent DB connections to protect the pool

async def fetch_consolidated_data(din: str):
    """Internal helper to get the full profile same as director_full.py"""
    pg_conn = None
    try:
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if not pg_conn: raise Exception("DB Connection Failed")
        cursor = get_pg_cursor(pg_conn)
        
        # 1. Master Info
        cursor.execute("SELECT * FROM directors_master.directors WHERE din = %s", (din,))
        master = cursor.fetchone()
        if not master: return None
        
        # 2. Profile Details
        cursor.execute("SELECT * FROM directors_profile.directors_profile WHERE din = %s", (din,))
        profile = cursor.fetchone() or {}
        
        # 3. Associations
        cursor.execute("""
            SELECT a.*, c.status as company_status
            FROM directors_master.external_board_members a
            LEFT JOIN directors_data.companies c ON a.cin = c.cin
            WHERE a.din = %s ORDER BY a.appointment_date DESC
        """, (din,))
        associations = cursor.fetchall() or []
        
        # 4. Family Info (Relational)
        cursor.execute("SELECT * FROM family_information.director_family WHERE din = %s", (din,))
        family_master = cursor.fetchone() or {}
        
        cursor.execute("SELECT * FROM family_information.director_family_members WHERE din = %s", (din,))
        family_members = cursor.fetchall() or []
        
        return {
            "director_info": master,
            "profile": profile,
            "associations": associations,
            "family": family_master,
            "family_members": family_members
        }
    finally:
        if pg_conn: pg_conn.close()

@router.get("/director/{din}")
async def export_single_director(din: str):
    """Download single director Excel"""
    try:
        data = await fetch_consolidated_data(din)
        if not data:
            raise HTTPException(status_code=404, detail="Director not found")
        
        loop = asyncio.get_event_loop()
        excel_buffer = await loop.run_in_executor(thread_pool, generate_director_excel, data)
        
        name = data['director_info'].get('name', 'Director').replace(" ", "_")
        filename = f"Director_Disclosure_{din}_{name}.xlsx"
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting director {din}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bulk-zip")
async def export_all_directors():
    """Download all 194 directors as a ZIP of Excels"""
    try:
        # 1. Get all DINs
        pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        cursor = pg_conn.cursor()
        cursor.execute("SELECT din FROM directors_master.directors")
        dins = [row[0] for row in cursor.fetchall() if row[0]]
        pg_conn.close()

        # 2. Fetch all data with concurrency limit to protect the DB pool
        async def fetch_with_semaphore(din):
            async with export_semaphore:
                return await fetch_consolidated_data(din)

        tasks = [fetch_with_semaphore(din) for din in dins]
        all_data = await asyncio.gather(*tasks)
        all_data = [d for d in all_data if d is not None]

        # 3. Generate ZIP
        loop = asyncio.get_event_loop()
        zip_buffer = await loop.run_in_executor(thread_pool, create_bulk_zip, all_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Aegis_Directors_Disclosures_{timestamp}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Bulk export error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
