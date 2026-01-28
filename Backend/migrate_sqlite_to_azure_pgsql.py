#!/usr/bin/env python3
"""
Script to migrate SQLite databases to Azure PostgreSQL for Director Disclosure system python migrate_sqlite_to_azure_pgsql.py
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure PostgreSQL credentials
AZURE_PG_CONFIG = {
    'host': 'az10psqldmrcbtp01.postgres.database.azure.com',
    'user': 'psqladmin',
    'password': '1k8h02grUu+qJ2uHZb<{lB3LF%+Yj-Ar',
    'port': 5432,
    'database': 'postgres'  # Using default database first, will create new one
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

def create_director_disclosure_database():
    """Create the director_disclosure_system database"""
    conn = connect_to_azure_pgsql()
    conn.autocommit = True  # Required for CREATE DATABASE
    cursor = conn.cursor()
    
    try:
        # Check if database already exists
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
    """Connect to the director disclosure database"""
    try:
        conn = psycopg2.connect(
            host=AZURE_PG_CONFIG['host'],
            user=AZURE_PG_CONFIG['user'],
            password=AZURE_PG_CONFIG['password'],
            port=AZURE_PG_CONFIG['port'],
            database='director_disclosure_system'
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to director_disclosure_system: {e}")
        raise

def create_schemas_and_tables():
    """Create schemas and tables in Azure PostgreSQL"""
    conn = connect_to_director_disclosure_db()
    cursor = conn.cursor()
    
    try:
        # Create schemas
        schemas = [
            "CREATE SCHEMA IF NOT EXISTS directors_master;",
            "CREATE SCHEMA IF NOT EXISTS directors_data;",
            "CREATE SCHEMA IF NOT EXISTS directors_profile;",
            "CREATE SCHEMA IF NOT EXISTS family_information;"
        ]
        
        for schema in schemas:
            cursor.execute(schema)
        
        # Create tables
        
        # directors_master.directors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_master.directors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                din TEXT UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_directors_master_din 
            ON directors_master.directors(din);
        """)
        
        # directors_data.directors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.directors (
                din TEXT PRIMARY KEY,
                name TEXT,
                source_file TEXT
            );
        """)
        
        # directors_data.companies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.companies (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                type TEXT
            );
        """)
                
        # directors_data.directorships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.directorships (
                id SERIAL PRIMARY KEY,
                din TEXT REFERENCES directors_data.directors(din) ON DELETE CASCADE,
                company_id INTEGER REFERENCES directors_data.companies(id) ON DELETE CASCADE,
                position TEXT,
                appointment_date DATE
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_directorships_din 
            ON directors_data.directorships(din);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_directorships_company_id 
            ON directors_data.directorships(company_id);
        """)
        
        # directors_data.document_summaries
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
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_summaries_file_path 
            ON directors_data.document_summaries(file_path);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_summaries_director_name 
            ON directors_data.document_summaries(director_name);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_summaries_din 
            ON directors_data.document_summaries(din);
        """)
        
        # directors_profile.directors_profile
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
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_directors_profile_pan 
            ON directors_profile.directors_profile(pan);
        """)
        
        # family_information.director_family
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
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_director_family_name 
            ON family_information.director_family(director_name);
        """)
        
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
    """Get connection to SQLite database"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def migrate_directors_data_db():
    """Migrate directors_data.db to Azure PostgreSQL directors_data schema"""
    # Local SQLite path
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "directors_data.db")
    
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}. Skipping directors_data migration.")
        return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Migrate directors table
        logger.info("Migrating directors_data.directors...")
        sqlite_cursor.execute("SELECT din, name, source_file FROM directors")
        directors = sqlite_cursor.fetchall()
        
        for row in directors:
            pg_cursor.execute("""
                INSERT INTO directors_data.directors (din, name, source_file)
                VALUES (%s, %s, %s)
                ON CONFLICT (din) DO NOTHING
            """, (row['din'], row['name'], row['source_file']))
        
        logger.info(f"Migrated {len(directors)} directors")
        
        # Migrate companies table
        logger.info("Migrating directors_data.companies...")
        
        # Drop the check constraint if it exists to allow 'Unknown' values
        pg_cursor.execute("""
            ALTER TABLE directors_data.companies DROP CONSTRAINT IF EXISTS companies_type_check;
        """)
        
        sqlite_cursor.execute("SELECT id, name, type FROM companies")
        companies = sqlite_cursor.fetchall()
        
        for row in companies:
            # Handle unknown company types by setting them to a valid type
            company_type = row['type']
            if company_type not in ['Public', 'Private - Subsidiary of Public', 'Private - Not Subsidiary of Public', 'Unknown']:
                company_type = 'Unknown'
            pg_cursor.execute("""
                INSERT INTO directors_data.companies (id, name, type)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (row['id'], row['name'], company_type))
        
        logger.info(f"Migrated {len(companies)} companies")
        
        # Migrate directorships table
        logger.info("Migrating directors_data.directorships...")
        sqlite_cursor.execute("SELECT id, din, company_id, position, appointment_date FROM directorships")
        directorships = sqlite_cursor.fetchall()
        
        for row in directorships:
            # Handle empty appointment dates by setting them to NULL
            # Also convert date format from DD/MM/YYYY to YYYY-MM-DD if needed
            appointment_date = row['appointment_date']
            if appointment_date:
                # Check if date is in DD/MM/YYYY format and convert to YYYY-MM-DD
                if '/' in appointment_date and len(appointment_date) == 10:
                    try:
                        day, month, year = appointment_date.split('/')
                        appointment_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    except ValueError:
                        # If parsing fails, set to None
                        appointment_date = None
            else:
                appointment_date = None
                
            pg_cursor.execute("""
                INSERT INTO directors_data.directorships (id, din, company_id, position, appointment_date)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (row['id'], row['din'], row['company_id'], row['position'], appointment_date))
        
        logger.info(f"Migrated {len(directorships)} directorships")
        
        # Migrate document_summaries table
        logger.info("Migrating directors_data.document_summaries...")
        sqlite_cursor.execute("SELECT id, director_name, din, file_path, full_text, summary, created_at, updated_at FROM document_summaries")
        summaries = sqlite_cursor.fetchall()
        
        for row in summaries:
            pg_cursor.execute("""
                INSERT INTO directors_data.document_summaries (id, director_name, din, file_path, full_text, summary, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (row['id'], row['director_name'], row['din'], row['file_path'], 
                  row['full_text'], row['summary'], row['created_at'], row['updated_at']))
        
        logger.info(f"Migrated {len(summaries)} document summaries")
        
        pg_conn.commit()
        logger.info("Completed migration of directors_data.db")
        
    except Exception as e:
        logger.error(f"Error migrating directors_data.db: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

def migrate_directors_db():
    """Migrate directors.db to Azure PostgreSQL directors_master schema"""
    # Local SQLite path
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "directors.db")
    
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}. Skipping directors migration.")
        return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Migrate directors table to directors_master schema
        logger.info("Migrating directors.db to directors_master.directors...")
        sqlite_cursor.execute("SELECT id, name, din, created_at FROM directors")
        directors = sqlite_cursor.fetchall()
        
        for row in directors:
            pg_cursor.execute("""
                INSERT INTO directors_master.directors (id, name, din, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (row['id'], row['name'], row['din'], row['created_at']))
        
        logger.info(f"Migrated {len(directors)} directors to master table")
        
        pg_conn.commit()
        logger.info("Completed migration of directors.db")
        
    except Exception as e:
        logger.error(f"Error migrating directors.db: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

def parse_date_value(date_str):
    """Parse various date formats and convert to YYYY-MM-DD format for PostgreSQL"""
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ['null', 'none', '']:
        return None
    
    # Handle various formats
    try:
        # Handle the main format from SQLite: "YYYY-MM-DD 00:00:00"
        if ' ' in date_str and ':' in date_str:
            # Format is "YYYY-MM-DD 00:00:00", extract just the date part
            date_part = date_str.split(' ')[0]  # Get "YYYY-MM-DD"
            if len(date_part) == 10 and date_part.count('-') == 2:
                return date_part  # Already in correct format
        
        # If it's already in YYYY-MM-DD format
        if '-' in date_str and len(date_str) == 10 and date_str.count('-') == 2:
            parts = date_str.split('-')
            if len(parts) == 3 and len(parts[0]) == 4:  # Year is first
                return date_str
        
        # Handle DD/MM/YYYY format
        if '/' in date_str and date_str.count('/') == 2:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year.zfill(2).strip()}-{month.zfill(2).strip()}-{day.zfill(2).strip()}"
        
        # Handle DD-MM-YYYY format
        elif '-' in date_str and date_str.count('-') == 2 and len(date_str) >= 8:
            parts = date_str.split('-')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year.zfill(2).strip()}-{month.zfill(2).strip()}-{day.zfill(2).strip()}"
        
        # Handle the problematic format like "24 00:00:00-06-1962" (if it exists)
        if ' ' in date_str and '-' in date_str and ':' in date_str:
            # Extract date part from "24 00:00:00-06-1962" -> day "24" month "06" year "1962"
            # Split by space first: ["24", "00:00:00-06-1962"]
            parts = date_str.split(' ', 1)  # Split only on first space to avoid splitting time
            if len(parts) == 2:
                day_part = parts[0].strip()  # "24"
                # The second part should be "00:00:00-06-1962"
                time_date_part = parts[1]
                # Split the time-date part by '-': ["00:00:00", "06", "1962"]
                date_parts = time_date_part.split('-')
                if len(date_parts) == 3:  # "00:00:00", "06", "1962"
                    month = date_parts[1]  # "06"
                    year = date_parts[2]   # "1962"
                    return f"{year.zfill(4).strip()}-{month.zfill(2).strip()}-{day_part.zfill(2).strip()}"
                elif len(date_parts) == 2:  # Sometimes it might be "00:00:00-06-1962" but parsed differently
                    # Look for the pattern where the first part has colons
                    if ':' in date_parts[0]:
                        month = date_parts[1][:2] if len(date_parts[1]) >= 2 else date_parts[1][:1]  # First 2 chars of second part
                        year_str = date_parts[1][2:] if len(date_parts[1]) > 2 else '1900'  # Remaining chars as year
                        if year_str.isdigit() and len(year_str) == 2:
                            year = '19' + year_str  # Convert 2-digit year to 4-digit
                        elif year_str.isdigit() and len(year_str) == 4:
                            year = year_str
                        else:
                            year = '1900'  # Default if parsing fails
                        return f"{year.zfill(4).strip()}-{month.zfill(2).strip()}-{day_part.zfill(2).strip()}"
                    else:
                        # Fallback: try to extract month and year from the second part
                        import re
                        nums = re.findall(r'\d+', date_parts[1])
                        if len(nums) >= 2:
                            month = nums[0]
                            year = nums[1]
                            if len(year) == 2:
                                year = '19' + year
                            return f"{year.zfill(4).strip()}-{month.zfill(2).strip()}-{day_part.zfill(2).strip()}"
            
            # Alternative approach for "24 00:00:00-06-1962" format
            # If the above didn't work, try a different approach
            import re
            # Match the pattern: day followed by time and date
            match = re.match(r'(\d+)\s+(\d+:\d+:\d+)-(\d+)-(\d+)', date_str)
            if match:
                day, _, month, year = match.groups()
                if len(year) == 2:
                    year = '19' + year
                return f"{year.zfill(4).strip()}-{month.zfill(2).strip()}-{day.zfill(2).strip()}"
        
        # If none of the above worked, try to extract numbers
        import re
        numbers = re.findall(r'\d+', date_str)
        if len(numbers) >= 3:
            # Assume format is day-month-year or day-month-year
            day = numbers[0][:2]  # Take first 2 digits as day
            month = numbers[1][:2]  # Take next 2 digits as month
            year = numbers[2][:4]  # Take up to 4 digits as year
            return f"{year.zfill(4).strip()}-{month.zfill(2).strip()}-{day.zfill(2).strip()}"
        
        # If all parsing attempts fail, return None
        return None
        
    except Exception:
        # If any error occurs during parsing, return None
        return None

def migrate_directors_profile_db():
    """Migrate directors_profile.db to Azure PostgreSQL directors_profile schema"""
    # Local SQLite path
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "directors_profile.db")
    
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}. Skipping directors_profile migration.")
        return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Migrate directors_profile table
        logger.info("Migrating directors_profile.db to directors_profile.directors_profile...")
        
        # First, get the column names to handle schema differences
        sqlite_cursor.execute("PRAGMA table_info(directors_profile)")
        columns_info = sqlite_cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        # Build query based on available columns
        if 'id' in column_names:
            query = """
                SELECT id, DIN, PAN, Name_of_Director, Address, Date_of_Birth, 
                       Qualification, Nature_of_Experience_in_specific_Functional_Areas
                FROM directors_profile
            """
        else:
            # If no id column, use ROWID as the id
            query = """
                SELECT ROWID as id, DIN, PAN, Name_of_Director, Address, Date_of_Birth, 
                       Qualification, Nature_of_Experience_in_specific_Functional_Areas
                FROM directors_profile
            """
        
        sqlite_cursor.execute(query)
        profiles = sqlite_cursor.fetchall()
        
        for row in profiles:
            # Check if the DIN exists in the directors table to satisfy foreign key constraint
            din_value = row['DIN'] if row['DIN'] else None
            if din_value:
                # Verify if DIN exists in directors table
                pg_cursor.execute("SELECT 1 FROM directors_master.directors WHERE din = %s LIMIT 1", (din_value,))
                din_exists = pg_cursor.fetchone()
                
                if din_exists:
                    # DIN exists, safe to insert
                    # Handle date format for date_of_birth
                    date_of_birth = row['Date_of_Birth']
                    if date_of_birth:
                        date_of_birth = date_of_birth.strip()  # Remove leading/trailing spaces
                        # Handle various date formats
                        date_of_birth = parse_date_value(date_of_birth)
                    
                    pg_cursor.execute("""
                        INSERT INTO directors_profile.directors_profile 
                        (id, din, pan, name_of_director, address, date_of_birth, qualification, experience)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (din) DO UPDATE SET
                            id = EXCLUDED.id,
                            pan = COALESCE(EXCLUDED.pan, directors_profile.pan),
                            name_of_director = COALESCE(EXCLUDED.name_of_director, directors_profile.name_of_director),
                            address = COALESCE(EXCLUDED.address, directors_profile.address),
                            date_of_birth = COALESCE(EXCLUDED.date_of_birth, directors_profile.date_of_birth),
                            qualification = COALESCE(EXCLUDED.qualification, directors_profile.qualification),
                            experience = COALESCE(EXCLUDED.experience, directors_profile.experience)
                    """, (row['id'], row['DIN'], row['PAN'], row['Name_of_Director'], 
                          row['Address'], date_of_birth, row['Qualification'], 
                          row['Nature_of_Experience_in_specific_Functional_Areas']))
                else:
                    # DIN doesn't exist in directors table, skip or handle differently
                    logger.warning(f"Skipping profile for DIN {din_value} - not found in directors table")
            else:
                # DIN is null, insert anyway
                # Handle date format for date_of_birth
                date_of_birth = row['Date_of_Birth']
                if date_of_birth:
                    date_of_birth = date_of_birth.strip()  # Remove leading/trailing spaces
                    # Handle various date formats
                    date_of_birth = parse_date_value(date_of_birth)
                            
                pg_cursor.execute("""
                    INSERT INTO directors_profile.directors_profile 
                    (id, din, pan, name_of_director, address, date_of_birth, qualification, experience)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (din) DO UPDATE SET
                        id = EXCLUDED.id,
                        pan = COALESCE(EXCLUDED.pan, directors_profile.pan),
                        name_of_director = COALESCE(EXCLUDED.name_of_director, directors_profile.name_of_director),
                        address = COALESCE(EXCLUDED.address, directors_profile.address),
                        date_of_birth = COALESCE(EXCLUDED.date_of_birth, directors_profile.date_of_birth),
                        qualification = COALESCE(EXCLUDED.qualification, directors_profile.qualification),
                        experience = COALESCE(EXCLUDED.experience, directors_profile.experience)
                """, (row['id'], row['DIN'], row['PAN'], row['Name_of_director'], 
                      row['Address'], date_of_birth, row['Qualification'], 
                      row['Nature_of_Experience_in_specific_Functional_Areas']))
        
        logger.info(f"Migrated {len(profiles)} director profiles")
        
        pg_conn.commit()
        logger.info("Completed migration of directors_profile.db")
        
    except Exception as e:
        logger.error(f"Error migrating directors_profile.db: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

def migrate_director_family_info_db():
    """Migrate Director_Family_Information.db to Azure PostgreSQL family_information schema"""
    # Local SQLite path
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "Director_Family_Information.db")
    
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}. Skipping director family info migration.")
        return
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_director_disclosure_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Migrate director family information
        logger.info("Migrating Director_Family_Information.db to family_information.director_family...")
        sqlite_cursor.execute("""
            SELECT Name, "Section_2(77)(i)", "Section_2(77)(ii)", "Section_2(77)(iii)",
                   Father, Mother, Son, "Son's_Wife", Daughter, "Daughter's_husband", 
                   Brother, Sister
            FROM Sheet1
        """)
        families = sqlite_cursor.fetchall()
        
        for row in families:
            pg_cursor.execute("""
                INSERT INTO family_information.director_family
                (director_name, section_2_77_i, section_2_77_ii, section_2_77_iii,
                 father, mother, son, sons_wife, daughter, daughters_husband, 
                 brother, sister)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (row['Name'], row['Section_2(77)(i)'], row['Section_2(77)(ii)'], 
                  row['Section_2(77)(iii)'], row['Father'], row['Mother'], 
                  row['Son'], row["Son's_Wife"], row['Daughter'], 
                  row["Daughter's_husband"], row['Brother'], row['Sister']))
        
        logger.info(f"Migrated {len(families)} director family records")
        
        pg_conn.commit()
        logger.info("Completed migration of Director_Family_Information.db")
        
    except Exception as e:
        logger.error(f"Error migrating Director_Family_Information.db: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

def main():
    """Main function to orchestrate the migration"""
    logger.info("Starting migration of Director Disclosure databases to Azure PostgreSQL")
    
    try:
        # Step 1: Create the target database
        logger.info("Step 1: Creating director_disclosure_system database")
        create_director_disclosure_database()
        
        # Step 2: Create schemas and tables
        logger.info("Step 2: Creating schemas and tables")
        create_schemas_and_tables()
        
        # Step 3: Migrate each database
        logger.info("Step 3: Starting data migration")
        
        migrate_directors_data_db()
        migrate_directors_db()
        migrate_directors_profile_db()
        migrate_director_family_info_db()
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()