"""
institutional_risk.py
Institutional Risk Monitor – Backend API
Provides deep analytics on the 928-company ecosystem enriched from Falconebiz MCA Registry.
"""
from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
import os, psycopg2
from dotenv import load_dotenv
from datetime import datetime, date
import traceback

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

router = APIRouter(prefix="/institutional-risk", tags=["Institutional Risk"])

def get_conn():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
        sslmode='require'
    )

def safe_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)


# ─────────────────────────── KPI SUMMARY ───────────────────────────
@router.get("/summary")
def get_risk_summary():
    """High-level KPIs: Leverage Index, Statutory Health, Capitalisation Density."""
    try:
        conn = get_conn()
        cur = safe_cursor(conn)

        # Total unique CINs tracked across the ecosystem (external_associations is the source of truth)
        try:
            cur.execute("""
                SELECT COUNT(DISTINCT cin) AS total
                FROM directors_master.external_board_members
                WHERE cin IS NOT NULL AND cin != ''
                  AND (status IS NULL OR (UPPER(status) != 'AMALGAMATED' AND UPPER(status) NOT LIKE 'RESIGNED%' AND UPPER(status) NOT LIKE 'INACTIVE%'))
            """)
            total = cur.fetchone()["total"]
        except Exception:
            conn.rollback()
            try:
                cur.execute("SELECT COUNT(*) AS total FROM directors_data.companies WHERE cin IS NOT NULL")
                total = cur.fetchone()["total"]
            except Exception:
                conn.rollback()
                total = 0

        # Ecosystem Leverage Index — cleaned aggresively to handle all symbols/spaces
        try:
            cur.execute("""
                SELECT
                    COALESCE(SUM(
                        CASE WHEN NULLIF(REGEXP_REPLACE(amount, '[^0-9.]', '', 'g'), '') IS NOT NULL
                             THEN CAST(NULLIF(REGEXP_REPLACE(amount, '[^0-9.]', '', 'g'), '') AS NUMERIC)
                             ELSE 0 END
                    ), 0) AS total_charges,
                    COUNT(*) AS charge_records
                FROM directors_data.company_charges
            """)
            charges    = cur.fetchone()
            total_charges  = float(charges["total_charges"])
            charge_records = charges["charge_records"]
        except Exception:
            conn.rollback()
            total_charges  = 0.0
            charge_records = 0

        # Capitalisation density
        try:
            cur.execute("""
                SELECT COALESCE(SUM(paid_capital), 0) AS total_paid,
                       COALESCE(SUM(auth_capital), 0) AS total_auth
                FROM directors_data.companies
                WHERE cin IS NOT NULL
            """)
            capital = cur.fetchone()
            total_paid = float(capital["total_paid"])
            total_auth = float(capital["total_auth"])
        except Exception:
            conn.rollback()
            total_paid = 0.0
            total_auth = 0.0

        # Statutory Health — count companies where last_agm is a 4-digit year (valid date)
        try:
            cur.execute("""
                SELECT COUNT(*) AS healthy
                FROM directors_data.companies
                WHERE last_agm IS NOT NULL
                  AND last_agm != ''
                  AND last_agm NOT IN ('Not Available', 'N/A', '-')
                  AND last_agm ~ '^[0-9]{4}'
            """)
            healthy = cur.fetchone()["healthy"]
        except Exception:
            conn.rollback()
            try:
                cur.execute("""
                    SELECT COUNT(*) AS healthy FROM directors_data.companies
                    WHERE last_agm IS NOT NULL AND last_agm != ''
                """)
                healthy = cur.fetchone()["healthy"]
            except Exception:
                conn.rollback()
                healthy = 0
        health_pct = round((healthy / total * 100), 1) if total > 0 else 0

        # Status breakdown with Drilldown (State-wise)
        try:
            cur.execute("""
                SELECT COALESCE(status, 'Unknown') AS status, COALESCE(state, 'Unknown') AS state, COUNT(*) AS count
                FROM directors_data.companies
                WHERE cin IS NOT NULL
                GROUP BY 1, 2 ORDER BY 1, 3 DESC
            """)
            raw_data = cur.fetchall()
            status_map = {}
            for row in raw_data:
                s = row['status']
                if s not in status_map:
                    status_map[s] = {"status": s, "count": 0, "state_breakdown": []}
                status_map[s]["count"] += row["count"]
                status_map[s]["state_breakdown"].append({"name": row["state"], "y": row["count"]})
            status_breakdown = list(status_map.values())
        except Exception:
            conn.rollback()
            status_breakdown = []

        # Listed vs Unlisted
        try:
            cur.execute("""
                SELECT COALESCE(list_status, 'Unknown') AS list_status, COUNT(*) AS count
                FROM directors_data.companies
                WHERE cin IS NOT NULL
                GROUP BY 1 ORDER BY 2 DESC
            """)
            listing_breakdown = [dict(r) for r in cur.fetchall()]
        except Exception:
            conn.rollback()
            listing_breakdown = []

        conn.close()
        return {
            "total_companies":     total,
            "ecosystem_leverage":  total_charges,
            "charge_records":      charge_records,
            "total_paid_capital":  total_paid,
            "total_auth_capital":  total_auth,
            "statutory_health_pct": health_pct,
            "filed_agm_count":     healthy,
            "status_breakdown":    status_breakdown,
            "listing_breakdown":   listing_breakdown
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────── RED FLAGS ───────────────────────────
@router.get("/red-flags")
def get_red_flags():
    """Returns dormant entities, stale-filing companies, and high-leverage entities."""
    try:
        conn = get_conn()
        cur = safe_cursor(conn)

        # 1. Non-active companies still with director associations
        cur.execute("""
            SELECT c.cin, c.name, c.name as company_name, c.status, c.state, c.last_agm, c.last_bal_sheet,
                   COUNT(ea.din) AS director_count
            FROM directors_data.companies c
            JOIN directors_master.external_board_members ea ON c.cin = ea.cin
            WHERE UPPER(COALESCE(c.status, '')) NOT IN ('ACTIVE', '')
              AND (ea.status IS NULL OR (UPPER(ea.status) != 'AMALGAMATED' AND UPPER(ea.status) NOT LIKE 'RESIGNED%' AND UPPER(ea.status) NOT LIKE 'INACTIVE%'))
            GROUP BY c.cin, c.name, c.status, c.state, c.last_agm, c.last_bal_sheet
            ORDER BY director_count DESC
            LIMIT 50
        """)
        dormant = [dict(r) for r in cur.fetchall()]

        # 2. Stale Filings (No AGM in 18 months or NULL)
        cur.execute("""
            SELECT c.cin, c.name, c.name as company_name, c.status, c.state, 
                   COUNT(ea.din) AS director_count,
                   c.last_agm, c.last_bal_sheet
            FROM directors_data.companies c
            LEFT JOIN directors_master.external_board_members ea ON c.cin = ea.cin
            WHERE (c.last_agm IS NULL OR c.last_agm = '' OR c.last_agm = 'Not Available')
              AND (ea.status IS NULL OR (UPPER(ea.status) != 'AMALGAMATED' AND UPPER(ea.status) NOT LIKE 'RESIGNED%' AND UPPER(ea.status) NOT LIKE 'INACTIVE%'))
            GROUP BY c.cin, c.name, c.status, c.state, c.last_agm, c.last_bal_sheet
            ORDER BY director_count DESC
            LIMIT 50
        """)
        stale = [dict(r) for r in cur.fetchall()]

        # 3. High-leverage entities ranked by total charges
        cur.execute("""
            SELECT c.cin, c.name, c.status, c.state, c.list_status,
                   c.name as company_name, 
                   COUNT(ch.id) AS active_charges,
                   COALESCE(SUM(
                       CASE WHEN NULLIF(REGEXP_REPLACE(ch.amount, '[^0-9.]', '', 'g'), '') IS NOT NULL
                            THEN CAST(NULLIF(REGEXP_REPLACE(ch.amount, '[^0-9.]', '', 'g'), '') AS NUMERIC)
                            ELSE 0 END
                   ), 0) AS total_charge_amount
            FROM directors_data.companies c
            LEFT JOIN directors_data.company_charges ch ON c.cin = ch.cin AND (ch.closure_date IS NULL OR ch.closure_date = 'N/A')
            GROUP BY c.cin, c.name, c.status, c.state, c.list_status
            HAVING COUNT(ch.id) > 5 OR 
                   SUM(CASE WHEN NULLIF(REGEXP_REPLACE(ch.amount, '[^0-9.]', '', 'g'), '') IS NOT NULL
                            THEN CAST(NULLIF(REGEXP_REPLACE(ch.amount, '[^0-9.]', '', 'g'), '') AS NUMERIC)
                            ELSE 0 END) > 1000000000
            ORDER BY total_charge_amount DESC
            LIMIT 50
        """)
        high_leverage = [dict(r) for r in cur.fetchall()]

        conn.close()
        return {
            "dormant_with_directors": dormant,
            "stale_filings": stale,
            "high_leverage": high_leverage
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────── SECTOR MAP ───────────────────────────
@router.get("/sector-map")
def get_sector_map():
    """Returns industrial sector breakdown from activity field."""
    try:
        conn = get_conn()
        cur = safe_cursor(conn)

        cur.execute("""
            SELECT 
                CASE 
                    WHEN activity ILIKE '%manufactur%' THEN 'Manufacturing'
                    WHEN activity ILIKE '%financ%' THEN 'Financial Services'
                    WHEN activity ILIKE '%infrastructure%' OR activity ILIKE '%construct%' THEN 'Infrastructure'
                    WHEN activity ILIKE '%energy%' OR activity ILIKE '%power%' OR activity ILIKE '%electric%' THEN 'Energy'
                    WHEN activity ILIKE '%real estate%' OR activity ILIKE '%property%' THEN 'Real Estate'
                    WHEN activity ILIKE '%transport%' OR activity ILIKE '%logistics%' THEN 'Logistics'
                    WHEN activity ILIKE '%information%' OR activity ILIKE '%software%' OR activity ILIKE '%technolog%' THEN 'Technology'
                    WHEN activity ILIKE '%mining%' OR activity ILIKE '%mineral%' THEN 'Mining & Resources'
                    WHEN activity ILIKE '%trade%' OR activity ILIKE '%wholesale%' THEN 'Trade'
                    WHEN activity ILIKE '%service%' THEN 'Services'
                    ELSE 'Other'
                END AS sector,
                COUNT(*) AS count,
                COALESCE(SUM(paid_capital), 0) AS total_capital
            FROM directors_data.companies
            WHERE cin IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
        """)
        sectors = [dict(r) for r in cur.fetchall()]

        # State-wise distribution
        cur.execute("""
            SELECT COALESCE(state, 'Unknown') AS state, COUNT(*) AS count
            FROM directors_data.companies
            WHERE cin IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 20
        """)
        states = [dict(r) for r in cur.fetchall()]

        conn.close()
        return {"sectors": sectors, "states": states}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────── ENTITY PEDIGREE ───────────────────────────
@router.get("/entity/{cin}")
def get_entity_pedigree(cin: str):
    """Full company profile + board + charges for drill-down modal."""
    try:
        conn = get_conn()
        cur = safe_cursor(conn)

        cur.execute("SELECT * FROM directors_data.companies WHERE cin = %s", (cin,))
        company = cur.fetchone()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found in registry")

        cur.execute("""
            SELECT ea.din, ea.designation, ea.appointment_date, 
                   COALESCE(d.name, ea.company_name) AS director_name,
                   d.din_status, d.gender
            FROM directors_master.external_board_members ea
            LEFT JOIN directors_master.directors d ON ea.din = d.din
            WHERE ea.cin = %s
              AND (ea.status IS NULL OR (UPPER(ea.status) != 'AMALGAMATED' AND UPPER(ea.status) NOT LIKE 'RESIGNED%' AND UPPER(ea.status) NOT LIKE 'INACTIVE%'))
            ORDER BY ea.appointment_date
        """, (cin,))
        board = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT charge_id, amount, holder, creation_date, closure_date
            FROM directors_data.company_charges
            WHERE cin = %s
            ORDER BY creation_date DESC
        """, (cin,))
        charges = [dict(r) for r in cur.fetchall()]

        conn.close()
        return {
            "company": dict(company),
            "board": board,
            "charges": charges,
            "total_charge": sum(float(str(c.get("amount", "0")).replace(',', '').replace(' ', '') or 0) for c in charges)
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────── BOARD INTERLOCK ───────────────────────────
@router.get("/board-interlock")
def get_board_interlock():
    """
    Shows external directors (non-Adani) who share board seats with group directors.
    Source: directors_master.external_board_members (Layer A of Two-Layer Registry).
    Only returns people co-sitting on CINs where at least one Adani group director sits.
    """
    try:
        conn = get_conn()
        cur = safe_cursor(conn)

        cur.execute("""
            SELECT
                ebm.din,
                COALESCE(ebm.name, 'Unknown') AS director_name,
                COUNT(DISTINCT ebm.cin)        AS company_count,
                array_agg(DISTINCT ebm.company_name ORDER BY ebm.company_name) AS companies,
                FALSE                          AS is_group_director
            FROM directors_master.external_board_members ebm
            WHERE
                -- Only on CINs where at least one Adani group director also sits
                EXISTS (
                    SELECT 1 FROM directors_master.external_board_members ea
                    WHERE ea.cin = ebm.cin
                )
                -- Exclude people who ARE Adani group directors
                AND NOT EXISTS (
                    SELECT 1 FROM directors_master.directors d WHERE d.din = ebm.din
                )
            GROUP BY ebm.din, ebm.name
            HAVING COUNT(DISTINCT ebm.cin) >= 1
            ORDER BY company_count DESC
            LIMIT 50
        """)
        interlocks = [dict(r) for r in cur.fetchall()]

        # Serialise the array_agg safely
        for row in interlocks:
            row['companies'] = list(row.get('companies') or [])

        conn.close()
        return {"interlocks": interlocks}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────── DISCLOSURE vs REGISTRY DIFF ───────────────────────────
@router.get("/disclosure-diff")
def get_disclosure_diff():
    """Identifies directors where MBP-1 board count vs registry count diverges."""
    try:
        conn = get_conn()
        cur = safe_cursor(conn)

        cur.execute("""
            SELECT 
                d.din,
                d.name,
                d.external_board_count AS registry_count,
                ds.directorships_mentioned AS disclosed_count,
                ABS(COALESCE(d.external_board_count, 0) - COALESCE(ds.directorships_mentioned, 0)) AS discrepancy
            FROM directors_master.directors d
            LEFT JOIN (
                SELECT din, COUNT(*) AS directorships_mentioned
                FROM directors_data.directorships
                GROUP BY din
            ) ds ON d.din = ds.din
            WHERE d.last_api_sync IS NOT NULL
            ORDER BY discrepancy DESC
            LIMIT 30
        """)
        diffs = [dict(r) for r in cur.fetchall()]

        conn.close()
        return {"discrepancies": diffs}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
