r"""
=============================================================================
  AEGIS - ServiceNow PIT Compliance Pre-Calculator
=============================================================================
  Run this script manually ONCE A WEEK (after shareholder + ServiceNow data
  is refreshed) to pre-calculate all violation checks and store results in
  the 'compliance_cache_summary' and 'compliance_cache_violations' tables.

  Usage:
    cd Backend\aegis_backend
    python scripts\precalculate_compliance.py

  What it does:
    1. Creates/migrates the two cache tables if they don't exist.
    2. Runs the 3 heavy PAN-based cross-reference queries:
       - UNSANCTIONED  (traded without pre-clearance)
       - VOLUME_BREACH (traded more than approved)
       - HOLDING_MISMATCH (declared qty != depository qty)
    3. Stores the summary counts + detailed violation rows.
    4. Dashboard APIs read from these tables instantly.
=============================================================================
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

# ── Resolve .env ──────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_SCRIPT_DIR)  # aegis_backend/
env_path = os.path.join(_APP_DIR, ".env")
load_dotenv(env_path)

DB_HOST = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST') or '192.168.0.56'
DB_PORT = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT') or '5436'
DB_NAME = os.getenv('DB_NAME') or os.getenv('POSTGRES_DATABASE_INSIDER') or 'aegis_insider'
DB_USER = os.getenv('DB_USER') or os.getenv('POSTGRES_USER') or 'postgres'
DB_PASS = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD') or 'postgres'


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
        cursor_factory=RealDictCursor
    )


def create_cache_tables(cur):
    """Create the two cache tables + indexes if they don't exist."""

    # Summary KPI cache (one row per calculation run)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.compliance_cache_summary (
            id              SERIAL PRIMARY KEY,
            total_declarations      INTEGER DEFAULT 0,
            total_holdings          INTEGER DEFAULT 0,
            total_preclearances     INTEGER DEFAULT 0,
            unsanctioned_count      INTEGER DEFAULT 0,
            volume_breach_count     INTEGER DEFAULT 0,
            holding_mismatch_count  INTEGER DEFAULT 0,
            calculated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Detailed violations cache (all rows from 3 violation types)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.compliance_cache_violations (
            id                  SERIAL PRIMARY KEY,
            violation_type      VARCHAR(30) NOT NULL,
            shareholder_name    VARCHAR(255),
            pan                 VARCHAR(20),
            company_name        VARCHAR(255),
            employee_name       VARCHAR(255),
            employee_email      VARCHAR(255),
            shares_traded       REAL,
            approved_volume     INTEGER,
            excess_volume       REAL,
            declared_quantity   INTEGER,
            depository_quantity REAL,
            difference          REAL,
            ritm_number         VARCHAR(50),
            batch_name          VARCHAR(100),
            transaction_date    VARCHAR(50),
            relationship        VARCHAR(100),
            phase               VARCHAR(50),
            fiscal_year         VARCHAR(50),
            calculated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Index for fast filtering by violation_type
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ccv_type
        ON public.compliance_cache_violations (violation_type);
    """)

    print("  [OK] Cache tables created/verified.")


def calculate_simple_counts(cur):
    """Get direct counts from ServiceNow tables (fast, no joins)."""
    cur.execute("SELECT COUNT(*) AS cnt FROM public.servicenow_declarations")
    total_dec = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM public.servicenow_holdings")
    total_hold = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM public.servicenow_preclearances")
    total_pc = cur.fetchone()['cnt']

    return total_dec, total_hold, total_pc


def calculate_unsanctioned(cur):
    """
    Find shareholder trades where:
    - The PAN exists in ServiceNow (known insider)
    - position_difference != 0 (they traded)
    - No matching pre-clearance with 'Closed Complete' state
    Only looks at the latest batch per company.
    """
    cur.execute("""
        SELECT
            sr.name             AS shareholder_name,
            sr.pangir           AS pan,
            c.company_name,
            sr.position_difference AS shares_traded,
            rb.batch_name,
            rb.latest_date      AS transaction_date,
            COALESCE(
                (SELECT requested_for FROM public.servicenow_declarations
                 WHERE email = sr.email LIMIT 1),
                (SELECT requested_for FROM public.servicenow_preclearances
                 WHERE email = sr.email LIMIT 1),
                'Insider Employee'
            ) AS employee_name,
            sr.email AS employee_email
        FROM public.shareholder_records sr
        JOIN (
            SELECT company_id, MAX(batch_id) AS max_batch_id
            FROM public.shareholder_records
            GROUP BY company_id
        ) lb ON sr.company_id = lb.company_id AND sr.batch_id = lb.max_batch_id
        JOIN public.companies c ON sr.company_id = c.id
        JOIN public.result_batches rb ON sr.batch_id = rb.id
        JOIN (
            SELECT DISTINCT pan_card FROM public.servicenow_holdings WHERE pan_card != ''
            UNION
            SELECT DISTINCT pan_card FROM public.servicenow_preclearance_details WHERE pan_card != ''
        ) dp ON sr.pangir = dp.pan_card
        WHERE
            sr.position_difference != 0
            AND NOT EXISTS (
                SELECT 1
                FROM public.servicenow_preclearance_details pd2
                JOIN public.servicenow_preclearances pc2 ON pd2.ritm_number = pc2.ritm_number
                WHERE pd2.pan_card = sr.pangir AND pc2.state = 'Closed Complete'
            )
        ORDER BY rb.latest_date DESC, sr.name
    """)
    rows = cur.fetchall()
    results = []
    for r in rows:
        results.append({
            "violation_type": "UNSANCTIONED",
            "shareholder_name": r['shareholder_name'],
            "pan": r['pan'],
            "company_name": r['company_name'],
            "shares_traded": r['shares_traded'],
            "batch_name": r['batch_name'],
            "transaction_date": str(r['transaction_date']) if r['transaction_date'] else None,
            "employee_name": r['employee_name'],
            "employee_email": r['employee_email'],
        })
    return results


def calculate_volume_breach(cur):
    """
    Find shareholder trades where:
    - The PAN has a 'Closed Complete' pre-clearance
    - ABS(position_difference) > approved_quantity
    Only looks at the latest batch per company.
    """
    cur.execute("""
        SELECT
            sr.name             AS shareholder_name,
            sr.pangir           AS pan,
            c.company_name,
            sr.position_difference AS shares_traded,
            pd.approved_quantity AS approved_volume,
            (ABS(sr.position_difference) - pd.approved_quantity) AS excess_volume,
            rb.batch_name,
            rb.latest_date      AS transaction_date,
            pc.requested_for    AS employee_name,
            pc.email            AS employee_email,
            pc.ritm_number      AS preclearance_ritm
        FROM public.shareholder_records sr
        JOIN (
            SELECT company_id, MAX(batch_id) AS max_batch_id
            FROM public.shareholder_records
            GROUP BY company_id
        ) lb ON sr.company_id = lb.company_id AND sr.batch_id = lb.max_batch_id
        JOIN public.companies c ON sr.company_id = c.id
        JOIN public.result_batches rb ON sr.batch_id = rb.id
        JOIN public.servicenow_preclearance_details pd ON sr.pangir = pd.pan_card
        JOIN public.servicenow_preclearances pc ON pd.ritm_number = pc.ritm_number
        WHERE
            sr.position_difference != 0
            AND pc.state = 'Closed Complete'
            AND ABS(sr.position_difference) > pd.approved_quantity
        ORDER BY excess_volume DESC
    """)
    rows = cur.fetchall()
    results = []
    for r in rows:
        results.append({
            "violation_type": "VOLUME_BREACH",
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
            "ritm_number": r['preclearance_ritm'],
        })
    return results


def calculate_holding_mismatch(cur):
    """
    Find holding declarations where:
    - declared_quantity != actual depository position_latest
    - Declaration state is 'Closed Complete'
    Only looks at the latest batch per company.
    """
    cur.execute("""
        SELECT
            sd.requested_for    AS employee_name,
            sd.email            AS employee_email,
            sh.name             AS declarant_name,
            sh.relationship,
            sh.pan_card         AS pan,
            c.company_name,
            sh.declared_quantity,
            sr.position_latest  AS depository_quantity,
            (sr.position_latest - sh.declared_quantity) AS difference,
            sd.ritm_number      AS declaration_ritm,
            sd.phase,
            sd.fiscal_year
        FROM public.servicenow_holdings sh
        JOIN public.servicenow_declarations sd ON sh.ritm_number = sd.ritm_number
        JOIN public.shareholder_records sr
            ON sh.pan_card = sr.pangir AND sr.company_id = sh.company_id
        JOIN (
            SELECT company_id, MAX(batch_id) AS max_batch_id
            FROM public.shareholder_records
            GROUP BY company_id
        ) lb ON sr.company_id = lb.company_id AND sr.batch_id = lb.max_batch_id
        JOIN public.companies c ON sh.company_id = c.id
        WHERE
            sd.state = 'Closed Complete'
            AND sh.declared_quantity != sr.position_latest
        ORDER BY sd.requested_for, c.company_name
    """)
    rows = cur.fetchall()
    results = []
    for r in rows:
        results.append({
            "violation_type": "HOLDING_MISMATCH",
            "shareholder_name": r['declarant_name'],
            "pan": r['pan'],
            "company_name": r['company_name'],
            "employee_name": r['employee_name'],
            "employee_email": r['employee_email'],
            "declared_quantity": r['declared_quantity'],
            "depository_quantity": r['depository_quantity'],
            "difference": r['difference'],
            "ritm_number": r['declaration_ritm'],
            "relationship": r['relationship'],
            "phase": r['phase'],
            "fiscal_year": r['fiscal_year'],
        })
    return results


def store_results(cur, total_dec, total_hold, total_pc, all_violations):
    """Atomically replace all cache data with the fresh calculation."""

    now = datetime.now()

    # Count violations by type
    unsanctioned_count = sum(1 for v in all_violations if v['violation_type'] == 'UNSANCTIONED')
    volume_breach_count = sum(1 for v in all_violations if v['violation_type'] == 'VOLUME_BREACH')
    holding_mismatch_count = sum(1 for v in all_violations if v['violation_type'] == 'HOLDING_MISMATCH')

    # ── Clear old data ──
    cur.execute("DELETE FROM public.compliance_cache_violations")
    cur.execute("DELETE FROM public.compliance_cache_summary")

    # ── Insert summary ──
    cur.execute("""
        INSERT INTO public.compliance_cache_summary
        (total_declarations, total_holdings, total_preclearances,
         unsanctioned_count, volume_breach_count, holding_mismatch_count, calculated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (total_dec, total_hold, total_pc,
          unsanctioned_count, volume_breach_count, holding_mismatch_count, now))

    # ── Insert violation detail rows ──
    for v in all_violations:
        cur.execute("""
            INSERT INTO public.compliance_cache_violations
            (violation_type, shareholder_name, pan, company_name,
             employee_name, employee_email, shares_traded,
             approved_volume, excess_volume,
             declared_quantity, depository_quantity, difference,
             ritm_number, batch_name, transaction_date,
             relationship, phase, fiscal_year, calculated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            v.get('violation_type'),
            v.get('shareholder_name'),
            v.get('pan'),
            v.get('company_name'),
            v.get('employee_name'),
            v.get('employee_email'),
            v.get('shares_traded'),
            v.get('approved_volume'),
            v.get('excess_volume'),
            v.get('declared_quantity'),
            v.get('depository_quantity'),
            v.get('difference'),
            v.get('ritm_number'),
            v.get('batch_name'),
            v.get('transaction_date'),
            v.get('relationship'),
            v.get('phase'),
            v.get('fiscal_year'),
            now,
        ))

    print(f"  [OK] Stored {len(all_violations)} violation rows + summary into cache.")


def main():
    print("=" * 65)
    print("  AEGIS - Compliance Pre-Calculator")
    print(f"  Database: {DB_NAME} @ {DB_HOST}:{DB_PORT}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Step 1: Ensure cache tables exist
        print("\n[1/5] Setting up cache tables...")
        create_cache_tables(cur)
        conn.commit()

        # Step 2: Simple counts
        print("[2/5] Counting ServiceNow records...")
        total_dec, total_hold, total_pc = calculate_simple_counts(cur)
        print(f"       Declarations: {total_dec}  |  Holdings: {total_hold}  |  Pre-clearances: {total_pc}")

        # Step 3: Unsanctioned trades
        print("[3/5] Calculating Unsanctioned Trades (PAN cross-check)...")
        unsanctioned = calculate_unsanctioned(cur)
        print(f"       Found {len(unsanctioned)} unsanctioned trades.")

        # Step 4: Volume breaches
        print("[4/5] Calculating Volume Breaches...")
        volume_breaches = calculate_volume_breach(cur)
        print(f"       Found {len(volume_breaches)} volume breaches.")

        # Step 5: Holding mismatches
        print("[5/5] Calculating Holding Mismatches...")
        holding_mismatches = calculate_holding_mismatch(cur)
        print(f"       Found {len(holding_mismatches)} holding mismatches.")

        # Combine and store
        all_violations = unsanctioned + volume_breaches + holding_mismatches

        print("\nStoring results to cache tables...")
        store_results(cur, total_dec, total_hold, total_pc, all_violations)
        conn.commit()

        print("\n" + "=" * 65)
        print("  [DONE] PRE-CALCULATION COMPLETE")
        print(f"  Total violations cached: {len(all_violations)}")
        print(f"    - Unsanctioned Trades : {len(unsanctioned)}")
        print(f"    - Volume Breaches     : {len(volume_breaches)}")
        print(f"    - Holding Mismatches  : {len(holding_mismatches)}")
        print("=" * 65)

    except Exception as e:
        conn.rollback()
        print(f"\n  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
