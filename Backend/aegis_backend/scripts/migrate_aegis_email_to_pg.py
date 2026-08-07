import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SQLITE_DB_PATH = r"C:\Users\agel_rpabot_pm\Downloads\aegis-platform 1\aegis-platform\Backend\aegis_backend\public\email_data.db"
POSTGRES_CONFIG = {
    "host": "az10psqldmrcbtp01.postgres.database.azure.com",
    "user": "psqladmin",
    "password": "1k8h02grUu+qJ2uHZb<{lB3LF%+Yj-Ar",
    "port": 5432,
    "database": "aegis_email_system"
}

def migrate_data():
    sqlite_conn = None
    pg_conn = None
    
    try:
        # 1. Connect to SQLite
        logger.info(f"Connecting to SQLite database: {SQLITE_DB_PATH}")
        if not os.path.exists(SQLITE_DB_PATH):
            logger.error(f"SQLite database file not found: {SQLITE_DB_PATH}")
            return
            
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        # 2. Connect to PostgreSQL
        logger.info(f"Connecting to Azure PostgreSQL: {POSTGRES_CONFIG['host']}")
        # To create the database if it doesn't exist, we'd need to connect to 'postgres' first.
        # But we'll assume the 'aegis_email_system' database is already created or that
        # we can just connect to it for now.
        try:
            pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        except psycopg2.OperationalError:
            # Fallback: connect to default 'postgres' to create the database if needed
            logger.warning(f"Database {POSTGRES_CONFIG['database']} not found. Attempting to create it...")
            temp_config = POSTGRES_CONFIG.copy()
            temp_config['database'] = 'postgres'
            temp_conn = psycopg2.connect(**temp_config)
            temp_conn.autocommit = True
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute(f"CREATE DATABASE {POSTGRES_CONFIG['database']}")
            temp_cursor.close()
            temp_conn.close()
            logger.info(f"Database {POSTGRES_CONFIG['database']} created successfully.")
            pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
            
        pg_cursor = pg_conn.cursor()
        
        # 3. Create Schema and Tables if they don't exist
        logger.info("Creating tables in PostgreSQL...")
        
        # Table for emails
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS email (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table for admin credentials
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_credentials (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        pg_conn.commit()
        
        # 4. Migrate 'email' table
        logger.info("Migrating table: email")
        sqlite_cursor.execute("SELECT email FROM email")
        emails = sqlite_cursor.fetchall()
        
        if emails:
            # Using execute_values for efficient insertion and handling potential duplicates
            execute_values(pg_cursor, 
                "INSERT INTO email (email) VALUES %s ON CONFLICT (email) DO NOTHING",
                emails)
            logger.info(f"Successfully migrated {len(emails)} email records.")
        else:
            logger.info("No records found in SQLite 'email' table.")
            
        # 5. Migrate 'admin_credentials' table
        logger.info("Migrating table: admin_credentials")
        # We need the columns: id, username, password. 
        # But SQLite might have different column order, let's be careful.
        try:
            sqlite_cursor.execute("SELECT id, username, password FROM admin_credentials")
            credentials = sqlite_cursor.fetchall()
            
            if credentials:
                execute_values(pg_cursor,
                    "INSERT INTO admin_credentials (id, username, password) VALUES %s ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username, password = EXCLUDED.password",
                    credentials)
                logger.info(f"Successfully migrated {len(credentials)} admin credentials.")
            else:
                logger.info("No records found in SQLite 'admin_credentials' table.")
        except sqlite3.OperationalError as e:
            logger.warning(f"Could not migrate admin_credentials: {e}")
            
        pg_conn.commit()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        if pg_conn:
            pg_conn.rollback()
        logger.error(f"Migration failed: {e}")
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if pg_conn:
            pg_cursor.close()
            pg_conn.close()

if __name__ == "__main__":
    migrate_data()
