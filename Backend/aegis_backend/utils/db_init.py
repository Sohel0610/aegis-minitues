# Database Initialization Utilities
# Consolidating visits and places into PostgreSQL for production.
import logging
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Schema for tracking
DB_SCHEMA = "tracking"

def init_postgres_tracking():
    """Initialize visits and places in PostgreSQL."""
    conn = get_pg_connection()
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            # Visits table
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
            
            # Places table
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
                """, ('Adani Corporate House', 'Shantigram, Near Vaishno Devi Circle, Ahmedabad', True))
            
            conn.commit()
            logger.info("Tracking PostgreSQL schema initialized successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Tracking init failed: {e}")
        finally:
            conn.close()

# Migration: No more SQLite calls on import
# We will call this from fastapi_server.py