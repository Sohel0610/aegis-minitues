# Database Initialization Utilities
# Consolidating visits and places into PostgreSQL for production.
import logging
import os
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

def init_postgres_tracking():
    """Initialize visits and places in PostgreSQL's public schema."""
    # Use dedicated visits database
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_VISITS'))
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            # Visits table in public schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seed visit if empty
            cursor.execute("SELECT COUNT(*) FROM visits")
            if cursor.fetchone()["count"] == 0:
                cursor.execute("INSERT INTO visits (id, count) VALUES (1, 0)")
            
            # Places table in public schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS places (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seed default place if empty
            cursor.execute("SELECT COUNT(*) FROM places WHERE is_default = TRUE")
            if cursor.fetchone()["count"] == 0:
                cursor.execute("""
                    INSERT INTO places (name, address, is_default)
                    VALUES (%s, %s, TRUE)
                """, ('Adani Corporate House', 'Shantigram, Near Vaishno Devi Circle, Ahmedabad'))
            
            conn.commit()
            logger.info("Tracking PostgreSQL public schema initialized successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Tracking init failed: {e}")
        finally:
            conn.close()