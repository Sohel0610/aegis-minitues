import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import logging
import os
import threading
from dotenv import load_dotenv

# Ensure we load the backend-local .env even when the server is started from `Backend/`.
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
logger = logging.getLogger(__name__)

_pools = {}
_pools_lock = threading.Lock()

class PooledConnection:
    """Proxy a pooled psycopg2 connection so `.close()` returns it to the pool."""

    def __init__(self, conn, pool_key):
        self._conn = conn
        self._pool_key = pool_key
        self._returned = False

    def close(self):
        if self._returned or self._conn is None:
            return

        with _pools_lock:
            pool = _pools.get(self._pool_key)

        if pool:
            try:
                if not self._conn.closed:
                    self._conn.rollback()
            except Exception:
                pass
            try:
                pool.putconn(self._conn)
            except Exception:
                try:
                    self._conn.close()
                except Exception:
                    pass
        else:
            try:
                self._conn.close()
            except Exception:
                pass

        self._returned = True
        self._conn = None

    def __getattr__(self, name):
        if self._conn is None:
            raise AttributeError(name)
        return getattr(self._conn, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

def get_pg_connection(database=None):
    """
    Get a PostgreSQL connection from the pool.
    Explicitly supports multi-database strategy (Director, BSE, Insider Trading).
    """
    host     = (os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost').strip()
    user     = (os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or '').strip()
    password = os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD')
    port     = (os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432').strip()

    # Fallback logic for database name
    if not database:
        database = os.getenv('POSTGRES_DATABASE') or os.getenv('DB_NAME')
    
    if database:
        database = database.strip()

    if not all([host, user, password, database]):
        logger.error(f"Missing PostgreSQL credentials: {{'Host': bool(host), 'User': bool(user), 'DB': bool(database)}}")
        return None

    pool_key = f"{host}:{port}:{database}"
    
    with _pools_lock:
        if pool_key not in _pools:
            conn_params = {
                'host': host,
                'user': user,
                'password': password,
                'port': int(port),
                'database': database,
                'connect_timeout': 10
            }
            
            # Security Rule: Enforce SSL (Required for Production Azure Instance)
            sslmode = os.getenv('POSTGRES_SSLMODE') or os.getenv('DB_SSLMODE')
            if sslmode:
                conn_params['sslmode'] = sslmode
            elif 'azure.com' in host.lower():
                conn_params['sslmode'] = 'require'
                
            try:
                logger.info(f"Initializing Multi-DB Connection Pool: {database} @ {host}")
                # Use ThreadedConnectionPool for FastAPI concurrency
                _pools[pool_key] = psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=25, **conn_params)
            except Exception as e:
                logger.error(f"Critical: Failed to initialize pool for {database}: {e}")
                raise RuntimeError(f"Database connection pool initialization failed: {e}")

    try:
        conn = _pools[pool_key].getconn()
        return PooledConnection(conn, pool_key)
    except Exception as e:
        logger.error(f"Pool exhausted or connection unavailable (DB: {database}): {e}")
        raise RuntimeError(f"Database connection unavailable: {e}")

def put_pg_connection(conn):
    """Explicitly return a connection to the pool (or use context manager)."""
    if conn and isinstance(conn, PooledConnection):
        conn.close()

def get_pg_cursor(conn):
    """Get a RealDictCursor for the given connection."""
    if conn:
        return conn.cursor(cursor_factory=RealDictCursor)
    return None

def check_pg_health() -> bool:
    """Check if PostgreSQL is reachable."""
    conn = get_pg_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"PG Health Check failed: {e}")
        return False
    finally:
        conn.close()
