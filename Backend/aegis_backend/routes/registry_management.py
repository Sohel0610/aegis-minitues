from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import subprocess
import psycopg2
from typing import List, Optional, Union
import pandas as pd
import io
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.pgsql_service import get_pg_connection, get_pg_cursor
import logging
import json
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registry", tags=["Registry Management"])

# Function to find the Director_Disclosure scripts robustly
def find_script(possible_names: Union[str, List[str]]) -> Path:
    """Search for the script recursively starting from the root of the Backend."""
    if isinstance(possible_names, str):
        possible_names = [possible_names]
        
    current = Path(__file__).resolve().parent
    root = current
    for _ in range(5):
        if root.name == "Backend" or (root / "Director_Disclosure").exists():
            break
        root = root.parent
        
    logger.info(f"Searching for {possible_names} in root: {root}")
    
    for dirpath, dirnames, filenames in os.walk(str(root)):
        for name in possible_names:
            if name in filenames:
                found_path = Path(dirpath) / name
                logger.info(f"Found script at: {found_path}")
                return found_path
            
    # Fallback to the first name in the list
    return root / "Director_Disclosure" / possible_names[0]

SYNC_DIN_SCRIPT = find_script(["sync_director_registry.py", "sync_director_details.py"])
SYNC_CIN_SCRIPT = find_script(["sync_company_details.py", "sync_company_registry.py"])
MBP1_SCRIPT = find_script(["mbp1_generator.py", "mbp1_gen.py"])
DIR8_SCRIPT = find_script(["dir8_generator.py", "dir8_gen.py"])

class SyncRequest(BaseModel):
    items: List[str]  # DINs or CINs

class GenerateRequest(BaseModel):
    din: Optional[str] = None
    cin: Optional[str] = None
    cins: Optional[List[str]] = None
    all_directors: bool = False
    year: str = "2024-25"

