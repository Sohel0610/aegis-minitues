import os
import zipfile
import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/disclosures", tags=["Disclosures"])

# Base path for generated documents
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "Director_Disclosure" / "Output_Disclosures"

def _sanitize_folder_name(name: str) -> str:
    """Matches the _sanitize_path logic in the generator scripts."""
    import re
    if not name: return "UNKNOWN"
    return re.sub(r'[^a-zA-Z0-9]', '_', name).upper()

class DisclosureFile(BaseModel):
    year: str
    company_name: str
    form_type: str
    file_name: str
    file_path: str
    din: str

@router.get("/{din}", response_model=List[DisclosureFile])
async def list_director_disclosures(din: str):
    """
    Scans the Output_Disclosures directory for files matching the given DIN.
    Structure: Output_Disclosures/{Year}/{CompanyName}/{FormType}/{FileName}_{DIN}.docx
    """
    if not BASE_DIR.exists():
        return []

    disclosures = []
    
    # Iterate through years
    for year_dir in BASE_DIR.iterdir():
        if not year_dir.is_dir(): continue
        
        # Iterate through companies
        for company_dir in year_dir.iterdir():
            if not company_dir.is_dir(): continue
            
            # Iterate through form types (DIR-8, MBP-1)
            for form_dir in company_dir.iterdir():
                if not form_dir.is_dir(): continue
                
                # Look for files matching the DIN
                for file in form_dir.glob(f"*_{din}.docx"):
                    disclosures.append(DisclosureFile(
                        year=year_dir.name,
                        company_name=company_dir.name.replace("_", " "),
                        form_type=form_dir.name,
                        file_name=file.name,
                        file_path=str(file.relative_to(BASE_DIR)),
                        din=din
                    ))
                    
    return disclosures

@router.get("/download/file")
async def download_file(path: str):
    """Download a specific file by its relative path or filename."""
    # 1. Try Direct Path
    file_path = BASE_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    # 2. Fallback: Recursive search by filename if path is just a name
    fname = os.path.basename(path)
    if os.path.exists(BASE_DIR):
        for root, dirs, files in os.walk(BASE_DIR):
            if fname in files:
                target_path = Path(root) / fname
                return FileResponse(
                    path=target_path,
                    filename=fname,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    
    raise HTTPException(status_code=404, detail=f"File {fname} not found in repository")

@router.get("/company/{cin}/status")
async def get_company_compliance_status(cin: str, year: str = "2024-25"):
    """
    Returns the status of DIR-8 and MBP-1 for all directors of a specific company.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Use environment variables from .env
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
        sslmode='require'
    )
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Get Company Name (Try master list first, then external registry)
        cur.execute("SELECT name FROM directors_data.companies WHERE cin = %s", (cin,))
        c_row = cur.fetchone()
        
        if c_row:
            company_name = c_row['name']
        else:
            # Fallback to external registry
            cur.execute("SELECT company_name as name FROM directors_master.external_board_members WHERE cin = %s LIMIT 1", (cin,))
            c_row = cur.fetchone()
            if not c_row: raise HTTPException(status_code=404, detail="Company not found in any registry")
            company_name = c_row['name']
            
        folder_name = _sanitize_folder_name(company_name)
        
        # Get ALL Directors for this company from the registry sync
        cur.execute("""
            SELECT 
                ebm.din, 
                ebm.name,
                ebm.designation,
                ebm.appointment_date,
                CASE WHEN d.din IS NOT NULL THEN TRUE ELSE FALSE END as is_adani
            FROM directors_master.external_board_members ebm
            LEFT JOIN directors_master.directors d ON ebm.din = d.din
            WHERE ebm.cin = %s
              AND (ebm.status IS NULL OR ebm.status = '' OR ebm.status = 'None' OR ebm.status ILIKE 'ACTIVE%')
            ORDER BY ebm.name ASC
        """, (cin,))
        directors = cur.fetchall()
        
        # 2. Check Files on Disk
        results = []
        target_dir = BASE_DIR / year / folder_name
        
        for d in directors:
            din = d['din']
            name = d['name']
            designation = d['designation'] or "Director"
            
            # Format appointment date
            appt_date = d['appointment_date']
            appt_date_str = appt_date.strftime("%d/%m/%Y") if hasattr(appt_date, 'strftime') else (str(appt_date) if appt_date else "N/A")
            
            dir8_path = target_dir / "DIR-8"
            mbp1_path = target_dir / "MBP-1"
            
            # Check for files matching *_{din}.docx
            dir8_files = list(dir8_path.glob(f"*_{din}.docx")) if dir8_path.exists() else []
            mbp1_files = list(mbp1_path.glob(f"*_{din}.docx")) if mbp1_path.exists() else []
            
            results.append({
                "din": din,
                "name": name,
                "designation": designation,
                "appointment_date": appt_date_str,
                "dir8_status": "Filed" if dir8_files else "Pending",
                "mbp1_status": "Filed" if mbp1_files else "Pending",
                "dir8_file": str(dir8_files[0].relative_to(BASE_DIR)) if dir8_files else None,
                "mbp1_file": str(mbp1_files[0].relative_to(BASE_DIR)) if mbp1_files else None,
                "last_updated": datetime.fromtimestamp(dir8_files[0].stat().st_mtime).strftime("%d/%m/%Y") if dir8_files else "N/A",
                "is_adani": d['is_adani']
            })
            
        return {
            "company_name": company_name,
            "year": year,
            "directors": results
        }
    finally:
        conn.close()

@router.get("/company/{cin}/bulk-download")
async def bulk_download_company_forms(cin: str, year: str = "2024-25"):
    """
    Creates a ZIP archive of all forms for a company and streams it.
    """
    import psycopg2
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
        sslmode='require'
    )
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM directors_data.companies WHERE cin = %s", (cin,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Company not found")
        company_name = row[0]
        folder_name = _sanitize_folder_name(company_name)
        target_dir = BASE_DIR / year / folder_name
        
        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="No documents generated for this company yet")

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    if file.endswith(".docx"):
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(target_dir)
                        zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        zip_filename = f"{folder_name}_Disclosures_{year}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    finally:
        conn.close()
