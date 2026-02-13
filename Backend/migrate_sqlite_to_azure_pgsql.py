import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Any
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

def connect_to_azure_pgsql(database=None):
    """Establish connection to Azure PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=AZURE_PG_CONFIG['host'],
            user=AZURE_PG_CONFIG['user'],
            password=AZURE_PG_CONFIG['password'],
            port=AZURE_PG_CONFIG['port'],
            database=database or AZURE_PG_CONFIG['database']
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Azure PostgreSQL (DB: {database or AZURE_PG_CONFIG['database']}): {e}")
        raise

def create_director_disclosure_database():
    """Create the director_disclosure_system database"""
    # Connect to default postgres DB to create the new one
    conn = connect_to_azure_pgsql(database='postgres')
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'director_disclosure_system'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE director_disclosure_system")
            logger.info("Created database 'director_disclosure_system'")
        else:
            logger.info("Database 'director_disclosure_system' already exists")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def connect_to_director_disclosure_db():
    return connect_to_azure_pgsql()

def create_schemas_and_tables():
    """Create schemas and tables in Azure PostgreSQL"""
    conn = connect_to_director_disclosure_db()
    cursor = conn.cursor()
    
    try:
        schemas = [
            "CREATE SCHEMA IF NOT EXISTS directors_master;",
            "CREATE SCHEMA IF NOT EXISTS directors_data;",
            "CREATE SCHEMA IF NOT EXISTS directors_profile;",
            "CREATE SCHEMA IF NOT EXISTS family_information;"
        ]
        
        for schema in schemas:
            cursor.execute(schema)
        
        # Table: directors_master.directors (Primary Source)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_master.directors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                din TEXT UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directors_master_din ON directors_master.directors(din);")
        
        # Table: directors_data.directors (Analytics Source)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.directors (
                din TEXT PRIMARY KEY,
                name TEXT,
                source_file TEXT
            );
        """)
        
        # Table: directors_data.companies (Analytics Source)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.companies (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                type TEXT
            );
        """)
                
        # Table: directors_data.directorships (Analytics Source)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.directorships (
                id SERIAL PRIMARY KEY,
                din TEXT REFERENCES directors_data.directors(din) ON DELETE CASCADE,
                company_id INTEGER REFERENCES directors_data.companies(id) ON DELETE CASCADE,
                position TEXT,
                appointment_date DATE
            );
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directorships_din ON directors_data.directorships(din);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directorships_company_id ON directors_data.directorships(company_id);")
        
        # Table: directors_data.document_summaries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.document_summaries (
                id SERIAL PRIMARY KEY,
                director_name TEXT NOT NULL,
                din TEXT,
                file_path TEXT NOT NULL,
                full_text TEXT,
                summary TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_file_path ON directors_data.document_summaries(file_path);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_din ON directors_data.document_summaries(din);")
        
        # Table: directors_profile.directors_profile
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_profile.directors_profile (
                id SERIAL PRIMARY KEY,
                din TEXT UNIQUE REFERENCES directors_master.directors(din) ON DELETE CASCADE,
                pan TEXT,
                name_of_director TEXT,
                address TEXT,
                date_of_birth DATE,
                qualification TEXT,
                experience TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_directors_profile_pan ON directors_profile.directors_profile(pan);")

        # Table: family_information.director_family
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS family_information.director_family (
                id SERIAL PRIMARY KEY,
                director_name TEXT NOT NULL,
                section_2_77_i TEXT,
                section_2_77_ii TEXT,
                section_2_77_iii TEXT,
                father TEXT,
                mother TEXT,
                son TEXT,
                sons_wife TEXT,
                daughter TEXT,
                daughters_husband TEXT,
                brother TEXT,
                sister TEXT,
                father_pan TEXT,
                mother_pan TEXT,
                father_pan_file TEXT,
                mother_pan_file TEXT,
                is_submitted INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Ensure latest columns exist
        columns_to_add = [
            ("father_pan", "TEXT"), ("mother_pan", "TEXT"),
            ("father_pan_file", "TEXT"), ("mother_pan_file", "TEXT"),
            ("is_submitted", "INTEGER DEFAULT 0")
        ]
        
        for col_name, col_type in columns_to_add:
            cursor.execute(f"""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_schema='family_information' 
                                   AND table_name='director_family' 
                                   AND column_name='{col_name}') THEN
                        ALTER TABLE family_information.director_family ADD COLUMN {col_name} {col_type};
                    END IF;
                END $$;
            """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_director_family_name ON family_information.director_family(director_name);")
        
        conn.commit()
        logger.info("Created schemas and tables successfully")
        
    except Exception as e:
        logger.error(f"Error creating schemas and tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def get_sqlite_connection(db_path: str):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def parse_date_value(date_str):
    if not date_str: return None
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ['null', 'none', '']: return None
    
    try:
        # Format: YYYY-MM-DD 00:00:00
        if ' ' in date_str and ':' in date_str:
            date_part = date_str.split(' ')[0]
            if len(date_part) == 10 and date_part.count('-') == 2:
                return date_part
        
        # Format: YYYY-MM-DD
        if '-' in date_str and len(date_str) == 10 and date_str.count('-') == 2:
            if date_str.split('-')[0].isdigit() and len(date_str.split('-')[0]) == 4:
                return date_str
        
        # Parse numbers for various orders
        import re
        nums = re.findall(r'\d+', date_str)
        if len(nums) >= 3:
            # Assume DD MM YYYY or YYYY MM DD
            if len(nums[0]) == 4: # YYYY-MM-DD
                return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
            elif len(nums[2]) == 4: # DD-MM-YYYY
                return f"{nums[2]}-{nums[1].zfill(2)}-{nums[0].zfill(2)}"
        return None
    except Exception: return None

def migrate_directors_data_db():
    """Migrate directors_data.db to Azure PostgreSQL"""
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "directors_data.db")
    if not os.path.exists(sqlite_path):
        logger.warning(f"Skipping directors_data migration: {sqlite_path} not found.")
        return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # 1. Directors
        logger.info("Migrating directors_data.directors...")
        pg_cursor.execute("TRUNCATE TABLE directors_data.directors CASCADE")
        sqlite_cursor.execute("SELECT din, name, source_file FROM directors")
        rows = sqlite_cursor.fetchall()
        for row in rows:
            pg_cursor.execute("INSERT INTO directors_data.directors (din, name, source_file) VALUES (%s, %s, %s) ON CONFLICT (din) DO NOTHING", 
                             (row['din'], row['name'], row['source_file']))
        
        # 2. Companies
        logger.info("Migrating directors_data.companies...")
        pg_cursor.execute("ALTER TABLE directors_data.companies DROP CONSTRAINT IF EXISTS companies_type_check;")
        sqlite_cursor.execute("SELECT id, name, type FROM companies")
        rows = sqlite_cursor.fetchall()
        for row in rows:
            pg_cursor.execute("INSERT INTO directors_data.companies (id, name, type) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING", 
                             (row['id'], row['name'], row['type']))
        
        # 3. Directorships
        logger.info("Migrating directors_data.directorships...")
        sqlite_cursor.execute("SELECT id, din, company_id, position, appointment_date FROM directorships")
        rows = sqlite_cursor.fetchall()
        for row in rows:
            appt_date = parse_date_value(row['appointment_date'])
            pg_cursor.execute("INSERT INTO directors_data.directorships (id, din, company_id, position, appointment_date) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING", 
                             (row['id'], row['din'], row['company_id'], row['position'], appt_date))
        
        # 4. Document Summaries
        logger.info("Migrating directors_data.document_summaries...")
        sqlite_cursor.execute("SELECT id, director_name, din, file_path, full_text, summary, created_at, updated_at FROM document_summaries")
        rows = sqlite_cursor.fetchall()
        for row in rows:
            pg_cursor.execute("INSERT INTO directors_data.document_summaries (id, director_name, din, file_path, full_text, summary, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING", 
                             (row['id'], row['director_name'], row['din'], row['file_path'], row['full_text'], row['summary'], row['created_at'], row['updated_at']))
        
        pg_conn.commit()
    finally:
        sqlite_conn.close()
        pg_conn.close()

def migrate_directors_db():
    """Migrate directors.db to directors_master.directors"""
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "directors.db")
    if not os.path.exists(sqlite_path): return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute("TRUNCATE TABLE directors_master.directors CASCADE")
        sqlite_cursor.execute("SELECT id, name, din, created_at FROM directors")
        rows = sqlite_cursor.fetchall()
        for row in rows:
            pg_cursor.execute("INSERT INTO directors_master.directors (id, name, din, created_at) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING", 
                             (row['id'], row['name'], row['din'], row['created_at']))
        pg_conn.commit()
    finally:
        sqlite_conn.close()
        pg_conn.close()

def migrate_directors_profile_db():
    """Migrate directors_profile.db to directors_profile schema"""
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "directors_profile.db")
    if not os.path.exists(sqlite_path): return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute("TRUNCATE TABLE directors_profile.directors_profile")
        
        sqlite_cursor.execute("PRAGMA table_info(directors_profile)")
        cols = [c[1].lower() for c in sqlite_cursor.fetchall()]
        
        query = "SELECT " + ( "id, " if 'id' in cols else "ROWID as id, " ) + \
                "DIN, PAN, Name_of_Director, Address, Date_of_Birth, Qualification, " + \
                "Nature_of_Experience_in_specific_Functional_Areas FROM directors_profile"
        
        sqlite_cursor.execute(query)
        rows = sqlite_cursor.fetchall()
        for row in rows:
            din_value = row['DIN']
            if not din_value:
                continue
            
            # Check if DIN exists in master table to satisfy FK constraint
            pg_cursor.execute("SELECT 1 FROM directors_master.directors WHERE din = %s", (din_value,))
            if not pg_cursor.fetchone():
                logger.warning(f"Skipping profile for DIN {din_value} - not found in directors_master.directors")
                continue

            dob = parse_date_value(row['Date_of_Birth'])
            pg_cursor.execute("""
                INSERT INTO directors_profile.directors_profile (id, din, pan, name_of_director, address, date_of_birth, qualification, experience)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (din) DO UPDATE SET
                    id = EXCLUDED.id, pan = EXCLUDED.pan, name_of_director = EXCLUDED.name_of_director, 
                    address = EXCLUDED.address, date_of_birth = EXCLUDED.date_of_birth, 
                    qualification = EXCLUDED.qualification, experience = EXCLUDED.experience
            """, (row['id'], din_value, row['PAN'], row['Name_of_Director'], row['Address'], dob, row['Qualification'], row['Nature_of_Experience_in_specific_Functional_Areas']))
        pg_conn.commit()
    finally:
        sqlite_conn.close()
        pg_conn.close()

def migrate_director_family_info_db():
    """Migrate Director_Family_Information.db to family_information schema"""
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "Director_Family_Information.db")
    if not os.path.exists(sqlite_path): return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute("TRUNCATE TABLE family_information.director_family")
        
        # Check table name (Sheet1 is default for many Adani SQLite exports)
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Sheet1'")
        if not sqlite_cursor.fetchone():
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            tbl = sqlite_cursor.fetchone()[0]
        else: tbl = 'Sheet1'
        
        sqlite_cursor.execute(f"""
            SELECT Name, "Section_2(77)(i)", "Section_2(77)(ii)", "Section_2(77)(iii)",
                   Father, Mother, Son, "Son's_Wife", Daughter, "Daughter's_husband", 
                   Brother, Sister, Father_PAN, Mother_PAN, Father_PAN_File, Mother_PAN_File, Is_Submitted
            FROM {tbl}
        """)
        rows = sqlite_cursor.fetchall()
        for row in rows:
            pg_cursor.execute("""
                INSERT INTO family_information.director_family
                (director_name, section_2_77_i, section_2_77_ii, section_2_77_iii, father, mother, son, sons_wife, daughter, daughters_husband, brother, sister, father_pan, mother_pan, father_pan_file, mother_pan_file, is_submitted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (row['Name'], row['Section_2(77)(i)'], row['Section_2(77)(ii)'], row['Section_2(77)(iii)'], row['Father'], row['Mother'], row['Son'], row["Son's_Wife"], row['Daughter'], row["Daughter's_husband"], row['Brother'], row['Sister'], row['Father_PAN'], row['Mother_PAN'], row['Father_PAN_File'], row['Mother_PAN_File'], row['Is_Submitted']))
        pg_conn.commit()
    finally:
        sqlite_conn.close()
        pg_conn.close()

def main():
    import sys
    selected = sys.argv[1].lower() if len(sys.argv) > 1 else None
    logger.info(f"Starting migration... Target: {selected or 'ALL'}")
    
    try:
        if not selected or selected == 'init':
            create_director_disclosure_database()
            create_schemas_and_tables()
            if selected == 'init': return
        
        if not selected or "directors_data" in selected: migrate_directors_data_db()
        if not selected or "directors.db" in selected or "master" in selected: migrate_directors_db()
        if not selected or "profile" in selected: migrate_directors_profile_db()
        if not selected or "family" in selected: migrate_director_family_info_db()
        
        logger.info("Migration task completed!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()