from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from routes.servicenow_ingestion import run_ingestion

logger = logging.getLogger(__name__)
router = APIRouter()

# Resolve the path to servicenow_data.json (project root)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))                      # routes/
_BACKEND_APP_DIR = os.path.dirname(_THIS_DIR)                                # aegis_backend/
_BACKEND_DIR = os.path.dirname(_BACKEND_APP_DIR)                             # Backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)                                # AEGIS_Servicenow/
SN_JSON_PATH = os.path.join(_PROJECT_ROOT, "servicenow_data.json")

def get_conn():
    db_host = os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or '192.168.0.56'
    db_port = os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5436'
    db_name = os.getenv('POSTGRES_DATABASE_INSIDER') or os.getenv('DB_NAME') or 'aegis_insider'
    db_user = os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'postgres'
    db_password = os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or 'postgres'
    
    return psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password,
        cursor_factory=RealDictCursor
    )

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

@router.post("/servicenow/sync")
async def sync_servicenow_data():
    """
    Full sync pipeline:
      Step 1 - Call the ServiceNow API (servicenow.py) to fetch latest RITM records.
      Step 2 - Merge new records into servicenow_data.json (deduplicated by RITM number).
      Step 3 - Run the DB ingestion engine to normalize and load fresh data.
    Returns a detailed status for each step.
    """
    steps = []
    api_fetched = False
    new_records = 0

    # ── Step 1: Fetch from ServiceNow API ──
    try:
        from servicenow import fetch_ritms_yesterday
        logger.info("Calling ServiceNow API to fetch latest RITM records...")
        api_response = fetch_ritms_yesterday(verify_cert=False, timeout=20)

        status_code = api_response.get("status", 0)
        has_data = api_response.get("has_data", False)

        if not has_data:
            msg = api_response.get("message", "API returned no new data.")
            steps.append({"step": "fetch_api", "status": "skipped", "detail": msg})
            logger.warning(f"ServiceNow API: {msg}")
        else:
            # ── Step 2: Merge into JSON file ──
            try:
                raw_result = api_response.get("result", {})

                # Normalise: ServiceNow API returns {"result": [...]} so
                # raw_result may be a dict like {"result": [...]} or already a list.
                if isinstance(raw_result, list):
                    incoming_items = raw_result
                elif isinstance(raw_result, dict):
                    inner = raw_result.get("result", [])
                    if isinstance(inner, list):
                        incoming_items = inner
                    elif isinstance(inner, dict):
                        incoming_items = inner.get("result", [])
                    else:
                        incoming_items = []
                else:
                    incoming_items = []

                # Load existing JSON — create the file if it doesn't exist yet
                if os.path.exists(SN_JSON_PATH):
                    with open(SN_JSON_PATH, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    existing_items = existing_data.get("result", {}).get("result", [])
                    if not isinstance(existing_items, list):
                        existing_items = []
                else:
                    logger.info(f"servicenow_data.json not found — creating at {SN_JSON_PATH}")
                    existing_data = {"result": {"result": []}}
                    existing_items = []

                # Deduplicate by RITM number — new records overwrite old ones
                existing_map = {item["number"]: item for item in existing_items if "number" in item}
                for item in incoming_items:
                    ritm = item.get("number")
                    if ritm and ritm not in existing_map:
                        new_records += 1
                    if ritm:
                        existing_map[ritm] = item

                merged_items = list(existing_map.values())
                existing_data["result"]["result"] = merged_items

                os.makedirs(os.path.dirname(SN_JSON_PATH), exist_ok=True)
                with open(SN_JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=4, ensure_ascii=False)

                api_fetched = True
                steps.append({
                    "step": "fetch_api",
                    "status": "success",
                    "detail": f"Fetched {len(incoming_items)} records from ServiceNow API. {new_records} new. JSON saved ({len(merged_items)} total)."
                })
                logger.info(f"ServiceNow JSON updated: {len(merged_items)} total ({new_records} new).")

            except Exception as merge_err:
                steps.append({"step": "save_json", "status": "error", "detail": str(merge_err)})
                logger.error(f"Failed to merge/save ServiceNow JSON: {merge_err}")

    except Exception as api_err:
        steps.append({
            "step": "fetch_api",
            "status": "error",
            "detail": f"Could not reach ServiceNow API: {api_err}. Will use existing JSON data."
        })
        logger.warning(f"ServiceNow API call failed: {api_err}. Falling back to existing JSON.")

    # ── Step 3: Ingest into DB ──
    try:
        logger.info("Running DB ingestion from servicenow_data.json...")
        success = run_ingestion()
        if success:
            steps.append({
                "step": "db_ingestion",
                "status": "success",
                "detail": "Database updated. All compliance checks refreshed."
            })
        else:
            steps.append({"step": "db_ingestion", "status": "error", "detail": "Ingestion engine reported failure."})
            raise HTTPException(status_code=500, detail="DB ingestion failed.")
    except HTTPException:
        raise
    except Exception as ingest_err:
        steps.append({"step": "db_ingestion", "status": "error", "detail": str(ingest_err)})
        raise HTTPException(status_code=500, detail=f"DB ingestion error: {ingest_err}")

    return {
        "message": "ServiceNow sync completed.",
        "api_fetched": api_fetched,
        "new_records_from_api": new_records,
        "steps": steps
    }

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
            conn.close()
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
                total_holdings,
                total_preclearances,
                unsanctioned_count,
                volume_breach_count,
                holding_mismatch_count,
                calculated_at
            FROM public.compliance_cache_summary
            ORDER BY calculated_at DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        conn.close()

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
            "total_holdings": row['total_holdings'],
            "total_preclearances": row['total_preclearances'],
            "unsanctioned_trades_count": row['unsanctioned_count'],
            "volume_breaches_count": row['volume_breach_count'],
            "holding_discrepancies_count": row['holding_mismatch_count'],
            "last_calculated": str(row['calculated_at']) if row['calculated_at'] else None,
        }
    except Exception as e:
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
            conn.close()
            return {"violations": [], "count": 0}

        # Count total for this violation type
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM public.compliance_cache_violations
            WHERE violation_type = %s
        """, (type.upper(),))
        total = cur.fetchone()['cnt']

        # Fetch paginated rows
        cur.execute("""
            SELECT
                violation_type, shareholder_name, pan, company_name,
                employee_name, employee_email, shares_traded,
                approved_volume, excess_volume,
                declared_quantity, depository_quantity, difference,
                ritm_number, batch_name, transaction_date,
                relationship, phase, fiscal_year
            FROM public.compliance_cache_violations
            WHERE violation_type = %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (type.upper(), limit, offset))

        rows = cur.fetchall()
        conn.close()

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
        logger.error(f"Failed to fetch ServiceNow violations: {e}")
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
            query += " WHERE d.name ILIKE %s OR p.name ILIKE %s OR d.email ILIKE %s OR p.email ILIKE %s OR d.code ILIKE %s OR p.code ILIKE %s"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param, search_param, search_param])
            
        # Get total count of matching employees
        count_query = f"SELECT COUNT(*) as count FROM ({query}) AS temp"
        cur.execute(count_query, params)
        total = cur.fetchone()['count']
        
        # Paginate results
        query += " ORDER BY name ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        
        return {"employees": rows, "count": total}
    except Exception as e:
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
            SELECT ritm_number, declaration_date, phase, fiscal_year, state
            FROM public.servicenow_declarations
            WHERE email = %s
            ORDER BY declaration_date DESC, ritm_number DESC
        """, (email_clean,))
        decls = cur.fetchall()
        
        # Fetch holdings for each declaration RITM
        company_names = {
            1: 'AESL',
            2: 'AEL',
            3: 'AGEL',
            4: 'APSEZL',
            5: 'ACL / Ambuja',
            6: 'Sanghi'
        }
        
        declarations_detailed = []
        for d in decls:
            ritm = d['ritm_number']
            cur.execute("""
                SELECT name, relationship, pan_card, company_id, declared_quantity
                FROM public.servicenow_holdings
                WHERE ritm_number = %s
            """, (ritm,))
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
            SELECT ritm_number, phase, fiscal_year, state
            FROM public.servicenow_preclearances
            WHERE email = %s
            ORDER BY ritm_number DESC
        """, (email_clean,))
        pcs = cur.fetchall()
        
        preclearances_detailed = []
        for pc in pcs:
            ritm = pc['ritm_number']
            cur.execute("""
                SELECT name, relationship, pan_card, approved_quantity
                FROM public.servicenow_preclearance_details
                WHERE ritm_number = %s
            """, (ritm,))
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
            
        conn.close()
        
        return {
            "email": email_clean,
            "declarations": declarations_detailed,
            "preclearances": preclearances_detailed
        }
    except Exception as e:
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
                phase,
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
                phase,
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
        conn.close()
        
        return {"tickets": rows, "count": total}
    except Exception as e:
        logger.error(f"Failed to fetch ServiceNow raw feed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")


