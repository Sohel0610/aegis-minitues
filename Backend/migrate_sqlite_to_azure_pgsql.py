import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Explicitly load .env from the aegis_backend directory
env_path = os.path.join(os.path.dirname(__file__), "aegis_backend", ".env")
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure PostgreSQL credentials from environment variables
AZURE_PG_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system')
}

def connect_to_azure_pgsql():
    """Establish connection to Azure PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=AZURE_PG_CONFIG['host'],
            user=AZURE_PG_CONFIG['user'],
            password=AZURE_PG_CONFIG['password'],
            port=AZURE_PG_CONFIG['port'],
            database=AZURE_PG_CONFIG['database']
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Azure PostgreSQL: {e}")
        raise

def parse_date(date_str):
    """Handles multiple date formats and returns YYYY-MM-DD for PostgreSQL."""
    if not date_str or str(date_str).lower() in ['none', 'null', '']: 
        return None
        
    try:
        clean_str = str(date_str).strip().split(' ')[0]
        
        # Match DD-MM-YYYY or DD/MM/YYYY
        m = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', clean_str)
        if m:
            d, m_part, y = m.groups()
            return f"{y}-{m_part.zfill(2)}-{d.zfill(2)}"
            
        # Match YYYY-MM-DD or YYYY/MM/DD
        m = re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$', clean_str)
        if m:
            y, m_part, d = m.groups()
            return f"{y}-{m_part.zfill(2)}-{d.zfill(2)}"
            
        return None
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None

def create_schemas_and_tables():
    """Create essential schemas and tables to match Backend logic."""
    conn = connect_to_azure_pgsql()
    cursor = conn.cursor()
    try:
        schemas = ["directors_master", "directors_data", "directors_profile", "family_information"]
        for schema in schemas:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS directors_master.directors (id SERIAL PRIMARY KEY, name TEXT NOT NULL, din TEXT UNIQUE, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());")
        cursor.execute("CREATE TABLE IF NOT EXISTS directors_master.director_changes (id SERIAL PRIMARY KEY, director_id INTEGER, director_name TEXT, change_type TEXT, description TEXT, changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute("CREATE TABLE IF NOT EXISTS directors_data.directors (din TEXT PRIMARY KEY, name TEXT, source_file TEXT);")
        cursor.execute("CREATE TABLE IF NOT EXISTS directors_data.companies (id SERIAL PRIMARY KEY, name TEXT UNIQUE, type TEXT);")
        cursor.execute("CREATE TABLE IF NOT EXISTS directors_data.directorships (id SERIAL PRIMARY KEY, din TEXT REFERENCES directors_data.directors(din) ON DELETE CASCADE, company_id INTEGER REFERENCES directors_data.companies(id) ON DELETE CASCADE, position TEXT, appointment_date DATE);")
        cursor.execute("CREATE TABLE IF NOT EXISTS directors_data.document_summaries (id SERIAL PRIMARY KEY, director_name TEXT NOT NULL, din TEXT, file_path TEXT NOT NULL UNIQUE, full_text TEXT, summary TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());")
        cursor.execute("CREATE TABLE IF NOT EXISTS directors_profile.directors_profile (id SERIAL PRIMARY KEY, din TEXT UNIQUE, pan TEXT, name_of_director TEXT, address TEXT, date_of_birth DATE, qualification TEXT, experience TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());")
        cursor.execute("""CREATE TABLE IF NOT EXISTS family_information.director_family (
                id SERIAL PRIMARY KEY, director_name TEXT NOT NULL, section_2_77_i TEXT, section_2_77_ii TEXT, section_2_77_iii TEXT,
                father TEXT, mother TEXT, son TEXT, sons_wife TEXT, daughter TEXT, daughters_husband TEXT,
                brother TEXT, sister TEXT, father_pan TEXT, mother_pan TEXT, father_pan_file TEXT, mother_pan_file TEXT,
                is_submitted INTEGER DEFAULT 0, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );""")
        conn.commit()
    finally:
        cursor.close(); conn.close()

def get_sqlite_connection(db_path: str):
    if not os.path.exists(db_path): raise FileNotFoundError(f"SQLite DB missing: {db_path}")
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    return conn

def migrate_analytics_data():
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "directors_data.db")
    if not os.path.exists(sqlite_path): return
    sconn = get_sqlite_connection(sqlite_path); pconn = connect_to_azure_pgsql()
    try:
        scursor = sconn.cursor(); pcursor = pconn.cursor()
        scursor.execute("SELECT din, name, source_file FROM directors")
        for r in scursor.fetchall():
            pcursor.execute("INSERT INTO directors_data.directors (din, name, source_file) VALUES (%s, %s, %s) ON CONFLICT (din) DO NOTHING", (r['din'], r['name'], r['source_file']))
        scursor.execute("SELECT id, name, type FROM companies")
        for r in scursor.fetchall():
            pcursor.execute("INSERT INTO directors_data.companies (id, name, type) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING", (r['id'], r['name'], r['type']))
        scursor.execute("SELECT din, company_id, position, appointment_date FROM directorships")
        for r in scursor.fetchall():
            pcursor.execute("INSERT INTO directors_data.directorships (din, company_id, position, appointment_date) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (r['din'], r['company_id'], r['position'], parse_date(r['appointment_date'])))
        scursor.execute("SELECT director_name, din, file_path, full_text, summary FROM document_summaries")
        for r in scursor.fetchall():
            pcursor.execute("INSERT INTO directors_data.document_summaries (director_name, din, file_path, full_text, summary) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (file_path) DO NOTHING", (r['director_name'], r['din'], r['file_path'], r['full_text'], r['summary']))
        pconn.commit()
    finally:
        sconn.close(); pconn.close()

def migrate_master_and_profiles():
    base = os.path.join(os.path.dirname(__file__), "aegis_backend", "public")
    pconn = connect_to_azure_pgsql(); pcursor = pconn.cursor()
    try:
        m_path = os.path.join(base, "directors.db")
        if os.path.exists(m_path):
            sconn = get_sqlite_connection(m_path); scursor = sconn.cursor()
            scursor.execute("SELECT name, din FROM directors")
            for r in scursor.fetchall():
                pcursor.execute("INSERT INTO directors_master.directors (name, din) VALUES (%s, %s) ON CONFLICT (din) DO NOTHING", (r['name'], r['din']))
            sconn.close()

        prof_path = os.path.join(base, "directors_profile.db")
        if os.path.exists(prof_path):
            sconn = get_sqlite_connection(prof_path); scursor = sconn.cursor()
            scursor.execute("SELECT * FROM directors_profile")
            for r in scursor.fetchall():
                pcursor.execute("""INSERT INTO directors_profile.directors_profile (din, pan, name_of_director, address, date_of_birth, qualification, experience)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (din) DO NOTHING""", 
                    (r['DIN'], r['PAN'], r['Name_of_Director'], r['Address'], parse_date(r['Date_of_Birth']), r['Qualification'], r['Nature_of_Experience_in_specific_Functional_Areas']))
            sconn.close()
        pconn.commit()
    finally:
        pconn.close()

def migrate_family_info():
    f_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "Director_Family_Information.db")
    if not os.path.exists(f_path): return
    sconn = get_sqlite_connection(f_path); pconn = connect_to_azure_pgsql()
    try:
        sc = sconn.cursor(); pc = pconn.cursor()
        tbl = sc.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()[0]
        rows = sc.execute(f"SELECT * FROM {tbl}").fetchall()
        for r in rows:
            pc.execute("""INSERT INTO family_information.director_family (director_name, section_2_77_i, section_2_77_ii, section_2_77_iii, father, mother, son, sons_wife, daughter, daughters_husband, brother, sister, father_pan, mother_pan, is_submitted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                (r['Name'], r['Section_2(77)(i)'], r['Section_2(77)(ii)'], r['Section_2(77)(iii)'], r['Father'], r['Mother'], r['Son'], r["Son's_Wife"], r['Daughter'], r["Daughter's_husband"], r['Brother'], r['Sister'], r['Father_PAN'], r['Mother_PAN'], r['Is_Submitted']))
        pconn.commit()
    finally:
        sconn.close(); pconn.close()

def sync_registry():
    pconn = connect_to_azure_pgsql(); pc = pconn.cursor()
    try:
        pc.execute("INSERT INTO directors_master.directors (name, din) SELECT DISTINCT name, din FROM directors_data.directors WHERE din IS NOT NULL AND din != '' ON CONFLICT (din) DO NOTHING;")
        pconn.commit(); logger.info("Master Registry Final Sync Done.")
    finally:
        pconn.close()

def main():
    logger.info("Starting Corrected Migration...")
    create_schemas_and_tables()
    migrate_analytics_data()
    migrate_master_and_profiles()
    migrate_family_info()
    sync_registry()
    logger.info("Migration Task Finished Successfully!")

if __name__ == "__main__":
    main()
