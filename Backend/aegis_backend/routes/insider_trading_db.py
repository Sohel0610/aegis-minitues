import os
import logging
import threading
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import psycopg2.pool

load_dotenv()
logger = logging.getLogger(__name__)

# ── Connection Pool (reuse connections instead of opening new ones) ───
_pool = None
_pool_lock = threading.Lock()

def _get_pool():
    global _pool
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is not None:
            return _pool
        host     = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST')
        user     = os.getenv('DB_USER') or os.getenv('POSTGRES_USER')
        password = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD')
        database = os.getenv('DB_NAME')
        port     = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT') or '5432'

        if not all([host, user, password, database]):
            logger.error(f"Missing DB credentials: Host={bool(host)}, User={bool(user)}, DB={bool(database)}")
            return None

        db_config = {
            'host': host,
            'port': int(port),
            'database': database,
            'user': user,
            'password': password,
            'connect_timeout': 10
        }
        _sslmode = os.getenv('DB_SSLMODE') or os.getenv('POSTGRES_SSLMODE')
        if _sslmode:
            db_config['sslmode'] = _sslmode
        elif host and 'azure.com' in host.lower():
            db_config['sslmode'] = 'require'

        logger.info(f"Creating PG pool: Host={repr(host)}, DB={repr(database)}, SSL={db_config.get('sslmode')}")
        try:
            _pool = psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=8, **db_config)
            return _pool
        except Exception as e:
            logger.error(f"Failed to create PG pool: {e}")
            return None


def _get_connection():
    pool = _get_pool()
    if not pool:
        return None
    try:
        return pool.getconn()
    except Exception as e:
        logger.error(f"Pool getconn failed: {e}")
        return None


def _put_connection(conn):
    pool = _get_pool()
    if pool and conn:
        try:
            pool.putconn(conn)
        except Exception:
            pass


def _dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ── ID Resolution Cache (avoid repeated lookups for names→ids) ───────
_id_cache = {}
_id_cache_lock = threading.Lock()

def _resolve_id(conn, table, name_col, name_val):
    if not name_val:
        return None
    cache_key = f"{table}:{name_val.lower()}"
    with _id_cache_lock:
        if cache_key in _id_cache:
            return _id_cache[cache_key]
    cur = conn.cursor()
    cur.execute(f"SELECT id FROM {table} WHERE LOWER({name_col}) = LOWER(%s) LIMIT 1", (name_val,))
    row = cur.fetchone()
    resolved = row[0] if row else None
    with _id_cache_lock:
        _id_cache[cache_key] = resolved
    return resolved


# ── Filter Options (single connection, single round-trip) ────────────

def fetch_filter_options() -> Dict[str, Any]:
    conn = _get_connection()
    if not conn:
        return {"companies": [], "depositories": [], "batches": []}
    try:
        cur = _dict_cursor(conn)
        cur.execute("SELECT company_name FROM companies ORDER BY company_name")
        companies = [r['company_name'] for r in cur.fetchall()]

        cur.execute("SELECT type_name FROM depository_types ORDER BY type_name")
        depositories = [r['type_name'] for r in cur.fetchall()]

        cur.execute("""
            SELECT id, batch_name, older_date, latest_date, created_at
            FROM result_batches ORDER BY latest_date DESC, created_at DESC
        """)
        batches = []
        for r in cur.fetchall():
            d = dict(r)
            for k in ('older_date', 'latest_date', 'created_at'):
                if d.get(k):
                    d[k] = str(d[k])
            batches.append(d)

        return {"companies": companies, "depositories": depositories, "batches": batches}
    except Exception as e:
        logger.error(f"fetch_filter_options error: {e}")
        return {"companies": [], "depositories": [], "batches": []}
    finally:
        _put_connection(conn)


def fetch_companies() -> List[Dict[str, Any]]:
    conn = _get_connection()
    if not conn:
        return []
    try:
        cur = _dict_cursor(conn)
        cur.execute("SELECT id, company_name, created_at FROM companies ORDER BY company_name")
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"fetch_companies error: {e}")
        return []
    finally:
        _put_connection(conn)


