from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

logger = logging.getLogger(__name__)
router = APIRouter()

# Resolve the path to servicenow_data.json (project root)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))                      # routes/
_BACKEND_APP_DIR = os.path.dirname(_THIS_DIR)                                # aegis_backend/
_BACKEND_DIR = os.path.dirname(_BACKEND_APP_DIR)                             # Backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)                                # AEGIS_Servicenow/
SN_JSON_PATH = os.path.join(_PROJECT_ROOT, "servicenow_data.json")

# Global connection pool
_db_pool = None

def get_conn():
    global _db_pool
    if _db_pool is None:
        db_host = os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or '192.168.0.56'
        db_port = os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5436'
        db_name = os.getenv('POSTGRES_DATABASE_INSIDER') or os.getenv('DB_NAME') or 'aegis_insider'
        db_user = os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'postgres'
        db_password = os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or 'postgres'
        
        _db_pool = pool.SimpleConnectionPool(
            1, 20,
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            cursor_factory=RealDictCursor
        )
    return _db_pool.getconn()

def release_conn(conn):
    global _db_pool
    if _db_pool and conn:
        _db_pool.putconn(conn)

# ── Response models ──
class ServiceNowSummaryResponse(BaseModel):
    total_declarations: int
    total_holdings: int
    total_preclearances: int
    unsanctioned_trades_count: int
    volume_breaches_count: int
    holding_discrepancies_count: int
    last_calculated: Optional[str] = None

# ── Endpoints ──

