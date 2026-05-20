from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import json
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from routes.servicenow_ingestion import run_ingestion

logger = logging.getLogger(__name__)
router = APIRouter()

# Load .env explicitly so DB_* vars are available when this module is imported
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

# Resolve the path to servicenow_data.json (project root)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))                      # routes/
_BACKEND_APP_DIR = os.path.dirname(_THIS_DIR)                                # aegis_backend/
_BACKEND_DIR = os.path.dirname(_BACKEND_APP_DIR)                             # Backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)                                # AEGIS_Servicenow/
SN_JSON_PATH = os.path.join(_PROJECT_ROOT, "servicenow_data.json")

# ── Dedicated local connection pool for aegis_insider (uses DB_* vars, not POSTGRES_*) ──
_sn_pool: psycopg2.pool.ThreadedConnectionPool | None = None

def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _sn_pool
    if _sn_pool is None:
        _sn_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=os.getenv('DB_HOST', '192.168.0.56'),
            port=int(os.getenv('DB_PORT', '5436')),
            dbname=os.getenv('DB_NAME', 'aegis_insider'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            sslmode=os.getenv('DB_SSLMODE', 'disable'),
            connect_timeout=10,
        )
        logger.info(f"ServiceNow pool initialized: {os.getenv('DB_NAME','aegis_insider')} @ {os.getenv('DB_HOST','192.168.0.56')}:{os.getenv('DB_PORT','5436')}")
    return _sn_pool

def get_conn():
    """Get a pooled connection to aegis_insider (local DB_* credentials)."""
    try:
        conn = _get_pool().getconn()
        conn.cursor_factory = RealDictCursor
        return conn
    except Exception as e:
        logger.error(f"ServiceNow pool error: {e}")
        raise HTTPException(status_code=503, detail="aegis_insider database unavailable")

def _return_conn(conn):
    """Return a connection back to the pool."""
    try:
        _get_pool().putconn(conn)
    except Exception:
        pass