def fetch_batches() -> List[Dict[str, Any]]:
    conn = _get_connection()
    if not conn:
        return []
    try:
        cur = _dict_cursor(conn)
        cur.execute("""
            SELECT id, batch_name, older_date, latest_date, created_at
            FROM result_batches ORDER BY latest_date DESC, created_at DESC
        """)
        results = []
        for r in cur.fetchall():
            d = dict(r)
            for k in ('older_date', 'latest_date', 'created_at'):
                if d.get(k):
                    d[k] = str(d[k])
            results.append(d)
        return results
    except Exception as e:
        logger.error(f"fetch_batches error: {e}")
        return []
    finally:
        _put_connection(conn)


def fetch_depository_types() -> List[Dict[str, Any]]:
    conn = _get_connection()
    if not conn:
        return []
    try:
        cur = _dict_cursor(conn)
        cur.execute("SELECT id, type_name FROM depository_types ORDER BY type_name")
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"fetch_depository_types error: {e}")
        return []
    finally:
        _put_connection(conn)


# ── Summary (uses pre-aggregated summary table) ──────────────────────

def fetch_summary(
    company_name: Optional[str] = None,
    batch_name: Optional[str] = None,
    depository_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    conn = _get_connection()
    if not conn:
        return []
    try:
        company_id = _resolve_id(conn, 'companies', 'company_name', company_name)
        batch_id = _resolve_id(conn, 'result_batches', 'batch_name', batch_name)
        depository_id = _resolve_id(conn, 'depository_types', 'type_name', depository_type)

        if company_name and not company_id:
            return []
        if batch_name and not batch_id:
            return []
        if depository_type and not depository_id:
            return []

        cur = _dict_cursor(conn)
        query = """
            SELECT
                s.id,
                c.company_name  AS company,
                rb.batch_name   AS batch,
                dt.type_name    AS depository,
                s.added_count   AS added,
                s.removed_count AS removed,
                s.changed_count AS changed,
                s.unchanged_count AS unchanged,
                s.total_count   AS total,
                s.empty_pangir_latest,
                s.empty_pangir_older
            FROM summary s
            JOIN companies        c  ON s.company_id    = c.id
            JOIN result_batches   rb ON s.batch_id      = rb.id
            JOIN depository_types dt ON s.depository_id  = dt.id
            WHERE 1=1
        """
        params: list = []
        if company_id:
            query += " AND s.company_id = %s"
            params.append(company_id)
        if batch_id:
            query += " AND s.batch_id = %s"
            params.append(batch_id)
        if depository_id:
            query += " AND s.depository_id = %s"
            params.append(depository_id)

        query += " ORDER BY rb.latest_date DESC, c.company_name, dt.type_name"
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"fetch_summary error: {e}")
        return []
    finally:
        _put_connection(conn)


# ── Record Counts (from summary table, not scanning shareholder_records) ─

def fetch_record_counts(
    company_name: Optional[str] = None,
    batch_name: Optional[str] = None,
    depository_type: Optional[str] = None,
) -> Dict[str, int]:
    conn = _get_connection()
    if not conn:
        return {"ADDED": 0, "REMOVED": 0, "CHANGED": 0, "UNCHANGED": 0, "TOTAL": 0}
    try:
        company_id = _resolve_id(conn, 'companies', 'company_name', company_name)
        batch_id = _resolve_id(conn, 'result_batches', 'batch_name', batch_name)
        depository_id = _resolve_id(conn, 'depository_types', 'type_name', depository_type)

        cur = _dict_cursor(conn)
        query = """
            SELECT
                COALESCE(SUM(added_count), 0)     AS added,
                COALESCE(SUM(removed_count), 0)   AS removed,
                COALESCE(SUM(changed_count), 0)    AS changed,
                COALESCE(SUM(unchanged_count), 0)  AS unchanged,
                COALESCE(SUM(total_count), 0)      AS total
            FROM summary
            WHERE 1=1
        """
        params: list = []
        if company_id:
            query += " AND company_id = %s"
            params.append(company_id)
        if batch_id:
            query += " AND batch_id = %s"
            params.append(batch_id)
        if depository_id:
            query += " AND depository_id = %s"
            params.append(depository_id)

        cur.execute(query, params)
        row = cur.fetchone()
        return {
            "ADDED": row['added'],
            "REMOVED": row['removed'],
            "CHANGED": row['changed'],
            "UNCHANGED": row['unchanged'],
            "TOTAL": row['total'],
        }
    except Exception as e:
        logger.error(f"fetch_record_counts error: {e}")
        return {"ADDED": 0, "REMOVED": 0, "CHANGED": 0, "UNCHANGED": 0, "TOTAL": 0}
    finally:
        _put_connection(conn)