@router.get("/servicenow/summary", response_model=ServiceNowSummaryResponse)
async def get_servicenow_summary():
    """
    Read pre-calculated summary from the compliance_cache_summary table.
    This table is populated by running: python scripts/precalculate_compliance.py
    """
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Check if the cache table exists and has data
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'compliance_cache_summary'
            ) AS table_exists
        """)
        table_exists = cur.fetchone()['table_exists']

        if not table_exists:
            release_conn(conn)
            # Cache table not created yet — return zeros
            return {
                "total_declarations": 0,
                "total_holdings": 0,
                "total_preclearances": 0,
                "unsanctioned_trades_count": 0,
                "volume_breaches_count": 0,
                "holding_discrepancies_count": 0,
                "last_calculated": None,
            }

        cur.execute("""
            SELECT
                total_declarations,
                total_preclearances,
                last_run_at AS calculated_at
            FROM public.compliance_cache_summary
            ORDER BY last_run_at DESC
            LIMIT 1
        """)
        row = cur.fetchone()

        # Get violation counts dynamically using business logic filters
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE source_type = 'preclearance' AND declared_qty = 0 AND position_difference != 0) AS unsanctioned_cnt,
                COUNT(*) FILTER (WHERE source_type = 'preclearance' AND declared_qty > 0 AND ABS(position_difference) > declared_qty) AS volume_breach_cnt,
                COUNT(*) FILTER (WHERE source_type = 'declaration' AND declared_qty != shareholder_position) AS mismatch_cnt
            FROM public.compliance_cache_violations
        """)
        counts_row = cur.fetchone()

        # Get total holdings from the raw table since it's not in the summary schema
        cur.execute("SELECT COUNT(*) as cnt FROM public.servicenow_holdings")
        holdings_cnt = cur.fetchone()['cnt']
        
        release_conn(conn)

        if not row:
            return {
                "total_declarations": 0,
                "total_holdings": 0,
                "total_preclearances": 0,
                "unsanctioned_trades_count": 0,
                "volume_breaches_count": 0,
                "holding_discrepancies_count": 0,
                "last_calculated": None,
            }

        return {
            "total_declarations": row['total_declarations'],
            "total_holdings": holdings_cnt,
            "total_preclearances": row['total_preclearances'],
            "unsanctioned_trades_count": counts_row['unsanctioned_cnt'] if counts_row else 0,
            "volume_breaches_count": counts_row['volume_breach_cnt'] if counts_row else 0,
            "holding_discrepancies_count": counts_row['mismatch_cnt'] if counts_row else 0,
            "last_calculated": str(row['calculated_at']) if row['calculated_at'] else None,
        }
    except Exception as e:
        if 'conn' in locals():
            release_conn(conn)
        logger.error(f"Failed to fetch ServiceNow summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@router.get("/servicenow/violations")
async def get_servicenow_violations(
    type: str = Query("UNSANCTIONED"),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """
    Read pre-calculated violation details from compliance_cache_violations table.
    This table is populated by running: python scripts/precalculate_compliance.py
    """
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Check if the cache table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'compliance_cache_violations'
            ) AS table_exists
        """)
        table_exists = cur.fetchone()['table_exists']

        if not table_exists:
            release_conn(conn)
            return {"violations": [], "count": 0}

        req_type = type.upper()
        if req_type == 'UNSANCTIONED':
            where_clause = "source_type = 'preclearance' AND declared_qty = 0 AND position_difference != 0"
        elif req_type == 'VOLUME_BREACH':
            where_clause = "source_type = 'preclearance' AND declared_qty > 0 AND ABS(position_difference) > declared_qty"
        elif req_type == 'HOLDING_MISMATCH':
            where_clause = "source_type = 'declaration' AND declared_qty != shareholder_position"
        else:
            where_clause = "1 = 0"

        # Count total for this violation type
        cur.execute(f"""
            SELECT count(*) as cnt
            FROM public.compliance_cache_violations
            WHERE {where_clause}
        """)
        total = cur.fetchone()['cnt']

        # Fetch paginated rows
        cur.execute(f"""
            SELECT
                %s AS violation_type,
                shareholder_name,
                pan_card AS pan,
                shareholder_company AS company_name,
                declared_name AS employee_name,
                NULL AS employee_email,
                position_difference AS shares_traded,
                declared_qty AS approved_volume,
                ABS(position_difference) - declared_qty AS excess_volume,
                declared_qty AS declared_quantity,
                shareholder_position AS depository_quantity,
                position_difference AS difference,
                source_ritm AS ritm_number,
                batch_name,
                NULL AS transaction_date,
                relationship,
                NULL AS phase,
                NULL AS fiscal_year
            FROM public.compliance_cache_violations
            WHERE {where_clause}
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (req_type, limit, offset))

        rows = cur.fetchall()
        release_conn(conn)

        violations = []
        for r in rows:
            v = {}
            # Map all non-None fields
            for key in ['shareholder_name', 'pan', 'company_name', 'employee_name',
                        'employee_email', 'shares_traded', 'approved_volume',
                        'excess_volume', 'declared_quantity', 'depository_quantity',
                        'difference', 'ritm_number', 'batch_name', 'transaction_date',
                        'relationship', 'phase', 'fiscal_year']:
                if r.get(key) is not None:
                    v[key] = r[key]

            # For HOLDING_MISMATCH, map shareholder_name → declarant_name for frontend compatibility
            if type.upper() == 'HOLDING_MISMATCH':
                v['declarant_name'] = v.pop('shareholder_name', None)

            violations.append(v)

        return {"violations": violations, "count": total}
    except Exception as e:
        if 'conn' in locals():
            release_conn(conn)
        logger.error(f"Failed to fetch ServiceNow violations: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@router.get("/servicenow/all-records")
async def get_servicenow_all_records(
    search: str = Query(None),
    limit: int = Query(15),
    offset: int = Query(0)
):
    """
    Fetch all records from compliance_cache_violations (both compliant and violated).
    """
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Check if the cache table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'compliance_cache_violations'
            ) AS table_exists
        """)
        table_exists = cur.fetchone()['table_exists']

        if not table_exists:
            release_conn(conn)
            return {"records": [], "count": 0}

        where_clause = "1=1"
        params = []

        if search:
            search_pattern = f"%{search}%"
            where_clause += " AND (pan_card ILIKE %s OR declared_name ILIKE %s OR shareholder_name ILIKE %s)"
            params.extend([search_pattern, search_pattern, search_pattern])

        # Count total
        cur.execute(f"SELECT count(*) as cnt FROM public.compliance_cache_violations WHERE {where_clause}", params)
        total = cur.fetchone()['cnt']

        # Fetch paginated rows
        q = f"""
            SELECT
                id,
                pan_card,
                declared_name,
                relationship,
                source_type,
                source_ritm,
                declared_qty,
                shareholder_name,
                shareholder_company,
                shareholder_position,
                position_difference,
                batch_name,
                detected_at,
                CASE
                    WHEN source_type = 'preclearance' AND declared_qty = 0 AND position_difference != 0 THEN 'UNSANCTIONED'
                    WHEN source_type = 'preclearance' AND declared_qty > 0 AND ABS(position_difference) > declared_qty THEN 'VOLUME_BREACH'
                    WHEN source_type = 'declaration' AND declared_qty != shareholder_position THEN 'HOLDING_MISMATCH'
                    ELSE 'COMPLIANT'
                END AS computed_status
            FROM public.compliance_cache_violations
            WHERE {where_clause}
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        cur.execute(q, params + [limit, offset])
        rows = [dict(r) for r in cur.fetchall()]
        release_conn(conn)

        return {"records": rows, "count": total}
    except Exception as e:
        if 'conn' in locals():
            release_conn(conn)
        logger.error(f"Failed to fetch all ServiceNow records: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
