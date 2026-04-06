# Database Initialization Utilities
# Consolidating visits and places into PostgreSQL for production.
import logging
import os
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

def init_postgres_tracking():
    """Initialize visits and places in PostgreSQL's visit_tracking schema."""
    # Use dedicated visits database
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_VISITS'))
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            
            # Create visit_tracking schema if it doesn't exist
            cursor.execute("CREATE SCHEMA IF NOT EXISTS visit_tracking")
            
            # Visits table in visit_tracking schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visit_tracking.visits (
                    id SERIAL PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seed visit if empty
            cursor.execute("SELECT COUNT(*) FROM visit_tracking.visits")
            if cursor.fetchone()["count"] == 0:
                cursor.execute("INSERT INTO visit_tracking.visits (id, count) VALUES (1, 0)")
            
            # Places table in visit_tracking schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visit_tracking.places (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seed default place if empty
            cursor.execute("SELECT COUNT(*) FROM visit_tracking.places WHERE is_default = TRUE")
            if cursor.fetchone()["count"] == 0:
                cursor.execute("""
                    INSERT INTO visit_tracking.places (name, address, is_default)
                    VALUES (%s, %s, TRUE)
                """, ('Adani Corporate House', 'Shantigram, Near Vaishno Devi Circle, Ahmedabad'))
            
            conn.commit()
            logger.info("Tracking PostgreSQL visit_tracking schema initialized successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Tracking init failed: {e}")
        finally:
            conn.close()

def init_email_system():
    """Initialize the email system on Azure PostgreSQL."""
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_EMAIL'))
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            
            # Email table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email (
                    email TEXT PRIMARY KEY
                )
            """)
            
            # Admin credentials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_credentials (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            
            # Seed default admin if empty
            cursor.execute("SELECT COUNT(*) FROM admin_credentials")
            if cursor.fetchone()["count"] == 0:
                cursor.execute("INSERT INTO admin_credentials (username, password) VALUES (%s, %s)",
                             ('admin', 'admin@aegis'))
            
            conn.commit()
            logger.info("Email system PostgreSQL initialized successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Email system init failed: {e}")
        finally:
            conn.close()