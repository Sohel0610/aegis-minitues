import os
import logging
import threading
from typing import Optional, List, Dict, Any
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# ── ID Resolution Cache ──────────────────────────────────────────
_id_cache = {}
_id_cache_lock = threading.Lock()

def _resolve_id(conn, table, name_col, name_val):
    if not name_val:
        return None
    cache_key = f"{table}:{name_val.lower()}"
    with _id_cache_lock:
        if cache_key in _id_cache:
            return _id_cache[cache_key]
    with conn.cursor() as cur:
        cur.execute(f"SELECT id FROM {table} WHERE LOWER({name_col}) = LOWER(%s) LIMIT 1", (name_val,))
        row = cur.fetchone()
    resolved = row[0] if row else None
    with _id_cache_lock:
        _id_cache[cache_key] = resolved
    return resolved

# ── Function wrappers using unified connection from pgsql_service ────

def fetch_filter_options() -> Dict[str, Any]:
    with get_pg_connection(os.getenv('POSTGRES_DATABASE_INSIDER')) as conn:
        if not conn: return {"companies": [], "depositories": [], "batches": []}
        cur = get_pg_cursor(conn)
        cur.execute("SELECT company_name FROM companies ORDER BY company_name")
        companies = [r['company_name'] for r in cur.fetchall()]
        cur.execute("SELECT type_name FROM depository_types ORDER BY type_name")
        depositories = [r['type_name'] for r in cur.fetchall()]
        cur.execute("SELECT id, batch_name, older_date, latest_date FROM result_batches ORDER BY latest_date DESC")
        batches = [dict(r) for r in cur.fetchall()]
        # Convert date to string
        for b in batches:
             for k in ('older_date', 'latest_date'):
                 if b.get(k): b[k] = str(b[k])
        return {"companies": companies, "depositories": depositories, "batches": batches}

def fetch_companies() -> List[Dict[str, Any]]:
    with get_pg_connection(os.getenv('POSTGRES_DATABASE_INSIDER')) as conn:
        if not conn: return []
        cur = get_pg_cursor(conn)
        cur.execute("SELECT id, company_name FROM companies ORDER BY company_name")
        return [dict(r) for r in cur.fetchall()]

def fetch_batches() -> List[Dict[str, Any]]:
    with get_pg_connection(os.getenv('POSTGRES_DATABASE_INSIDER')) as conn:
        if not conn: return []
        cur = get_pg_cursor(conn)
        cur.execute("SELECT id, batch_name, older_date, latest_date FROM result_batches ORDER BY latest_date DESC")
        res = [dict(r) for r in cur.fetchall()]
        for r in res:
            for k in ('older_date', 'latest_date'):
                 if r.get(k): r[k] = str(r[k])
        return res

def fetch_depository_types() -> List[Dict[str, Any]]:
    with get_pg_connection(os.getenv('POSTGRES_DATABASE_INSIDER')) as conn:
        if not conn: return []
        cur = get_pg_cursor(conn)
        cur.execute("SELECT id, type_name FROM depository_types ORDER BY type_name")
        return [dict(r) for r in cur.fetchall()]

def fetch_summary(company_name=None, batch_name=None, depository_type=None) -> List[Dict[str, Any]]:
    with get_pg_connection(os.getenv('POSTGRES_DATABASE_INSIDER')) as conn:
        if not conn: return []
        c_id = _resolve_id(conn, 'companies', 'company_name', company_name)
        b_id = _resolve_id(conn, 'result_batches', 'batch_name', batch_name)
        d_id = _resolve_id(conn, 'depository_types', 'type_name', depository_type)
        cur = get_pg_cursor(conn)
        q = "SELECT s.id, c.company_name AS company, rb.batch_name AS batch, dt.type_name AS depository, added_count AS added, removed_count AS removed, changed_count AS changed, unchanged_count AS unchanged, total_count AS total FROM summary s JOIN companies c ON s.company_id = c.id JOIN result_batches rb ON s.batch_id = rb.id JOIN depository_types dt ON s.depository_id = dt.id WHERE 1=1"
        params = []
        if c_id: q += " AND s.company_id = %s"; params.append(c_id)
        if b_id: q += " AND s.batch_id = %s"; params.append(b_id)
        if d_id: q += " AND s.depository_id = %s"; params.append(d_id)
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]

