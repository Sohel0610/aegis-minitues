"""
Director Data Analysis Module
This module handles parsing of MBP-1 DOCX documents, extracting director information,
normalizing the data, and storing it in a SQLite database.
"""

import os
import sqlite3
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

# Database setup - We use the 'directors_data' schema in Azure PostgreSQL
DB_SCHEMA = "directors_data"

def init_database():
    """Verify the PostgreSQL database schema and tables."""
    pg_conn = get_pg_connection()
    if not pg_conn:
        logger.error("Could not connect to Azure PostgreSQL for initialization")
        return
    
    try:
        cursor = get_pg_cursor(pg_conn)
        
        # Ensure schema exists
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}")
        
        # Create directors table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.directors (
                din TEXT PRIMARY KEY,
                name TEXT,
                source_file TEXT
            )
        """)
        
        # Create companies table
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
        
        # Create document_summaries table
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
        logger.info("PostgreSQL database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing PostgreSQL database: {e}")
    finally:
        pg_conn.close()

def extract_director_info(doc_path: str) -> Dict:
    """
    Extract director information from a DOCX file.
    
    Args:
        doc_path (str): Path to the DOCX file
        
    Returns:
        Dict: Dictionary containing director information
    """
    try:
        doc = Document(doc_path)
        filename = os.path.basename(doc_path)
        
        # Extract director name from filename (before _MBP.docx)
        director_name = filename.replace("_MBP.docx", "").replace("_", " ")
        
        # Extract DIN from document content
        din = None
        companies = []
        
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
            # Try alternative patterns for DIN
            din_match = re.search(r"(\d{8})", full_text_str)
            if din_match:
                din = din_match.group(1)
        
        # Extract companies information from tables and sections
        companies = extract_companies_info(doc, full_text_str)
        
        return {
            "name": director_name,
            "din": din,
            "source_file": filename,
            "companies": companies
        }
    except Exception as e:
        logger.error(f"Error extracting info from {doc_path}: {str(e)}")
        return {
            "name": "Unknown",
            "din": None,
            "source_file": os.path.basename(doc_path),
            "companies": []
        }

def extract_companies_info(doc, full_text_str: str) -> List[Dict]:
    """
    Extract companies information from document tables and sections.
    
    Args:
        doc: Document object
        full_text_str (str): Full text of the document
        
    Returns:
        List[Dict]: List of company dictionaries
    """
    companies = []
    
    # First, try to extract company types from sections
    company_types = extract_company_types_from_sections(full_text_str)
    
    # Extract companies from tables
    table_companies = extract_companies_from_tables(doc)
    
    # Merge company information with types
    for company in table_companies:
        company_name = company.get("name", "")
        if company_name:
            # Look up company type
            company_type = "Unknown"
            for section_type, section_companies in company_types.items():
                # Check if this company is in any of the sections
                for section_company in section_companies:
                    # Compare company names after cleaning
                    clean_company_name = re.sub(r'\s+', ' ', company_name.strip()).upper()
                    clean_section_company = re.sub(r'\s+', ' ', section_company.strip()).upper()
                    if clean_company_name == clean_section_company:
                        company_type = section_type
                        break
                if company_type != "Unknown":
                    break
            
            company["type"] = company_type
            companies.append(company)
    
    return companies

def extract_company_types_from_sections(full_text_str: str) -> Dict[str, List[str]]:
    """
    Extract company types from the section headers in the document.
    
    Args:
        full_text_str (str): Full text of the document
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping company types to company names
    """
    company_types = {
        "Public": [],
        "Private - Subsidiary of Public": [],
        "Private - Not Subsidiary of Public": []
    }
    
    # Normalize whitespace in the text
    full_text_str = re.sub(r'\r\n', '\n', full_text_str)
    full_text_str = re.sub(r'\r', '\n', full_text_str)
    
    # Look for section patterns with more robust regex
    # Pattern for Public Limited Companies section
    public_pattern = r"\(A\)\s*Public Limited Companies:\s*(.*?)(?=\n\([B-Z]\)|$)"
    public_match = re.search(public_pattern, full_text_str, re.DOTALL | re.IGNORECASE)
    if public_match:
        public_section = public_match.group(1).strip()
        # Extract company names - now extract all companies with comprehensive patterns
        # Look for lines that contain company names but not "NIL"
        public_companies = re.findall(r'^.*?LIMITED.*?$', public_section, re.MULTILINE | re.IGNORECASE)
        # Also look for other company names that don't contain "LIMITED" but are likely company names
        # Updated pattern based on Excel analysis: include FOUNDATION, LTD, and other company indicators
        other_companies = re.findall(r'^[A-Z][A-Z\s\(\)&\-\.]*?(?:FOUNDATION|LTD|PRIVATE|PUBLIC|COMPANY|CORPORATION|INC|LLC|LLP)[A-Z\s\(\)&\-\.]*?$', public_section, re.MULTILINE)
        all_companies = public_companies + other_companies
        for company in all_companies:
            company = company.strip()
            # Skip NIL entries and empty lines
            if company and not re.search(r'\bNIL\b', company, re.IGNORECASE) and company.upper() not in ["LIMITED", "LTD"]:
                # Clean up company name
                company = re.sub(r'\s+', ' ', company).strip()
                if company:
                    company_types["Public"].append(company)
    
    # Pattern for Private Limited Companies which are subsidiary(ies) of Public Companies
    private_subsidiary_pattern = r"\(B\)\s*Private Limited Companies which are subsidiary\(ies\) of Public Companies:\s*(.*?)(?=\n\([C-Z]\)|$)"
    private_subsidiary_match = re.search(private_subsidiary_pattern, full_text_str, re.DOTALL | re.IGNORECASE)
    if private_subsidiary_match:
        private_subsidiary_section = private_subsidiary_match.group(1).strip()
        # Check if it's not NIL (more robust check)
        if not re.search(r'\bNIL\b', private_subsidiary_section, re.IGNORECASE):
            # Extract company names - now extract all companies with comprehensive patterns
            private_subsidiary_companies = re.findall(r'^.*?LIMITED.*?$', private_subsidiary_section, re.MULTILINE | re.IGNORECASE)
            # Also look for other company names that don't contain "LIMITED" but are likely company names
            # Updated pattern based on Excel analysis: include FOUNDATION, LTD, and other company indicators
            other_companies = re.findall(r'^[A-Z][A-Z\s\(\)&\-\.]*?(?:FOUNDATION|LTD|PRIVATE|PUBLIC|COMPANY|CORPORATION|INC|LLC|LLP)[A-Z\s\(\)&\-\.]*?$', private_subsidiary_section, re.MULTILINE)
            all_companies = private_subsidiary_companies + other_companies
            for company in all_companies:
                company = company.strip()
                # Skip NIL entries and empty lines
                if company and not re.search(r'\bNIL\b', company, re.IGNORECASE) and company.upper() not in ["LIMITED", "LTD"]:
                    # Clean up company name
                    company = re.sub(r'\s+', ' ', company).strip()
                    if company:
                        company_types["Private - Subsidiary of Public"].append(company)
    
    # Pattern for Private Limited Companies which are not subsidiary(ies) of Public Companies
    private_non_subsidiary_pattern = r"\(C\)\s*Private Limited Companies which are not subsidiary\(ies\) of Public Companies:\s*(.*?)(?=\n\([D-Z]\)|$)"
    private_non_subsidiary_match = re.search(private_non_subsidiary_pattern, full_text_str, re.DOTALL | re.IGNORECASE)
    if private_non_subsidiary_match:
        private_non_subsidiary_section = private_non_subsidiary_match.group(1).strip()
        # Check if it's not NIL (more robust check)
        if not re.search(r'\bNIL\b', private_non_subsidiary_section, re.IGNORECASE):
            # Extract company names - now extract all companies with comprehensive patterns
            private_non_subsidiary_companies = re.findall(r'^.*?LIMITED.*?$', private_non_subsidiary_section, re.MULTILINE | re.IGNORECASE)
            # Also look for other company names that don't contain "LIMITED" but are likely company names
            other_companies = re.findall(r'^[A-Z][A-Z\s\(\)&\-\.]*?(?:FOUNDATION|LTD|PRIVATE|PUBLIC|COMPANY|CORPORATION|INC|LLC|LLP)[A-Z\s\(\)&\-\.]*?$', private_non_subsidiary_section, re.MULTILINE)
            all_companies = private_non_subsidiary_companies + other_companies
            for company in all_companies:
                company = company.strip()
                # Skip NIL entries and empty lines
                if company and not re.search(r'\bNIL\b', company, re.IGNORECASE) and company.upper() not in ["LIMITED", "LTD"]:
                    # Clean up company name
                    company = re.sub(r'\s+', ' ', company).strip()
                    if company:
                        company_types["Private - Not Subsidiary of Public"].append(company)
    
    return company_types

def extract_companies_from_tables(doc) -> List[Dict]:
    """
    Extract companies information from document tables.
    
    Args:
        doc: Document object
        
    Returns:
        List[Dict]: List of company dictionaries
    """
    companies = []
    
    # Process tables in the document
    for table in doc.tables:
        # Check if this is a company table (look for specific headers)
        if len(table.rows) < 2:
            continue
            
        # Get header row
        header_row = table.rows[0]
        headers = [cell.text.strip() for cell in header_row.cells]
        
        # Check if this looks like a company table
        if any("company" in header.lower() or "name" in header.lower() for header in headers):
            # Process data rows
            for i in range(1, len(table.rows)):
                row = table.rows[i]
                cells = [cell.text.strip() for cell in row.cells]
                
                # Skip empty rows
                if not any(cells):
                    continue
                    
                # Extract company information based on column positions
                company_info = extract_company_info_from_row(cells, headers)
                if company_info and company_info.get("name"):
                    companies.append(company_info)
    
    return companies

def extract_company_info_from_row(cells: List[str], headers: List[str]) -> Dict:
    """
    Extract company information from a table row.
    
    Args:
        cells (List[str]): Cell values in the row
        headers (List[str]): Header values for the table
        
    Returns:
        Dict: Company information dictionary
    """
    company_info = {}
    
    # Map headers to cell values
    header_to_value = {}
    for i, header in enumerate(headers):
        if i < len(cells):
            header_to_value[header.lower()] = cells[i]
    
    # Extract company name
    # Look for company name in various possible columns
    company_name = None
    for key, value in header_to_value.items():
        if "company" in key or "name" in key:
            if value and (value.strip() and not re.search(r'\bNIL\b', value, re.IGNORECASE)):
                company_name = value
                break
    
    # If not found, try to find any cell that looks like a company name
    if not company_name:
        for value in cells:
            # Check if the cell contains a company-like name with comprehensive patterns
            # Updated pattern based on Excel analysis: include FOUNDATION, LTD, and other company indicators
            if value and re.match(r'^[A-Z][A-Z\s\(\)&\-\.]*?(?:LIMITED|FOUNDATION|LTD|PRIVATE|PUBLIC|COMPANY|CORPORATION|INC|LLC|LLP)', value, re.IGNORECASE):
                company_name = value
                break
    
    if not company_name:
        return {}
    
    company_info["name"] = company_name
    
    # Extract position/type
    # Look for position information
    position = "Director"  # Default
    for key, value in header_to_value.items():
        if "position" in key or "nature" in key or "type" in key:
            if value:
                if "whole-time" in value.lower() or "whole time" in value.lower():
                    position = "Whole-time Director"
                elif "additional" in value.lower():
                    position = "Additional Director"
                elif "director" in value.lower():
                    position = "Director"
                else:
                    position = value
                break
    
    company_info["position"] = position
    
    # Extract company type (will be filled later)
    company_info["type"] = "Unknown"
    
    # Extract appointment date
    appointment_date = ""
    for key, value in header_to_value.items():
        if "date" in key:
            # Look for date pattern (dd/mm/yyyy)
            date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", value)
            if date_match:
                appointment_date = date_match.group(1)
                break
    
    company_info["appointment_date"] = appointment_date
    
    return company_info

def normalize_company_name(name: str) -> str:
    """
    Normalize company name by removing extra spaces and standardizing format.
    
    Args:
        name (str): Original company name
        
    Returns:
        str: Normalized company name
    """
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Remove special characters at the beginning or end
    name = re.sub(r'^[^\w]+|[^\w]+$', '', name)
    
    # Remove newlines and extra spaces
    name = re.sub(r'\n+', ' ', name)
    
    return name

def normalize_position(position: str) -> str:
    """
    Normalize position values to standard formats.
    
    Args:
        position (str): Original position text
        
    Returns:
        str: Normalized position
    """
    if not position:
        return "Director"
        
    position = position.lower().strip()
    
    if "whole-time" in position or "whole time" in position:
        return "Whole-time Director"
    elif "additional" in position:
        return "Additional Director"
    elif "director" in position:
        return "Director"
    else:
        # If it's a specific position, keep it but title case it
        return position.title()

def store_director_data(director_info: Dict):
    """
    Store director data in the PostgreSQL database.
    
    Args:
        director_info (Dict): Director information dictionary
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        logger.error(f"Could not connect to Azure PostgreSQL to store data for {director_info['name']}")
        return
    
    try:
        cursor = get_pg_cursor(pg_conn)
        
        # Insert or update director information
        if director_info["din"]:
            cursor.execute(f"""
                INSERT INTO {DB_SCHEMA}.directors (din, name, source_file)
                VALUES (%s, %s, %s)
                ON CONFLICT (din) DO UPDATE SET
                    name = EXCLUDED.name,
                    source_file = EXCLUDED.source_file
            """, (director_info["din"], director_info["name"], director_info["source_file"]))
        
        # Insert companies and directorships
        for company in director_info["companies"]:
            if "name" not in company:
                continue
                
            # Normalize company name
            company_name = normalize_company_name(company.get("name", ""))
            if not company_name:
                continue
                
            company_type = company.get("type", "Unknown")
            position = normalize_position(company.get("position", "Director"))
            appointment_date = company.get("appointment_date", "")
            
            # Check if company already exists
            cursor.execute(f"SELECT id, type FROM {DB_SCHEMA}.companies WHERE name = %s", (company_name,))
            existing_company = cursor.fetchone()
            
            if existing_company:
                # If company exists, update the type if it's more specific than "Unknown"
                company_id = existing_company['id']
                existing_type = existing_company['type']
                if existing_type == "Unknown" and company_type != "Unknown":
                    cursor.execute(f"""
                        UPDATE {DB_SCHEMA}.companies SET type = %s WHERE id = %s
                    """, (company_type, company_id))
            else:
                # Insert new company
                cursor.execute(f"""
                    INSERT INTO {DB_SCHEMA}.companies (name, type)
                    VALUES (%s, %s)
                    RETURNING id
                """, (company_name, company_type))
                company_id = cursor.fetchone()['id']
            
            # Insert directorship if DIN is available
            if director_info["din"]:
                # Check for existing directorship to avoid duplicates if necessary, or just insert
                # For simplicity, we can use a check or just assume it's a new entry
                cursor.execute(f"""
                    SELECT 1 FROM {DB_SCHEMA}.directorships 
                    WHERE din = %s AND company_id = %s AND position = %s
                """, (director_info["din"], company_id, position))
                
                if not cursor.fetchone():
                    cursor.execute(f"""
                        INSERT INTO {DB_SCHEMA}.directorships (din, company_id, position, appointment_date)
                        VALUES (%s, %s, %s, %s)
                    """, (director_info["din"], company_id, position, appointment_date))
        
        pg_conn.commit()
        logger.info(f"Stored data for director: {director_info['name']}")
        
    except Exception as e:
        logger.error(f"Error storing data for {director_info['name']}: {str(e)}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()

def process_all_director_files(directory_path: str):
    """
    Process all director DOCX files in the given directory.
    
    Args:
        directory_path (str): Path to the directory containing DOCX files
    """
    # Initialize database
    init_database()
    
    # Get all DOCX files
    docx_files = [f for f in os.listdir(directory_path) if f.endswith('.docx')]
    
    logger.info(f"Processing {len(docx_files)} director files...")
    
    processed_count = 0
    for filename in docx_files:
        file_path = os.path.join(directory_path, filename)
        logger.info(f"Processing {filename}...")
        
        # Extract director information
        director_info = extract_director_info(file_path)
        
        # Store in database
        store_director_data(director_info)
        processed_count += 1
    
    logger.info(f"Successfully processed {processed_count} files")

# API Functions
def get_all_directors():
    """
    Get all directors from the database.
    
    Returns:
        List[Dict]: List of director dictionaries
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        return []
        
    try:
        cursor = get_pg_cursor(pg_conn)
        cursor.execute(f"SELECT din, name, source_file FROM {DB_SCHEMA}.directors")
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                "din": row['din'],
                "name": row['name'],
                "source_file": row['source_file']
            })
        return result
    finally:
        pg_conn.close()

def get_company_count():
    """
    Get company count statistics.
    
    Returns:
        Dict: Company count statistics
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        return {"total": 0, "public": 0, "private": 0}
        
    try:
        cursor = get_pg_cursor(pg_conn)
        
        # Total companies
        cursor.execute(f"SELECT COUNT(*) FROM {DB_SCHEMA}.companies")
        total_companies = cursor.fetchone()['count']
        
        # Public companies
        cursor.execute(f"SELECT COUNT(*) FROM {DB_SCHEMA}.companies WHERE type = 'Public'")
        public_companies = cursor.fetchone()['count']
        
        # Private companies (both types)
        cursor.execute(f"SELECT COUNT(*) FROM {DB_SCHEMA}.companies WHERE type LIKE 'Private%%'")
        private_companies = cursor.fetchone()['count']
        
        return {
            "total": total_companies,
            "public": public_companies,
            "private": private_companies
        }
    finally:
        pg_conn.close()

def get_cross_directorship():
    """
    Get cross-directorship information.
    
    Returns:
        List[Dict]: List of directors with their company counts
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        return []
        
    try:
        cursor = get_pg_cursor(pg_conn)
        cursor.execute(f"""
            SELECT d.name, COUNT(DISTINCT ds.company_id) as company_count
            FROM {DB_SCHEMA}.directors d
            JOIN {DB_SCHEMA}.directorships ds ON d.din = ds.din
            GROUP BY d.din, d.name
            ORDER BY company_count DESC
        """)
        
        rows = cursor.fetchall()
        return [{"name": row['name'], "companies": row['company_count']} for row in rows]
    finally:
        pg_conn.close()

def get_clustering():
    """
    Get director clustering information (shared companies).
    
    Returns:
        List[Dict]: List of director pairs with shared company counts
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        return []
        
    try:
        cursor = get_pg_cursor(pg_conn)
        cursor.execute(f"""
            SELECT 
                d1.name as director1,
                d2.name as director2,
                COUNT(DISTINCT ds1.company_id) as shared_companies
            FROM {DB_SCHEMA}.directorships ds1
            JOIN {DB_SCHEMA}.directorships ds2 ON ds1.company_id = ds2.company_id AND ds1.din < ds2.din
            JOIN {DB_SCHEMA}.directors d1 ON ds1.din = d1.din
            JOIN {DB_SCHEMA}.directors d2 ON ds2.din = d2.din
            GROUP BY d1.din, d2.din, d1.name, d2.name
            HAVING COUNT(DISTINCT ds1.company_id) > 0
            ORDER BY shared_companies DESC
            LIMIT 50
        """)
        
        rows = cursor.fetchall()
        return [
            {
                "director1": row['director1'],
                "director2": row['director2'],
                "sharedCompanies": row['shared_companies']
            }
            for row in rows
        ]
    finally:
        pg_conn.close()

def get_network():
    """
    Get network data for visualization.
    
    Returns:
        Dict: Network nodes and links
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        return {"nodes": [], "links": []}
        
    try:
        cursor = get_pg_cursor(pg_conn)
        
        # Get directors
        cursor.execute(f"SELECT din, name FROM {DB_SCHEMA}.directors")
        directors = cursor.fetchall()
        
        # Get companies
        cursor.execute(f"SELECT id, name FROM {DB_SCHEMA}.companies")
        companies = cursor.fetchall()
        
        # Get directorships (links)
        cursor.execute(f"""
            SELECT d.name as director_name, c.name as company_name
            FROM {DB_SCHEMA}.directorships ds
            JOIN {DB_SCHEMA}.directors d ON ds.din = d.din
            JOIN {DB_SCHEMA}.companies c ON ds.company_id = c.id
        """)
        directorships = cursor.fetchall()
        
        # Format for network visualization
        nodes = []
        links = []
        
        # Add directors as nodes
        director_names = set()
        for row in directors:
            name = row['name']
            if name not in director_names:
                nodes.append({"id": name, "type": "director"})
                director_names.add(name)
        
        # Add companies as nodes
        company_names = set()
        for row in companies:
            name = row['name']
            if name not in company_names:
                nodes.append({"id": name, "type": "company"})
                company_names.add(name)
        
        # Add links
        link_set = set()
        for row in directorships:
            d_name = row['director_name']
            c_name = row['company_name']
            link_key = (d_name, c_name)
            if link_key not in link_set:
                links.append({"source": d_name, "target": c_name})
                link_set.add(link_key)
        
        return {"nodes": nodes, "links": links}
    finally:
        pg_conn.close()

def get_wtd_count():
    """
    Get whole-time director count.
    
    Returns:
        List[Dict]: List of directors with whole-time director positions
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        return []
        
    try:
        cursor = get_pg_cursor(pg_conn)
        cursor.execute(f"""
            SELECT d.name, COUNT(*) as wtd_positions
            FROM {DB_SCHEMA}.directors d
            JOIN {DB_SCHEMA}.directorships ds ON d.din = ds.din
            WHERE ds.position = 'Whole-time Director'
            GROUP BY d.din, d.name
            ORDER BY wtd_positions DESC
        """)
        
        rows = cursor.fetchall()
        return [{"name": row['name'], "positions": row['wtd_positions']} for row in rows]
    finally:
        pg_conn.close()

def get_all_companies_with_director_count():
    """
    Get all companies with their director counts and types.
    
    Returns:
        List[Dict]: List of companies with their director counts and types
    """
    pg_conn = get_pg_connection()
    if not pg_conn:
        return []
        
    try:
        cursor = get_pg_cursor(pg_conn)
        cursor.execute(f"""
            SELECT c.name, c.type, COUNT(ds.id) as director_count
            FROM {DB_SCHEMA}.companies c
            LEFT JOIN {DB_SCHEMA}.directorships ds ON c.id = ds.company_id
            GROUP BY c.id, c.name, c.type
            ORDER BY c.name
        """)
        
        rows = cursor.fetchall()
        return [{"name": row['name'], "type": row['type'], "director_count": row['director_count']} for row in rows]
    finally:
        pg_conn.close()

# Test function
def test_extraction():
    """Test the extraction functionality with one file."""
    file_path = "public/Directors Discloser Output/Abdul Ishad Khan_MBP.docx"
    if os.path.exists(file_path):
        director_info = extract_director_info(file_path)
        print("Extracted Director Info:")
        print(f"Name: {director_info['name']}")
        print(f"DIN: {director_info['din']}")
        print(f"Source File: {director_info['source_file']}")
        print("Companies:")
        for company in director_info['companies']:
            print(f"  - {company}")
    else:
        print(f"File not found: {file_path}")

if __name__ == "__main__":
    # Process all director files when run directly
    directory_path = "public/Directors Discloser Output"
    if os.path.exists(directory_path):
        process_all_director_files(directory_path)
    else:
        logger.error(f"Directory not found: {directory_path}")
