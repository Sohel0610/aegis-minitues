"""
Director Data Analysis Module
This module handles parsing of MBP-1 DOCX documents, extracting director information,
normalizing the data, and storing it in a PostgreSQL database (now mandatory).
"""

import os
import re
from datetime import datetime
from docx import Document
from typing import List, Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our PostgreSQL service
from utils.pgsql_service import get_pg_connection, get_pg_cursor

# Database schema in PostgreSQL (Unified Master Schema)
DB_SCHEMA = "directors_master"

def init_database():
    """Verify the PostgreSQL database schema and tables (Unified)."""
    # Use dedicated Directors database pointer
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)

            # Ensure schema exists (Central Namespace)
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}")

            # 1. Master Directors Table (Unified with routes.directors_disclosure)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.directors (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    din TEXT UNIQUE,
                    source_file TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Master Companies Table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.companies (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    type TEXT
                )
            """)

            # Create directorships table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.directorships (
                    id SERIAL PRIMARY KEY,
                    din TEXT REFERENCES {DB_SCHEMA}.directors(din),
                    company_id INTEGER REFERENCES {DB_SCHEMA}.companies(id),
                    position TEXT,
                    appointment_date TEXT
                )
            """)

            # Create document_summaries table (file_path must be unique for UPSERT)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.document_summaries (
                    id SERIAL PRIMARY KEY,
                    director_name TEXT NOT NULL,
                    din TEXT,
                    file_path TEXT NOT NULL UNIQUE,
                    full_text TEXT,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for document_summaries
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_doc_summ_file_path ON {DB_SCHEMA}.document_summaries (file_path)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_doc_summ_dir_name ON {DB_SCHEMA}.document_summaries (director_name)")

            pg_conn.commit()
            logger.info("PostgreSQL database schemas for Directors initialized successfully")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")
            try:
                pg_conn.rollback()
            except Exception:
                pass
            raise RuntimeError(f"Database initialization failed: {e}")
        finally:
            pg_conn.close()
    else:
        logger.error("Could not get a database connection for initialization")
        raise RuntimeError("Database connection failed during initialization")

def extract_director_info(doc_path: str) -> Dict:
    """Extract director information from a DOCX file."""
    try:
        doc = Document(doc_path)
        filename = os.path.basename(doc_path)
        
        # Extract director name from filename (before _MBP.docx)
        director_name = filename.replace("_MBP.docx", "").replace("_", " ")
        
        # Extract DIN from document content
        din = None
        
        # Convert document to text
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        
        full_text_str = "\n".join(full_text)
        
        # Look for DIN pattern (typically a number)
        din_match = re.search(r"DIN\s*:\s*(\d+)", full_text_str, re.IGNORECASE)
        if din_match:
            din = din_match.group(1)
        else:
            din_match = re.search(r"(\d{8})", full_text_str)
            if din_match:
                din = din_match.group(1)
        
        # Extract companies information
        companies = extract_companies_info(doc, full_text_str)
        
        return {
            "name": director_name,
            "din": din,
            "source_file": filename,
            "companies": companies
        }
    except Exception as e:
        logger.error(f"Error extracting info from {doc_path}: {str(e)}")
        return {"name": "Unknown", "din": None, "source_file": os.path.basename(doc_path), "companies": []}

def extract_companies_info(doc, full_text_str: str) -> List[Dict]:
    """Extract companies information from document tables and sections."""
    companies = []
    company_types = extract_company_types_from_sections(full_text_str)
    table_companies = extract_companies_from_tables(doc)
    
    for company in table_companies:
        company_name = company.get("name", "")
        if company_name:
            company_type = "Unknown"
            for section_type, section_companies in company_types.items():
                for section_company in section_companies:
                    if re.sub(r'\s+', ' ', company_name.strip()).upper() == re.sub(r'\s+', ' ', section_company.strip()).upper():
                        company_type = section_type
                        break
                if company_type != "Unknown":
                    break
            company["type"] = company_type
            companies.append(company)
    
    return companies

def extract_company_types_from_sections(full_text_str: str) -> Dict[str, List[str]]:
    """Extract company types from the section headers in the document."""
    company_types = {
        "Public": [],
        "Private - Subsidiary of Public": [],
        "Private - Not Subsidiary of Public": []
    }
    full_text_str = full_text_str.replace('\r\n', '\n').replace('\r', '\n')
    
    sections = {
        "Public": r"\(A\)\s*Public Limited Companies:\s*(.*?)(?=\n\([B-Z]\)|$)",
        "Private - Subsidiary of Public": r"\(B\)\s*Private Limited Companies which are subsidiary\(ies\) of Public Companies:\s*(.*?)(?=\n\([C-Z]\)|$)",
        "Private - Not Subsidiary of Public": r"\(C\)\s*Private Limited Companies which are not subsidiary\(ies\) of Public Companies:\s*(.*?)(?=\n\([D-Z]\)|$)"
    }
    
    for key, pattern in sections.items():
        match = re.search(pattern, full_text_str, re.DOTALL | re.IGNORECASE)
        if match:
            batch = match.group(1).strip()
            if re.search(r'\bNIL\b', batch, re.IGNORECASE):
                continue
            candidates = re.findall(r'^.*?LIMITED.*?$', batch, re.MULTILINE | re.IGNORECASE)
            others = re.findall(r'^[A-Z][A-Z\s\(\)&\-\.]*?(?:FOUNDATION|LTD|PRIVATE|PUBLIC|COMPANY|CORPORATION|INC|LLC|LLP)[A-Z\s\(\)&\-\.]*?$', batch, re.MULTILINE)
            for c in candidates + others:
                c = re.sub(r'\s+', ' ', c).strip()
                if c and not re.search(r'\bNIL\b', c, re.IGNORECASE) and c.upper() not in ["LIMITED", "LTD"]:
                    company_types[key].append(c)
    
    return company_types

