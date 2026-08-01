#!/usr/bin/env python3
"""
Script to migrate places.db to Azure PostgreSQL for Minutes Preparation system migrate_places_to_azure_pgsql.py
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

def create_minutes_preparation_database():
    """Create the minutes_preparation_system database"""
    conn = connect_to_azure_pgsql()
    conn.autocommit = True  # Required for CREATE DATABASE
    cursor = conn.cursor()
    
    try:
        # Check if database already exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'minutes_preparation_system'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE minutes_preparation_system")
            logger.info("Created database 'minutes_preparation_system'")
        else:
            logger.info("Database 'minutes_preparation_system' already exists")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def connect_to_minutes_preparation_db():
    """Connect to the minutes preparation database"""
    try:
        conn = psycopg2.connect(
            host=AZURE_PG_CONFIG['host'],
            user=AZURE_PG_CONFIG['user'],
            password=AZURE_PG_CONFIG['password'],
            port=AZURE_PG_CONFIG['port'],
            database='minutes_preparation_system'
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to minutes_preparation_system: {e}")
        raise

def create_places_schema_and_tables():
    """Create schema and tables for places in Azure PostgreSQL"""
    conn = connect_to_minutes_preparation_db()
    cursor = conn.cursor()
    
    try:
        # Create places schema
        cursor.execute("CREATE SCHEMA IF NOT EXISTS locations;")
        
        # Create places table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations.places (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create index on is_default for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_places_is_default 
            ON locations.places(is_default);
        """)
        
        # Create index on name for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_places_name 
            ON locations.places(name);
        """)
        
        conn.commit()
        logger.info("Created locations schema and places table successfully")
        
    except Exception as e:
        logger.error(f"Error creating schema and tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

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
                return f"{year.zfill(4).strip()}-{month.zfill(2).strip()}-{day_part.zfill(2).strip()}"
        
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

def get_sqlite_connection(db_path: str):
    """Get connection to SQLite database"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def migrate_places_db():
    """Migrate places.db to Azure PostgreSQL locations.places table"""
    # Local SQLite path
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", "places.db")
    
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found: {sqlite_path}")
        raise FileNotFoundError(f"places.db not found at {sqlite_path}")
    
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = connect_to_minutes_preparation_db()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Migrate places table
        logger.info("Migrating places...")
        sqlite_cursor.execute("SELECT id, name, address, is_default, created_at FROM places")
        places = sqlite_cursor.fetchall()
        
        for row in places:
            # Handle boolean conversion for is_default (SQLite stores as int, PG expects bool)
            is_default_bool = bool(row['is_default']) if row['is_default'] is not None else False
            
            # Handle date format for created_at
            created_at = row['created_at']
            if created_at:
                created_at = created_at.strip()  # Remove leading/trailing spaces
                # Handle various date formats
                created_at = parse_date_value(created_at)
            
            pg_cursor.execute("""
                INSERT INTO locations.places (id, name, address, is_default, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    address = EXCLUDED.address,
                    is_default = EXCLUDED.is_default,
                    created_at = EXCLUDED.created_at
            """, (row['id'], row['name'], row['address'], is_default_bool, created_at))
        
        logger.info(f"Migrated {len(places)} places")
        
        pg_conn.commit()
        logger.info("Completed migration of places.db")
        
    except Exception as e:
        logger.error(f"Error migrating places.db: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    conn = connect_to_minutes_preparation_db()
    cursor = conn.cursor()
    
    try:
        # Count records in the places table
        cursor.execute("SELECT COUNT(*) as count FROM locations.places")
        result = cursor.fetchone()
        count = result['count'] if result else 0
        
        logger.info(f"Verification: Found {count} records in locations.places table")
        
        # Show sample records
        cursor.execute("SELECT id, name, address, is_default FROM locations.places LIMIT 5")
        samples = cursor.fetchall()
        
        logger.info("Sample records:")
        for record in samples:
            logger.info(f"  ID: {record['id']}, Name: {record['name']}, Default: {record['is_default']}")
        
        return count > 0
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to orchestrate the places migration"""
    logger.info("Starting migration of Places database to Azure PostgreSQL for Minutes Preparation System")
    
    try:
        # Step 1: Create the target database
        logger.info("Step 1: Creating minutes_preparation_system database")
        create_minutes_preparation_database()
        
        # Step 2: Create schema and tables
        logger.info("Step 2: Creating locations schema and places table")
        create_places_schema_and_tables()
        
        # Step 3: Migrate places database
        logger.info("Step 3: Starting places data migration")
        migrate_places_db()
        
        # Step 4: Verify migration
        logger.info("Step 4: Verifying migration")
        if verify_migration():
            logger.info("Migration completed successfully!")
        else:
            logger.warning("Migration completed but verification showed unexpected results")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()