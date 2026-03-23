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
    host     = os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST')
    user     = os.getenv('POSTGRES_USER') or os.getenv('DB_USER')
    password = os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD')
    port     = os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT')

    if not database:
        database = os.getenv('POSTGRES_DATABASE_DIRECTOR') or os.getenv('POSTGRES_DATABASE') or os.getenv('DB_NAME')

    if not all([host, user, password, database]):
        logger.error(f"Missing PostgreSQL vars (Host: {bool(host)}, User: {bool(user)}, DB: {bool(database)})")
        return None

    pool_key = f"{host}:{port}:{database}"
    with _pools_lock:
        if pool_key not in _pools:
            conn_params = {
                'host': host,
                'user': user,
                'password': password,
                'port': int(port) if port else 5432,
                'database': database,
                'connect_timeout': 5
            }
            if host and 'azure.com' in host.lower():
                conn_params['sslmode'] = 'require'
            try:
                _pools[pool_key] = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=4, **conn_params)
            except Exception as e:
                logger.error(f"Failed to create pool for {database}: {e}")
                return None

    try:
        conn = _pools[pool_key].getconn()
        return PooledConnection(conn, pool_key)
    except Exception as e:
        logger.error(f"Pool getconn failed (DB: {database}): {e}")
        return None

def put_pg_connection(conn, database=None):
    if not conn:
        return
    if isinstance(conn, PooledConnection):
        conn.close()
        return
    host = os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST')
    port = os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT')
    if not database:
        database = os.getenv('POSTGRES_DATABASE_DIRECTOR') or os.getenv('POSTGRES_DATABASE') or os.getenv('DB_NAME')
    pool_key = f"{host}:{port}:{database}"
    with _pools_lock:
        if pool_key in _pools:
            try:
                _pools[pool_key].putconn(conn)
            except Exception:
                pass

def get_pg_cursor(conn):
    if conn:
        return conn.cursor(cursor_factory=RealDictCursor)
    return None