def run_script(script_path: Path, args: List[str]):
    """Helper to run a script as a subprocess with architect-grade logging."""
    if not script_path or not script_path.exists():
        msg = f"CRITICAL ERROR: Script not found at expected path: {script_path}"
        logger.error(msg)
        raise Exception(msg)
        
    try:
        cmd = [sys.executable, str(script_path)] + args
        
        print("\n" + "="*80)
        print(f"🚀 REGISTRY TASK STARTED: {script_path.name}")
        print(f"📂 Path: {script_path}")
        print(f"🔧 Command: {' '.join(cmd)}")
        print("="*80 + "\n")
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Set cwd to script's directory
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True, 
            cwd=str(script_path.parent)
        )
        
        print("\n" + "-"*40)
        print(f"✅ TASK COMPLETED: {script_path.name}")
        if result.stdout:
            print(f"📄 Output Snippet:\n{result.stdout[:500]}...")
        print("-"*40 + "\n")
        
        if result.stdout:
            logger.info(f"Script Output:\n{result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("\n" + "!"*80)
        print(f"❌ TASK FAILED: {script_path.name}")
        print(f"🛑 Error: {e.stderr}")
        print("!"*80 + "\n")
        
        error_msg = f"Execution failed for {script_path.name}.\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
        logger.error(error_msg)
        raise Exception(f"Task Failed: {script_path.name}. Check terminal logs for details.")

@router.get("/unsynced-cins")
async def get_unsynced_cins():
    """Find CINs found in director associations but missing from the companies master table."""
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Query to find CINs in associations but not in companies
        cur.execute("""
            SELECT DISTINCT ebm.cin, ebm.company_name 
            FROM directors_master.external_board_members ebm
            LEFT JOIN directors_data.companies c ON ebm.cin = c.cin
            WHERE c.cin IS NULL 
              AND ebm.cin IS NOT NULL 
              AND ebm.cin != 'N/A'
              AND ebm.cin != ''
            ORDER BY ebm.company_name ASC
        """)
        unsynced = cur.fetchall()
        return {"count": len(unsynced), "items": unsynced}
    finally:
        cur.close()
        conn.close()

@router.post("/sync/din")
async def sync_dins(request: SyncRequest, background_tasks: BackgroundTasks):
    """Sync one or more DINs."""
    for din in request.items:
        background_tasks.add_task(run_script, SYNC_DIN_SCRIPT, [din])
    return {"message": f"Started sync for {len(request.items)} DINs in background."}

@router.post("/sync/din/upload")
async def upload_dins_for_sync(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload an Excel/CSV file with DINs and sync them."""
    try:
        content = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Look for columns named 'din' or 'DIN'
        din_col = next((c for c in df.columns if c.lower() == 'din'), None)
        if not din_col:
            raise HTTPException(status_code=400, detail="File must contain a column named 'DIN'")
        
        dins = [str(d).strip().zfill(8) for d in df[din_col].dropna().unique()]
        if not dins:
            raise HTTPException(status_code=400, detail="No DINs found in file")
            
        for din in dins:
            background_tasks.add_task(run_script, SYNC_DIN_SCRIPT, [din])
            
        return {"message": f"Started bulk sync for {len(dins)} DINs extracted from {file.filename}."}
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.post("/sync/cin")
async def sync_cins(request: SyncRequest, background_tasks: BackgroundTasks):
    """Sync one or more CINs."""
    for cin in request.items:
        background_tasks.add_task(run_script, SYNC_CIN_SCRIPT, [cin])
    return {"message": f"Started sync for {len(request.items)} CINs in background."}

@router.post("/sync/din/all")
async def sync_all_dins(background_tasks: BackgroundTasks):
    """Sync all directors in the master table."""
    background_tasks.add_task(run_script, SYNC_DIN_SCRIPT, ["--all"])
    return {"message": "Started full DIN sync for all directors in background."}

@router.post("/sync/cin/all")
async def sync_all_cins(background_tasks: BackgroundTasks):
    """Sync all companies in the master table."""
    background_tasks.add_task(run_script, SYNC_CIN_SCRIPT, ["--all"])
    return {"message": "Started full CIN sync for all companies in background."}

@router.post("/generate/mbp1")
async def generate_mbp1(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate MBP-1 forms."""
    if request.all_directors:
        background_tasks.add_task(run_script, MBP1_SCRIPT, ["--all", "--year", request.year])
    elif request.din:
        # Support both single 'cin' and multiple 'cins'
        target_cins = request.cins or ([request.cin] if request.cin else [])
        if not target_cins:
            raise HTTPException(status_code=400, detail="Provide either --all or specific din/cin(s)")
            
        # Pass all CINs as a single comma-separated string to generate ONE combined document
        cins_str = ",".join(target_cins)
        background_tasks.add_task(run_script, MBP1_SCRIPT, ["--din", request.din, "--cin", cins_str, "--year", request.year])
    else:
        raise HTTPException(status_code=400, detail="Provide either --all or specific din/cin(s)")
    
    return {"message": "Started MBP-1 generation in background."}

@router.post("/generate/dir8")
async def generate_dir8(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate DIR-8 forms."""
    if request.all_directors:
        background_tasks.add_task(run_script, DIR8_SCRIPT, ["--all", "--year", request.year])
    elif request.din:
        # Support both single 'cin' and multiple 'cins'
        target_cins = request.cins or ([request.cin] if request.cin else [])
        if not target_cins:
            raise HTTPException(status_code=400, detail="Provide either --all or specific din/cin(s)")
            
        # Pass all CINs as a single comma-separated string to generate ONE combined document
        cins_str = ",".join(target_cins)
        background_tasks.add_task(run_script, DIR8_SCRIPT, ["--din", request.din, "--cin", cins_str, "--year", request.year])
    else:
        raise HTTPException(status_code=400, detail="Provide either --all or specific din/cin(s)")
    
    return {"message": "Started DIR-8 generation in background."}

@router.get("/directors")
async def get_directors_list():
    """Get list of directors with DIN and Name."""
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT din, name FROM directors_master.directors ORDER BY name ASC")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

@router.get("/companies")
async def get_companies_list():
    """Get list of group companies with CIN and Name."""
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT cin, name FROM directors_data.companies ORDER BY name ASC")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()
@router.get("/companies-by-director/{din}")
async def get_companies_by_director(din: str):
    """Get list of active companies associated with a specific director."""
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Fetch only 'Active' associations from the master registry
        cur.execute("""
            SELECT DISTINCT cin, company_name as name 
            FROM directors_master.external_board_members 
            WHERE din = %s 
              AND (status IS NULL OR (UPPER(status) != 'AMALGAMATED' AND UPPER(status) NOT LIKE 'RESIGNED%' AND UPPER(status) NOT LIKE 'INACTIVE%'))
            ORDER BY company_name ASC
        """, (din,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

@router.get("/sync/progress")
async def get_sync_progress(type: str = "din"):
    """Fetch the latest progress from the sync JSON files."""
    if type == "din":
        filename = "sync_progress_din.json"
        script_dir = SYNC_DIN_SCRIPT.parent
    elif type == "cin":
        filename = "sync_progress_cin.json"
        script_dir = SYNC_CIN_SCRIPT.parent
    elif type == "mbp1":
        filename = "sync_progress_mbp1.json"
        script_dir = MBP1_SCRIPT.parent
    elif type == "dir8":
        filename = "sync_progress_dir8.json"
        script_dir = DIR8_SCRIPT.parent
    else:
        return {"current": 0, "total": 0, "status": "Invalid type", "active": False}
        
    file_path = script_dir / filename
    
    if not file_path.exists():
        return {"current": 0, "total": 0, "status": "No active task", "active": False}
        
    try:
        # Check file age (if older than 5 minutes, consider it stale/inactive)
        if time.time() - os.path.getmtime(file_path) > 300:
            return {"current": 0, "total": 0, "status": "Task timed out or inactive", "active": False}
            
        with open(file_path, "r") as f:
            data = json.load(f)
            data["active"] = data.get("current", 0) < data.get("total", 0)
            return data
    except Exception:
        return {"current": 0, "total": 0, "status": "Error reading progress", "active": False}
