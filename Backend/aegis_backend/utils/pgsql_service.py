import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import logging
import os
import threading
import sqlite3
import re
from dotenv import load_dotenv

# Ensure we load the backend-local .env even when the server is started from `Backend/`.
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
logger = logging.getLogger(__name__)

_pools = {}
_pools_lock = threading.Lock()

class SQLiteCursorWrapper:
    def __init__(self, sqlite_cursor):
        self.cursor = sqlite_cursor

    def execute(self, query, params=None):
        if not isinstance(query, str):
            if params is not None:
                return self.cursor.execute(query, params)
            return self.cursor.execute(query)

        # 1. Skip unsupported PostgreSQL statements
        query_upper = query.upper()
        if "CREATE SCHEMA" in query_upper or "DO $$" in query_upper:
            return self

        # 2. Schema name stripping: e.g., rbac.user_roles -> user_roles
        query = re.sub(r'\b(rbac|directors_master|directors_data|insider_trading|public|visit_tracking)\.', '', query, flags=re.IGNORECASE)

        # 3. Translate SERIAL to INTEGER PRIMARY KEY AUTOINCREMENT
        query = re.sub(r'\bSERIAL\s+PRIMARY\s+KEY\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', query, flags=re.IGNORECASE)
        query = re.sub(r'\bSERIAL\b', 'INTEGER', query, flags=re.IGNORECASE)

        # 4. Replace %s placeholder with ?
        query = query.replace('%s', '?')

        # 5. Execute with RETURNING fallback if needed
        has_returning = False
        table_name = None
        ret_match = re.search(r'\bRETURNING\b\s+(.+)$', query, re.IGNORECASE)
        if ret_match:
            has_returning = True
            table_match = re.search(r'\bINSERT\s+INTO\s+([a-zA-Z0-9_]+)', query, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1)

        try:
            if params is not None:
                if not isinstance(params, (tuple, list, dict)):
                    params = (params,)
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
        except sqlite3.OperationalError as err:
            # If RETURNING is not supported, do manual fallback
            if has_returning and ("returning" in str(err).lower() or "syntax error" in str(err).lower()):
                base_query = re.sub(r'\bRETURNING\b\s+.+$', '', query, flags=re.IGNORECASE)
                if params is not None:
                    if not isinstance(params, (tuple, list, dict)):
                        params = (params,)
                    self.cursor.execute(base_query, params)
                else:
                    self.cursor.execute(base_query)
                last_id = self.cursor.lastrowid
                if last_id and table_name:
                    self.cursor.execute(f"SELECT * FROM {table_name} WHERE rowid = ?", (last_id,))
            else:
                raise err
        return self

    def _normalize_row(self, row):
        if row is None:
            return None
        d = dict(row)
        normalized = {}
        for k, v in d.items():
            normalized[k] = v
            # Map count(*) to count
            if k.lower() in ('count(*)', 'count(1)'):
                normalized['count'] = v
        return normalized

    def fetchall(self):
        try:
            rows = self.cursor.fetchall()
            return [self._normalize_row(r) for r in rows]
        except Exception:
            return []

    def fetchone(self):
        try:
            row = self.cursor.fetchone()
            return self._normalize_row(row)
        except Exception:
            return None

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class SQLiteConnectionWrapper:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.closed = False

    def cursor(self, cursor_factory=None):
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def close(self):
        if not self.closed:
            try:
                self.conn.close()
            except Exception:
                pass
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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
    Get a PostgreSQL connection from the pool, or fallback to SQLite if configured or unavailable.
    Explicitly supports multi-database strategy (Director, BSE, Insider Trading).
    """
    # SQLite Fallback check
    use_sqlite = os.getenv("USE_SQLITE_FALLBACK", "False").lower() in ("true", "1", "yes")
    if use_sqlite:
        sqlite_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", "local_fallback.db"))
        os.makedirs(os.path.dirname(sqlite_db_path), exist_ok=True)
        logger.info(f"Using SQLite Fallback Database at: {sqlite_db_path}")
        return SQLiteConnectionWrapper(sqlite_db_path)

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
        logger.warning("Missing PostgreSQL credentials. Falling back to local SQLite database.")
        sqlite_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", "local_fallback.db"))
        os.makedirs(os.path.dirname(sqlite_db_path), exist_ok=True)
        return SQLiteConnectionWrapper(sqlite_db_path)

    pool_key = f"{host}:{port}:{database}"
    
    with _pools_lock:
        if pool_key not in _pools:
            conn_params = {
                'host': host,
                'user': user,
                'password': password,
                'port': int(port),
                'database': database,
                'connect_timeout': 3  # Reduced timeout for faster fallback
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
                logger.warning(f"Failed to initialize PostgreSQL pool for {database}: {e}. Falling back to SQLite.")
                sqlite_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", "local_fallback.db"))
                os.makedirs(os.path.dirname(sqlite_db_path), exist_ok=True)
                return SQLiteConnectionWrapper(sqlite_db_path)

    try:
        conn = _pools[pool_key].getconn()
        return PooledConnection(conn, pool_key)
    except Exception as e:
        logger.warning(f"Connection pool exhausted or PostgreSQL unavailable: {e}. Falling back to SQLite.")
        sqlite_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", "local_fallback.db"))
        os.makedirs(os.path.dirname(sqlite_db_path), exist_ok=True)
        return SQLiteConnectionWrapper(sqlite_db_path)

def put_pg_connection(conn):
    """Explicitly return a connection to the pool (or use context manager)."""
    if conn:
        try:
            conn.close()
        except Exception:
            pass

def get_pg_cursor(conn):
    """Get a cursor for the given connection (handles SQLiteWrapper or psycopg2)."""
    if conn:
        if isinstance(conn, SQLiteConnectionWrapper):
            return conn.cursor()
        return conn.cursor(cursor_factory=RealDictCursor)
    return None

def check_pg_health() -> bool:
    """Check if database is reachable (PostgreSQL or SQLite fallback)."""
    conn = get_pg_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Health Check failed: {e}")
        return False
    finally:
        if conn:
            conn.close()
