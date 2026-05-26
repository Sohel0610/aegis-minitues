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

@router.get("/servicenow/ledger")
async def get_servicenow_ledger(
    search: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """
    Get a aggregated list of all unique employees who have ServiceNow compliance submissions.
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Base query to get aggregated employee compliance history
        query = """
            WITH decls AS (
                SELECT 
                    email, 
                    MAX(requested_for) as name, 
                    MAX(employee_code) as code, 
                    MAX(designation) as designation,
                    COUNT(*) as decl_count
                FROM public.servicenow_declarations
                GROUP BY email
            ),
            preclears AS (
                SELECT 
                    email, 
                    MAX(requested_for) as name, 
                    MAX(employee_code) as code, 
                    MAX(designation) as designation,
                    COUNT(*) as pc_count
                FROM public.servicenow_preclearances
                GROUP BY email
            )
            SELECT 
                COALESCE(d.email, p.email) as email,
                COALESCE(d.name, p.name) as name,
                COALESCE(d.code, p.code) as employee_code,
                COALESCE(d.designation, p.designation) as designation,
                COALESCE(d.decl_count, 0) as declarations_count,
                COALESCE(p.pc_count, 0) as preclearances_count
            FROM decls d
            FULL OUTER JOIN preclears p ON d.email = p.email
        """
        
        params = []
        if search:
            query += """ WHERE 
                d.name ILIKE %s OR p.name ILIKE %s OR 
                d.email ILIKE %s OR p.email ILIKE %s OR 
                d.code ILIKE %s OR p.code ILIKE %s OR
                EXISTS (
                    SELECT 1 FROM public.servicenow_declarations sd
                    JOIN public.servicenow_holdings sh ON sd.id = sh.declaration_id
                    WHERE sd.email = COALESCE(d.email, p.email) AND sh.pan_card ILIKE %s
                ) OR
                EXISTS (
                    SELECT 1 FROM public.servicenow_preclearances sp
                    JOIN public.servicenow_preclearance_details spd ON sp.id = spd.preclearance_id
                    WHERE sp.email = COALESCE(d.email, p.email) AND spd.pan_card ILIKE %s
                )
            """
            search_param = f"%{search}%"
            params.extend([search_param] * 8)
            
        # Get total count of matching employees
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS temp"
        cur.execute(count_query, params)
        total = cur.fetchone()['count']
        
        # Paginate results
        query += " ORDER BY name ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        rows = cur.fetchall()
        release_conn(conn)
        
        return {"employees": rows, "count": total}
    except Exception as e:
        if 'conn' in locals():
            release_conn(conn)
        logger.error(f"Failed to fetch compliance ledger: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@router.get("/servicenow/ledger/details")
async def get_servicenow_ledger_details(email: str = Query(...)):
    """
    Get detailed timeline of all ServiceNow declarations and preclearances for a specific employee.
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        email_clean = email.strip().lower()
        
        # 1. Fetch Declarations
        cur.execute("""
            SELECT id, ritm_number, declaration_date, NULL as phase, fiscal_year, state
            FROM public.servicenow_declarations
            WHERE email ILIKE %s
            ORDER BY declaration_date DESC, ritm_number DESC
        """, (email_clean,))
        decls = cur.fetchall()
        
        declarations_detailed = []
        for d in decls:
            cur.execute("""
                SELECT name, relationship, pan_card, 
                       aesl_qty, ael_qty, apl_qty, agel_qty, atgl_qty, apsezl_qty, 
                       acc_qty, acl_qty, ndtv_qty, sanghi_qty, ocl_qty, itd_qty, psp_qty
                FROM public.servicenow_holdings
                WHERE declaration_id = %s
            """, (d['id'],))
            holdings = cur.fetchall()
            
            holdings_list = []
            for h in holdings:
                companies = [
                    ('AESL', h['aesl_qty']), ('AEL', h['ael_qty']), ('APL', h['apl_qty']),
                    ('AGEL', h['agel_qty']), ('ATGL', h['atgl_qty']), ('APSEZL', h['apsezl_qty']),
                    ('ACC', h['acc_qty']), ('ACL / Ambuja', h['acl_qty']), ('NDTV', h['ndtv_qty']),
                    ('Sanghi', h['sanghi_qty']), ('OCL', h['ocl_qty']), ('ITD', h['itd_qty']),
                    ('PSP', h['psp_qty'])
                ]
                has_any_holdings = False
                for comp_name, qty in companies:
                    # In some cases the db might store qty as string or None, handle gracefully
                    try:
                        q_val = float(qty) if qty is not None else 0
                    except:
                        q_val = 0
                    if q_val > 0:
                        has_any_holdings = True
                        holdings_list.append({
                            "name": h['name'],
                            "relationship": h['relationship'],
                            "pan_card": h['pan_card'],
                            "company_name": comp_name,
                            "declared_quantity": int(q_val)
                        })
                
                # If family member has 0 holdings for all companies, still include them in the UI
                if not has_any_holdings:
                    holdings_list.append({
                        "name": h['name'],
                        "relationship": h['relationship'],
                        "pan_card": h['pan_card'],
                        "company_name": "-",
                        "declared_quantity": 0
                    })
                
            declarations_detailed.append({
                "ritm_number": d['ritm_number'],
                "declaration_date": str(d['declaration_date']) if d['declaration_date'] else None,
                "phase": d['phase'],
                "fiscal_year": d['fiscal_year'],
                "state": d['state'],
                "holdings": holdings_list
            })
            
        # 2. Fetch Preclearances
        cur.execute("""
            SELECT id, ritm_number, declaration_phase as phase, fiscal_year, state
            FROM public.servicenow_preclearances
            WHERE email ILIKE %s
            ORDER BY ritm_number DESC
        """, (email_clean,))
        pcs = cur.fetchall()
        
        preclearances_detailed = []
        for pc in pcs:
            cur.execute("""
                SELECT name, relationship, pan_card, quantity as approved_quantity
                FROM public.servicenow_preclearance_details
                WHERE preclearance_id = %s
            """, (pc['id'],))
            details = cur.fetchall()
            
            details_list = []
            for det in details:
                details_list.append({
                    "name": det['name'],
                    "relationship": det['relationship'],
                    "pan_card": det['pan_card'],
                    "approved_quantity": det['approved_quantity']
                })
                
            preclearances_detailed.append({
                "ritm_number": pc['ritm_number'],
                "phase": pc['phase'],
                "fiscal_year": pc['fiscal_year'],
                "state": pc['state'],
                "details": details_list
            })
            
        release_conn(conn)
        
        return {
            "email": email_clean,
            "declarations": declarations_detailed,
            "preclearances": preclearances_detailed
        }
    except Exception as e:
        if 'conn' in locals():
            release_conn(conn)
        logger.error(f"Failed to fetch employee details for {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@router.get("/servicenow/raw-feed")
async def get_servicenow_raw_feed(
    search: Optional[str] = Query(None),
    type: str = Query("ALL"),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """
    Get a flat chronological feed of all ServiceNow tickets (declarations and preclearances).
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Build queries based on type filter
        queries = []
        
        dec_query = """
            SELECT 
                'Declaration' as ticket_type,
                ritm_number,
                requested_for as name,
                email,
                employee_code,
                designation,
                state,
                fiscal_year,
                NULL as phase,
                declaration_date::text as date
            FROM public.servicenow_declarations
        """
        
        pc_query = """
            SELECT 
                'Pre-clearance' as ticket_type,
                ritm_number,
                requested_for as name,
                email,
                employee_code,
                designation,
                state,
                fiscal_year,
                declaration_phase as phase,
                NULL as date
            FROM public.servicenow_preclearances
        """
        
        if type.upper() == "DECLARATION":
            queries.append(dec_query)
        elif type.upper() == "PRECLEARANCE":
            queries.append(pc_query)
        else:
            queries.extend([dec_query, pc_query])
            
        combined_query = " UNION ALL ".join(queries)
        
        params = []
        final_query = f"SELECT * FROM ({combined_query}) AS raw_feed"
        
        if search:
            final_query += """ WHERE 
                ritm_number ILIKE %s OR 
                name ILIKE %s OR 
                email ILIKE %s OR 
                employee_code ILIKE %s OR 
                designation ILIKE %s OR 
                state ILIKE %s
            """
            search_param = f"%{search}%"
            params.extend([search_param] * 6)
            
        # Get count
        count_query = f"SELECT COUNT(*) as count FROM ({final_query}) AS temp"
        cur.execute(count_query, params)
        total = cur.fetchone()['count']
        
        # Add order and pagination (RITM number sorting gives chronological order)
        final_query += " ORDER BY ritm_number DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(final_query, params)
        rows = cur.fetchall()
        release_conn(conn)
        
        return {"tickets": rows, "count": total}
    except Exception as e:
        if 'conn' in locals():
            release_conn(conn)
        logger.error(f"Failed to fetch ServiceNow raw feed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@router.get("/servicenow/ticket/details")
async def get_servicenow_ticket_details(ritm: str = Query(...)):
    """
    Get detailed holdings or preclearance details for a single RITM ticket.
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        ritm_clean = ritm.strip().upper()
        
        # Check if it's a declaration
        cur.execute("SELECT * FROM public.servicenow_declarations WHERE ritm_number = %s", (ritm_clean,))
        decl = cur.fetchone()
        
        if decl:
            company_names = {
                1: 'AESL',
                2: 'AEL',
                3: 'AGEL',
                4: 'APSEZL',
                5: 'ACL / Ambuja',
                6: 'Sanghi'
            }
            cur.execute("""
                SELECT name, relationship, pan_card, company_id, declared_quantity
                FROM public.servicenow_holdings
                WHERE ritm_number = %s
            """, (ritm_clean,))
            holdings = cur.fetchall()
            
            holdings_list = []
            for h in holdings:
                holdings_list.append({
                    "name": h['name'],
                    "relationship": h['relationship'],
                    "pan_card": h['pan_card'],
                    "company_name": company_names.get(h['company_id'], f"Company {h['company_id']}"),
                    "declared_quantity": h['declared_quantity']
                })
            release_conn(conn)
            return {"type": "Declaration", "ritm": ritm_clean, "details": holdings_list}
            
        # Check if it's a preclearance
        cur.execute("SELECT * FROM public.servicenow_preclearances WHERE ritm_number = %s", (ritm_clean,))
        pc = cur.fetchone()
        
        if pc:
            cur.execute("""
                SELECT name, relationship, pan_card, approved_quantity
                FROM public.servicenow_preclearance_details
                WHERE ritm_number = %s
            """, (ritm_clean,))
            details = cur.fetchall()
            
            details_list = []
            for det in details:
                details_list.append({
                    "name": det['name'],
                    "relationship": det['relationship'],
                    "pan_card": det['pan_card'],
                    "approved_quantity": det['approved_quantity']
                })
            release_conn(conn)
            return {"type": "Pre-clearance", "ritm": ritm_clean, "details": details_list}
            
        release_conn(conn)
        raise HTTPException(status_code=404, detail="Ticket not found")
    except Exception as e:
        if 'conn' in locals():
            release_conn(conn)
        logger.error(f"Failed to fetch ticket details for {ritm}: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")