def extract_companies_from_tables(doc) -> List[Dict]:
    """Extract companies information from document tables."""
    companies = []
    for table in doc.tables:
        if len(table.rows) < 2:
            continue
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        if any("company" in h.lower() or "name" in h.lower() for h in headers):
            for i in range(1, len(table.rows)):
                cells = [cell.text.strip() for cell in table.rows[i].cells]
                if not any(cells): continue
                cinfo = extract_company_info_from_row(cells, headers)
                if cinfo and cinfo.get("name"):
                    companies.append(cinfo)
    return companies

def extract_company_info_from_row(cells: List[str], headers: List[str]) -> Dict:
    """Extract company information from a table row."""
    header_to_value = {h.lower(): (cells[i] if i < len(cells) else "") for i, h in enumerate(headers)}
    company_name = None
    for k, v in header_to_value.items():
        if ("company" in k or "name" in k) and v and not re.search(r'\bNIL\b', v, re.IGNORECASE):
            company_name = v
            break
    if not company_name:
        for v in cells:
            if v and re.match(r'^[A-Z][A-Z\s\(\)&\-\.]*?(?:LIMITED|FOUNDATION|LTD|PRIVATE|PUBLIC|COMPANY|CORPORATION|INC|LLC|LLP)', v, re.IGNORECASE):
                company_name = v
                break
    if not company_name: return {}
    
    position = "Director"
    for k, v in header_to_value.items():
        if ("position" in k or "nature" in k or "type" in k) and v:
            if "whole-time" in v.lower() or "whole time" in v.lower(): position = "Whole-time Director"
            elif "additional" in v.lower(): position = "Additional Director"
            elif "director" in v.lower(): position = "Director"
            else: position = v
            break
            
    appointment_date = ""
    for k, v in header_to_value.items():
        if "date" in k:
            dm = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", v)
            if dm: appointment_date = dm.group(1); break
            
    return {"name": company_name, "position": position, "type": "Unknown", "appointment_date": appointment_date}

def normalize_company_name(name: str) -> str:
    """Normalize company name."""
    name = re.sub(r'\s+', ' ', name.strip())
    name = re.sub(r'^[^\w]+|[^\w]+$', '', name)
    return name.replace('\n', ' ')

def normalize_position(position: str) -> str:
    """Normalize position values."""
    if not position: return "Director"
    p = position.lower().strip()
    if any(x in p for x in ("whole-time", "whole time")): return "Whole-time Director"
    if "additional" in p: return "Additional Director"
    if "director" in p: return "Director"
    return position.title()

def store_director_data(director_info: Dict):
    """Store director data in PostgreSQL (mandatory)."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            if director_info.get("din"):
                cursor.execute(f"""
                    INSERT INTO {DB_SCHEMA}.directors (din, name, source_file)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (din) DO UPDATE SET
                        name = EXCLUDED.name,
                        source_file = EXCLUDED.source_file
                """, (director_info["din"], director_info.get("name"), director_info.get("source_file")))

            for company in director_info.get("companies", []):
                if "name" not in company: continue
                cname = normalize_company_name(company.get("name", ""))
                if not cname: continue
                ctype = company.get("type", "Unknown")
                pos = normalize_position(company.get("position", "Director"))
                adate = company.get("appointment_date", "")

                cursor.execute(f"SELECT id, type FROM {DB_SCHEMA}.companies WHERE name = %s", (cname,))
                existing = cursor.fetchone()
                if existing:
                    cid = existing["id"]
                    if existing["type"] == "Unknown" and ctype != "Unknown":
                        cursor.execute(f"UPDATE {DB_SCHEMA}.companies SET type = %s WHERE id = %s", (ctype, cid))
                else:
                    cursor.execute(f"INSERT INTO {DB_SCHEMA}.companies (name, type) VALUES (%s, %s) RETURNING id", (cname, ctype))
                    cid = cursor.fetchone()["id"]

                if director_info.get("din"):
                    cursor.execute(f"""
                        SELECT 1 FROM {DB_SCHEMA}.directorships
                        WHERE din = %s AND company_id = %s AND position = %s
                    """, (director_info["din"], cid, pos))
                    if not cursor.fetchone():
                        cursor.execute(f"""
                            INSERT INTO {DB_SCHEMA}.directorships (din, company_id, position, appointment_date)
                            VALUES (%s, %s, %s, %s)
                        """, (director_info["din"], cid, pos, adate))
            pg_conn.commit()
            logger.info(f"Stored data for director (PostgreSQL): {director_info.get('name')}")
        except Exception as e:
            pg_conn.rollback()
            logger.error(f"PostgreSQL store failed for {director_info.get('name')}: {e}")
        finally:
            pg_conn.close()

def process_all_director_files(directory_path: str):
    """Process all director DOCX files in the given directory."""
    init_database()
    docx_files = [f for f in os.listdir(directory_path) if f.endswith('.docx')]
    for filename in docx_files:
        info = extract_director_info(os.path.join(directory_path, filename))
        store_director_data(info)

def get_all_directors():
    """Get all directors from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute(f"SELECT din, name, source_file FROM {DB_SCHEMA}.directors")
            rows = cursor.fetchall()
            return [{"din": r["din"], "name": r["name"], "source_file": r["source_file"]} for r in rows]
        finally:
            pg_conn.close()
    return []