# ── Records (cursor pagination + ID-based filtering) ─────────────────

def fetch_records(
    status: Optional[str] = None,
    company_name: Optional[str] = None,
    batch_name: Optional[str] = None,
    depository_type: Optional[str] = None,
    limit: int = 15,
    offset: int = 0,
    cursor: Optional[int] = None,
) -> Dict[str, Any]:
    conn = _get_connection()
    if not conn:
        return {"records": [], "total": 0, "limit": limit, "offset": offset, "next_cursor": None}
    try:
        company_id = _resolve_id(conn, 'companies', 'company_name', company_name)
        batch_id = _resolve_id(conn, 'result_batches', 'batch_name', batch_name)
        depository_id = _resolve_id(conn, 'depository_types', 'type_name', depository_type)

        cur = _dict_cursor(conn)
        where_parts = []
        params: list = []

        if status:
            where_parts.append("sr.status = UPPER(%s)")
            params.append(status)
        if company_id:
            where_parts.append("sr.company_id = %s")
            params.append(company_id)
        if batch_id:
            where_parts.append("sr.batch_id = %s")
            params.append(batch_id)
        if depository_id:
            where_parts.append("sr.depository_id = %s")
            params.append(depository_id)

        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

        # Get total from summary table when possible (much faster than COUNT(*))
        if batch_id and company_id and depository_id and not status:
            total_query = """
                SELECT COALESCE(total_count, 0) AS cnt FROM summary
                WHERE batch_id = %s AND company_id = %s AND depository_id = %s
            """
            cur.execute(total_query, [batch_id, company_id, depository_id])
            total_row = cur.fetchone()
            total = total_row['cnt'] if total_row else 0
        else:
            count_query = f"SELECT COUNT(*) AS cnt FROM shareholder_records sr{where_clause}"
            cur.execute(count_query, params)
            total = cur.fetchone()['cnt']

        # Cursor-based pagination (fast) or fallback to OFFSET
        select_cols = """
            sr.id,
            c.company_name  AS company,
            rb.batch_name   AS batch,
            dt.type_name    AS depository,
            sr.pangir,
            sr.name,
            sr.email,
            sr.position_latest,
            sr.position_older,
            sr.position_difference,
            sr.status
        """
        from_clause = """
            FROM shareholder_records sr
            JOIN companies        c  ON sr.company_id    = c.id
            JOIN result_batches   rb ON sr.batch_id      = rb.id
            JOIN depository_types dt ON sr.depository_id  = dt.id
        """

        if cursor is not None:
            cursor_where = where_parts + ["sr.id > %s"]
            cursor_params = params + [cursor]
            full_where = " WHERE " + " AND ".join(cursor_where) if cursor_where else ""
            select_query = f"SELECT {select_cols} {from_clause} {full_where} ORDER BY sr.id LIMIT %s"
            cur.execute(select_query, cursor_params + [limit])
        else:
            select_query = f"""
                SELECT {select_cols} {from_clause} {where_clause}
                ORDER BY sr.id
                LIMIT %s OFFSET %s
            """
            cur.execute(select_query, params + [limit, offset])

        records = [dict(r) for r in cur.fetchall()]
        next_cursor = records[-1]['id'] if records else None

        return {
            "records": records,
            "total": total,
            "limit": limit,
            "offset": offset,
            "next_cursor": next_cursor,
        }
    except Exception as e:
        logger.error(f"fetch_records error: {e}")
        return {"records": [], "total": 0, "limit": limit, "offset": offset, "next_cursor": None}
    finally:
        _put_connection(conn)
