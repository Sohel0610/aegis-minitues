import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_pg_connection(database=None):
    """Establish connection to Azure PostgreSQL using environment variables"""
    try:
        host = os.getenv('POSTGRES_HOST')
        user = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        port = os.getenv('POSTGRES_PORT', 5432)
        
        # Default to director database if not specified
        if not database:
            database = os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system')

        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database=database
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Azure PostgreSQL (DB: {database}): {e}")
        return None

def get_pg_cursor(conn):
    """Get a cursor that returns rows as dictionaries"""
    if conn:
        return conn.cursor(cursor_factory=RealDictCursor)
    return None