# ── Response models ──
class ServiceNowSummaryResponse(BaseModel):
    total_declarations: int
    total_holdings: int
    total_preclearances: int
    unsanctioned_trades_count: int
    volume_breaches_count: int
    holding_discrepancies_count: int

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
    """Get high level metrics on declarations, tickets, and detected violations"""
    try:
        conn = None
        conn = get_conn()
        cur = conn.cursor()

        # Count master declarations
        cur.execute("SELECT COUNT(*) FROM public.servicenow_declarations")
        total_dec = cur.fetchone()['count']

        # Count holdings
        cur.execute("SELECT COUNT(*) FROM public.servicenow_holdings")
        total_hold = cur.fetchone()['count']

        # Count pre-clearances
        cur.execute("SELECT COUNT(*) FROM public.servicenow_preclearances")
        total_pc = cur.fetchone()['count']

        # Count Unsanctioned Trades (insider trades without pre-clearance)
        cur.execute("""
            SELECT COUNT(DISTINCT (sr.pangir, sr.company_id, sr.batch_id)) AS count
            FROM public.shareholder_records sr
            JOIN (
                SELECT DISTINCT pan_card FROM public.servicenow_holdings WHERE pan_card != ''
                UNION
                SELECT DISTINCT pan_card FROM public.servicenow_preclearance_details WHERE pan_card != ''
            ) dp ON sr.pangir = dp.pan_card
            LEFT JOIN public.servicenow_preclearance_details pd ON sr.pangir = pd.pan_card
            LEFT JOIN public.servicenow_preclearances pc ON pd.ritm_number = pc.ritm_number AND pc.state = 'Closed Complete'
            WHERE 
                sr.position_difference != 0
                AND pc.ritm_number IS NULL
        """)
        unsanctioned_count = cur.fetchone()['count'] or 0

        # Count Volume Breaches (Over-trading)
        cur.execute("""
            SELECT COUNT(DISTINCT (sr.pangir, sr.company_id, sr.batch_id)) AS count
            FROM public.shareholder_records sr
            JOIN public.servicenow_preclearance_details pd ON sr.pangir = pd.pan_card
            JOIN public.servicenow_preclearances pc ON pd.ritm_number = pc.ritm_number
            WHERE 
                sr.position_difference != 0
                AND pc.state = 'Closed Complete'
                AND ABS(sr.position_difference) > pd.approved_quantity
        """)
        volume_breach_count = cur.fetchone()['count'] or 0

        # Count Holding Discrepancies — use DISTINCT ON to take only the latest batch per PAN+company
        cur.execute("""
            WITH latest_sr AS (
                SELECT DISTINCT ON (pangir, company_id)
                    pangir, company_id, position_latest
                FROM public.shareholder_records
                ORDER BY pangir, company_id, batch_id DESC
            )
            SELECT COUNT(*) AS count
            FROM public.servicenow_holdings sh
            JOIN public.servicenow_declarations sd ON sh.ritm_number = sd.ritm_number
            JOIN latest_sr sr ON sh.pan_card = sr.pangir AND sh.company_id = sr.company_id
            WHERE 
                sd.state = 'Closed Complete'
                AND sh.declared_quantity != sr.position_latest
        """)
        holding_discrepancy_count = cur.fetchone()['count'] or 0

        return {
            "total_declarations": total_dec,
            "total_holdings": total_hold,
            "total_preclearances": total_pc,
            "unsanctioned_trades_count": unsanctioned_count,
            "volume_breaches_count": volume_breach_count,
            "holding_discrepancies_count": holding_discrepancy_count
        }
    except Exception as e:
        logger.error(f"Failed to fetch ServiceNow summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn:
            _return_conn(conn)

@router.get("/servicenow/violations")
async def get_servicenow_violations(
    type: str = Query("UNSANCTIONED"),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """Fetch list of detected violations of a specific category"""
    try:
        conn = None
        conn = get_conn()
        cur = conn.cursor()
        violations = []

        if type.upper() == "UNSANCTIONED":
            cur.execute("""
                WITH latest_sr AS (
                    SELECT DISTINCT ON (pangir, company_id)
                        pangir, company_id, position_difference, name, email, batch_id
                    FROM public.shareholder_records
                    ORDER BY pangir, company_id, batch_id DESC
                ),
                latest_rb AS (
                    SELECT DISTINCT ON (sr.pangir, sr.company_id)
                        sr.pangir, sr.company_id, rb.batch_name, rb.latest_date
                    FROM public.shareholder_records sr
                    JOIN public.result_batches rb ON sr.batch_id = rb.id
                    ORDER BY sr.pangir, sr.company_id, sr.batch_id DESC
                )
                SELECT 
                    lsr.name AS shareholder_name,
                    lsr.pangir AS pan,
                    c.company_name,
                    lsr.position_difference AS shares_traded,
                    lrb.batch_name,
                    lrb.latest_date AS transaction_date,
                    COALESCE(
                        (SELECT requested_for FROM public.servicenow_declarations WHERE email = lsr.email LIMIT 1),
                        (SELECT requested_for FROM public.servicenow_preclearances WHERE email = lsr.email LIMIT 1),
                        'Insider Employee'
                    ) AS employee_name,
                    lsr.email AS employee_email
                FROM latest_sr lsr
                JOIN public.companies c ON lsr.company_id = c.id
                JOIN latest_rb lrb ON lsr.pangir = lrb.pangir AND lsr.company_id = lrb.company_id
                JOIN (
                    SELECT DISTINCT pan_card FROM public.servicenow_holdings WHERE pan_card != ''
                    UNION
                    SELECT DISTINCT pan_card FROM public.servicenow_preclearance_details WHERE pan_card != ''
                ) dp ON lsr.pangir = dp.pan_card
                LEFT JOIN public.servicenow_preclearance_details pd ON lsr.pangir = pd.pan_card
                LEFT JOIN public.servicenow_preclearances pc ON pd.ritm_number = pc.ritm_number AND pc.state = 'Closed Complete'
                WHERE 
                    lsr.position_difference != 0
                    AND pc.ritm_number IS NULL
                ORDER BY lrb.latest_date DESC, lsr.name
                LIMIT %s OFFSET %s
            """, (limit, offset))
            rows = cur.fetchall()
            for r in rows:
                violations.append({
                    "shareholder_name": r['shareholder_name'],
                    "pan": r['pan'],
                    "company_name": r['company_name'],
                    "shares_traded": r['shares_traded'],
                    "batch_name": r['batch_name'],
                    "transaction_date": str(r['transaction_date']) if r['transaction_date'] else None,
                    "employee_name": r['employee_name'],
                    "employee_email": r['employee_email']
                })

        elif type.upper() == "VOLUME_BREACH":
            cur.execute("""
                WITH latest_sr AS (
                    SELECT DISTINCT ON (pangir, company_id)
                        pangir, company_id, position_difference, name, email, batch_id
                    FROM public.shareholder_records
                    ORDER BY pangir, company_id, batch_id DESC
                ),
                latest_rb AS (
                    SELECT DISTINCT ON (sr.pangir, sr.company_id)
                        sr.pangir, sr.company_id, rb.batch_name, rb.latest_date
                    FROM public.shareholder_records sr
                    JOIN public.result_batches rb ON sr.batch_id = rb.id
                    ORDER BY sr.pangir, sr.company_id, sr.batch_id DESC
                )
                SELECT 
                    lsr.name AS shareholder_name,
                    lsr.pangir AS pan,
                    c.company_name,
                    lsr.position_difference AS shares_traded,
                    pd.approved_quantity AS approved_volume,
                    (ABS(lsr.position_difference) - pd.approved_quantity) AS excess_volume,
                    lrb.batch_name,
                    lrb.latest_date AS transaction_date,
                    pc.requested_for AS employee_name,
                    pc.email AS employee_email,
                    pc.ritm_number AS preclearance_ritm
                FROM latest_sr lsr
                JOIN public.companies c ON lsr.company_id = c.id
                JOIN latest_rb lrb ON lsr.pangir = lrb.pangir AND lsr.company_id = lrb.company_id
                JOIN public.servicenow_preclearance_details pd ON lsr.pangir = pd.pan_card
                JOIN public.servicenow_preclearances pc ON pd.ritm_number = pc.ritm_number
                WHERE 
                    lsr.position_difference != 0
                    AND pc.state = 'Closed Complete'
                    AND ABS(lsr.position_difference) > pd.approved_quantity
                ORDER BY lrb.latest_date DESC, lsr.name
                LIMIT %s OFFSET %s
            """, (limit, offset))
            rows = cur.fetchall()
            for r in rows:
                violations.append({
                    "shareholder_name": r['shareholder_name'],
                    "pan": r['pan'],
                    "company_name": r['company_name'],
                    "shares_traded": r['shares_traded'],
                    "approved_volume": r['approved_volume'],
                    "excess_volume": r['excess_volume'],
                    "batch_name": r['batch_name'],
                    "transaction_date": str(r['transaction_date']) if r['transaction_date'] else None,
                    "employee_name": r['employee_name'],
                    "employee_email": r['employee_email'],
                    "ritm_number": r['preclearance_ritm']
                })

        elif type.upper() == "HOLDING_MISMATCH":
            cur.execute("""
                WITH latest_sr AS (
                    SELECT DISTINCT ON (pangir, company_id)
                        pangir, company_id, position_latest
                    FROM public.shareholder_records
                    ORDER BY pangir, company_id, batch_id DESC
                )
                SELECT 
                    sd.requested_for AS employee,
                    sd.email AS employee_email,
                    sh.name AS declarant,
                    sh.relationship,
                    sh.pan_card AS pan,
                    c.company_name,
                    sh.declared_quantity,
                    lsr.position_latest AS depository_quantity,
                    (lsr.position_latest - sh.declared_quantity) AS difference,
                    sd.ritm_number AS declaration_ritm,
                    sd.phase,
                    sd.fiscal_year
                FROM public.servicenow_holdings sh
                JOIN public.servicenow_declarations sd ON sh.ritm_number = sd.ritm_number
                JOIN latest_sr lsr ON sh.pan_card = lsr.pangir AND sh.company_id = lsr.company_id
                JOIN public.companies c ON sh.company_id = c.id
                WHERE 
                    sd.state = 'Closed Complete'
                    AND sh.declared_quantity != lsr.position_latest
                ORDER BY sd.requested_for, c.company_name
                LIMIT %s OFFSET %s
            """, (limit, offset))
            rows = cur.fetchall()
            for r in rows:
                violations.append({
                    "employee_name": r['employee'],
                    "employee_email": r['employee_email'],
                    "declarant_name": r['declarant'],
                    "relationship": r['relationship'],
                    "pan": r['pan'],
                    "company_name": r['company_name'],
                    "declared_quantity": r['declared_quantity'],
                    "depository_quantity": r['depository_quantity'],
                    "difference": r['difference'],
                    "ritm_number": r['declaration_ritm'],
                    "phase": r['phase'],
                    "fiscal_year": r['fiscal_year']
                })

        return {"violations": violations, "count": len(violations)}
    except Exception as e:
        logger.error(f"Failed to fetch ServiceNow violations: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")
    finally:
        if conn:
            _return_conn(conn)