def fetch_record_counts(company_name=None, batch_name=None, depository_type=None) -> Dict[str, int]:
    with get_pg_connection(os.getenv('POSTGRES_DATABASE_INSIDER')) as conn:
        if not conn: return {"TOTAL": 0}
        c_id = _resolve_id(conn, 'companies', 'company_name', company_name)
        b_id = _resolve_id(conn, 'result_batches', 'batch_name', batch_name)
        d_id = _resolve_id(conn, 'depository_types', 'type_name', depository_type)
        cur = get_pg_cursor(conn)
        q = "SELECT SUM(added_count) as added, SUM(removed_count) as removed, SUM(changed_count) as changed, SUM(unchanged_count) as unchanged, SUM(total_count) as total FROM summary WHERE 1=1"
        params = []
        if c_id: q += " AND company_id = %s"; params.append(c_id)
        if b_id: q += " AND batch_id = %s"; params.append(b_id)
        if d_id: q += " AND depository_id = %s"; params.append(d_id)
        cur.execute(q, params)
        r = cur.fetchone()
        return {"ADDED": r['added'] or 0, "REMOVED": r['removed'] or 0, "CHANGED": r['changed'] or 0, "UNCHANGED": r['unchanged'] or 0, "TOTAL": r['total'] or 0}

def fetch_records(status=None, company_name=None, batch_name=None, depository_type=None, search=None, limit=15, offset=0, cursor=None) -> Dict[str, Any]:
    with get_pg_connection(os.getenv('POSTGRES_DATABASE_INSIDER')) as conn:
        if not conn: return {"records": []}
        c_id = _resolve_id(conn, 'companies', 'company_name', company_name)
        b_id = _resolve_id(conn, 'result_batches', 'batch_name', batch_name)
        d_id = _resolve_id(conn, 'depository_types', 'type_name', depository_type)
        cur = get_pg_cursor(conn)
        where = []
        params = []
        if status: where.append("status = %s"); params.append(status.upper())
        if c_id: where.append("company_id = %s"); params.append(c_id)
        if b_id: where.append("batch_id = %s"); params.append(b_id)
        if d_id: where.append("depository_id = %s"); params.append(d_id)
        if search:
            search_prefix = f"{search.lower()}%"
            where.append("(lower(sr.name) LIKE %s OR lower(sr.email) LIKE %s OR lower(sr.pangir) LIKE %s)")
            params.extend([search_prefix, search_prefix, search_prefix])
        
        where_clause = (" WHERE " + " AND ".join(where)) if where else ""
        if search:
            # Full table scan when explicitly searching
            cur.execute(f"SELECT COUNT(*) as cnt FROM shareholder_records sr {where_clause}", params)
        else:
            # Cap at 200 to prevent massive latency and timeout on load
            cur.execute(f"SELECT COUNT(*) as cnt FROM (SELECT 1 FROM shareholder_records sr {where_clause} LIMIT 200) AS temp", params)
        total = cur.fetchone()['cnt']
        
        q = f"SELECT sr.id, c.company_name AS company, rb.batch_name AS batch, dt.type_name AS depository, sr.pangir, sr.name, sr.email, sr.position_latest, sr.position_older, sr.position_difference, sr.status FROM shareholder_records sr JOIN companies c ON sr.company_id = c.id JOIN result_batches rb ON sr.batch_id = rb.id JOIN depository_types dt ON sr.depository_id = dt.id {where_clause} ORDER BY sr.id LIMIT %s OFFSET %s"
        cur.execute(q, params + [limit, offset])
        records = [dict(r) for r in cur.fetchall()]
        return {"records": records, "total": total}

def pg_is_available() -> bool:
    import utils.pgsql_service as ps
    return ps.check_pg_health()