def get_company_count():
    """Get company count statistics from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute(f"SELECT COUNT(*) AS count FROM {DB_SCHEMA}.companies")
            total = cursor.fetchone()["count"] or 0
            cursor.execute(f"SELECT COUNT(*) AS count FROM {DB_SCHEMA}.companies WHERE type = 'Public'")
            public = cursor.fetchone()["count"] or 0
            cursor.execute(f"SELECT COUNT(*) AS count FROM {DB_SCHEMA}.companies WHERE type LIKE 'Private%%'")
            private = cursor.fetchone()["count"] or 0
            return {"total": int(total), "public": int(public), "private": int(private)}
        finally:
            pg_conn.close()
    return {"total": 0, "public": 0, "private": 0}

def get_cross_directorship():
    """Get cross-directorship information from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute(f"""
                SELECT d.name, d.din, COUNT(ds.company_id) AS company_count
                FROM {DB_SCHEMA}.directors d
                JOIN {DB_SCHEMA}.directorships ds ON d.din = ds.din
                GROUP BY d.name, d.din
                HAVING COUNT(ds.company_id) > 1
                ORDER BY company_count DESC
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            pg_conn.close()
    return []

def get_clustering():
    """Get director clustering information (shared companies) from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute(f"""
                SELECT d1.name AS director1, d2.name AS director2, COUNT(ds1.company_id) AS shared_companies
                FROM {DB_SCHEMA}.directorships ds1
                JOIN {DB_SCHEMA}.directorships ds2 ON ds1.company_id = ds2.company_id AND ds1.din < ds2.din
                JOIN {DB_SCHEMA}.directors d1 ON ds1.din = d1.din
                JOIN {DB_SCHEMA}.directors d2 ON ds2.din = d2.din
                GROUP BY d1.name, d2.name
                ORDER BY shared_companies DESC
                LIMIT 50
            """)
            return [{"director1": r["director1"], "director2": r["director2"], "sharedCompanies": r["shared_companies"]} for r in cursor.fetchall()]
        finally:
            pg_conn.close()
    return []

def get_network():
    """Get network data (nodes and links) for visualization from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            # Fetch some directors and their companies to build a sample network
            cursor.execute(f"SELECT din, name FROM {DB_SCHEMA}.directors LIMIT 100")
            directors = cursor.fetchall()
            
            cursor.execute(f"SELECT id, name FROM {DB_SCHEMA}.companies LIMIT 50")
            companies = cursor.fetchall()
            
            cursor.execute(f"SELECT din, company_id FROM {DB_SCHEMA}.directorships LIMIT 300")
            links = cursor.fetchall()
            
            nodes = []
            for d in directors: nodes.append({"id": d["din"], "type": "director", "label": d["name"]})
            for c in companies: nodes.append({"id": str(c["id"]), "type": "company", "label": c["name"]})
            
            link_data = []
            for l in links:
                link_data.append({"source": l["din"], "target": str(l["company_id"])})
                
            return {"nodes": nodes, "links": link_data}
        finally:
            pg_conn.close()
    return {"nodes": [], "links": []}

def get_wtd_count():
    """Get whole-time director count from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute(f"""
                SELECT d.name, COUNT(di.id) AS positions
                FROM {DB_SCHEMA}.directors d
                JOIN {DB_SCHEMA}.directorships di ON d.din = di.din
                WHERE di.position ILIKE '%Whole-time%' OR di.position ILIKE '%WTD%'
                GROUP BY d.name
                ORDER BY positions DESC
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            pg_conn.close()
    return []

def get_all_companies_with_director_count():
    """Get all companies with their director counts and types from PostgreSQL."""
    pg_conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
    if pg_conn:
        try:
            cursor = get_pg_cursor(pg_conn)
            cursor.execute(f"""
                SELECT c.name, c.type, COUNT(di.din) AS director_count
                FROM {DB_SCHEMA}.companies c
                LEFT JOIN {DB_SCHEMA}.directorships di ON c.id = di.company_id
                GROUP BY c.id, c.name, c.type
                ORDER BY director_count DESC, c.name ASC
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            pg_conn.close()
    return []
