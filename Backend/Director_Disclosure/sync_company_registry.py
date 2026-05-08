"""
sync_company_registry.py - Aegis Company Intelligence Sync
===========================================================
Fetches full company profiles from the Falconebiz MCA Registry API
and stores them in Azure PostgreSQL using a two-layer director architecture.

Run modes:
  python sync_company_registry.py              -> Interactive (batch or single)
  python sync_company_registry.py <CIN>        -> Single CIN
  python sync_company_registry.py --retry      -> Retry previously failed CINs only

Output:
  Console : Live progress with status per CIN
  File    : sync_failed_cins.log  (all CINs that failed, with reason)
  File    : sync_summary.txt      (final run statistics)
"""

import requests
import json
import os
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import urllib3
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# --- Environment --------------------------------------------------------
env_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aegis_backend", ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
]
for p in env_paths:
    if os.path.exists(p):
        load_dotenv(p)
        print(f"  [ENV] Loaded config from: {p}")
        break

# --- Configuration -------------------------------------------------------
API_KEY  = "tgNuM80eYUxtV0TX!Aa3furfuUcg"
API_URL  = "https://www.falconebiz.com/api/company_details"
DOMAIN   = "adani.com"
PROXY    = "http://cloudproxy.adani.com:8080"
PROXIES  = {"http": PROXY, "https": PROXY}
TIMEOUT  = 30    # seconds per request
DELAY    = 0.5   # seconds between requests (rate-limit safety)
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "sync_progress_cin.json")

def report_progress(current, total, status="Syncing..."):
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump({"current": current, "total": total, "status": status, "timestamp": time.time()}, f)
    except:
        pass

LOG_FAILED  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_failed_cins.log")
LOG_SUMMARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_summary.txt")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Error Classification ------------------------------------------------
ERROR_PROXY       = "PROXY_UNREACHABLE"
ERROR_SSL         = "SSL_ERROR"
ERROR_TIMEOUT     = "TIMEOUT"
ERROR_API_STATUS  = "API_HTTP_ERROR"
ERROR_EMPTY       = "EMPTY_RESPONSE"
ERROR_MISSING_CIN = "MISSING_CIN_IN_RESPONSE"
ERROR_DB          = "DB_WRITE_ERROR"
ERROR_UNKNOWN     = "UNKNOWN"


# ─── Utils ───────────────────────────────────────────────────────────────
def clean_numeric(val):
    """
    Cleans value for numeric DB columns.
    Returns: float | int | None
    """
    if val is None: return None
    s = str(val).strip().replace(',', '').replace('₹', '')
    if not s or s.lower() in ['n/a', 'null', 'none', '-']: return None
    try:
        if '.' in s: return float(s)
        return int(s)
    except: return None


# ─── DB Connection ───────────────────────────────────────────────────────
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"   [DB ERROR] Connection failed: {e}")
        return None


# ─── Schema Init ─────────────────────────────────────────────────────────
def init_company_schema():
    conn = get_db_connection()
    if not conn:
        print("  [SCHEMA] Cannot connect to DB — aborting schema check.")
        return False
    try:
        cur = conn.cursor()
        
        # 1. Ensure 'cin' exists and is unique
        cur.execute("ALTER TABLE directors_data.companies ADD COLUMN IF NOT EXISTS cin TEXT")
        
        # 2. Fix Constraints: Move from Name-uniqueness to CIN-uniqueness
        # We drop the 'name' unique constraint if it exists to allow CIN-based upserts
        cur.execute("""
            DO $$ 
            BEGIN 
                -- Drop the old 'name' unique constraint if it exists
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE table_schema = 'directors_data' 
                    AND table_name = 'companies' 
                    AND constraint_name = 'companies_name_key'
                ) THEN
                    ALTER TABLE directors_data.companies DROP CONSTRAINT companies_name_key;
                END IF;
                
                -- Add Unique CIN constraint if missing
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE table_schema = 'directors_data' 
                    AND table_name = 'companies' 
                    AND constraint_name = 'companies_cin_key'
                ) THEN
                    ALTER TABLE directors_data.companies ADD CONSTRAINT companies_cin_key UNIQUE (cin);
                END IF;
            END $$;
        """)

        # 3. Fix Sequence: Sync the ID sequence to prevent pkey violations
        cur.execute("""
            SELECT setval('directors_data.companies_id_seq', (SELECT COALESCE(MAX(id), 1) FROM directors_data.companies));
        """)

        for col_name, col_type in [
            ("status", "TEXT"), ("incorporation_date", "TEXT"),
            ("auth_capital", "NUMERIC"), ("paid_capital", "NUMERIC"),
            ("pincode", "TEXT"), ("category", "TEXT"), ("class", "TEXT"),
            ("roc", "TEXT"), ("subcategory", "TEXT"), ("state", "TEXT"),
            ("district", "TEXT"), ("activity", "TEXT"), ("last_agm", "TEXT"),
            ("last_bal_sheet", "TEXT"), ("email", "TEXT"), ("address", "TEXT"),
            ("list_status", "TEXT"), ("is_adani", "BOOLEAN DEFAULT TRUE"),
            ("last_sync", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
        ]:
            cur.execute(f"ALTER TABLE directors_data.companies ADD COLUMN IF NOT EXISTS {col_name} {col_type}")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS directors_data.company_charges (
                id SERIAL PRIMARY KEY,
                cin TEXT NOT NULL,
                charge_id TEXT,
                amount TEXT,
                holder TEXT,
                creation_date TEXT,
                closure_date TEXT
            );
            
            -- Fix column types if they were created as numeric previously
            DO $$ 
            BEGIN 
                IF (SELECT data_type FROM information_schema.columns 
                    WHERE table_schema = 'directors_data' AND table_name = 'company_charges' AND column_name = 'amount') != 'text' 
                THEN
                    ALTER TABLE directors_data.company_charges ALTER COLUMN amount TYPE TEXT;
                END IF;
            END $$;
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS directors_master.external_board_members (
                id SERIAL PRIMARY KEY,
                din TEXT NOT NULL,
                name TEXT,
                cin TEXT NOT NULL,
                company_name TEXT,
                designation TEXT,
                appointment_date TEXT,
                status TEXT,
                source TEXT DEFAULT 'COMPANY_API',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(din, cin)
            )
        """)
        # Ensure status column exists for existing tables
        cur.execute("ALTER TABLE directors_master.external_board_members ADD COLUMN IF NOT EXISTS status TEXT")
        conn.commit()
        print("  [SCHEMA] All tables verified/ready.\n")
        return True
    except Exception as e:
        print(f"  [SCHEMA ERROR] {e}")
        return False
    finally:
        conn.close()


# --- Log Failed CIN ------------------------------------------------------
def log_failure(cin: str, reason: str, detail: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FAILED, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {cin} | {reason} | {detail[:200]}\n")


# --- API Fetch -----------------------------------------------------------
def fetch_from_api(cin: str, session: requests.Session = None):
    """
    Returns (data_dict, None) on success.
    Returns (None, error_code) on failure.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": API_KEY,
        "Company": cin,
        "Domain": DOMAIN
    }
    
    # Use global proxies if not using a session with them pre-configured
    fetcher = session if session else requests
    
    try:
        response = fetcher.get(
            API_URL, headers=headers, proxies=PROXIES if not session else None,
            timeout=TIMEOUT, verify=False
        )
        if response.status_code == 200:
            data = response.json()
            if not data or 'company_details' not in data:
                return None, ERROR_EMPTY
            return data, None
        else:
            return None, f"{ERROR_API_STATUS}:{response.status_code}"

    except requests.exceptions.ProxyError as e:
        return None, ERROR_PROXY
    except requests.exceptions.SSLError as e:
        return None, ERROR_SSL
    except requests.exceptions.Timeout:
        return None, ERROR_TIMEOUT
    except Exception as e:
        return None, f"{ERROR_UNKNOWN}:{str(e)[:100]}"


# --- DB Write ------------------------------------------------------------
def save_company_to_db(data: dict) -> tuple[bool, str]:
    """Returns (True, 'ok') on success, (False, error_code) on failure."""
    details  = data.get('company_details', {})
    filings  = data.get('filings', {})
    contacts = data.get('contact_details', {})
    cin      = details.get('cin')
    if not cin: 
        return False, ERROR_MISSING_CIN

    conn = get_db_connection()
    if not conn: 
        return False, ERROR_DB
    try:
        cur = conn.cursor()

        # 1. Upsert company record
        cur.execute("""
            INSERT INTO directors_data.companies (
                cin, name, status, incorporation_date, auth_capital, paid_capital,
                pincode, category, class, roc, subcategory, state, district,
                activity, last_agm, last_bal_sheet, email, address, list_status, last_sync
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
            ON CONFLICT (cin) DO UPDATE SET
                name=EXCLUDED.name, status=EXCLUDED.status,
                incorporation_date=EXCLUDED.incorporation_date,
                auth_capital=EXCLUDED.auth_capital, paid_capital=EXCLUDED.paid_capital,
                pincode=EXCLUDED.pincode, category=EXCLUDED.category,
                class=EXCLUDED.class, roc=EXCLUDED.roc, subcategory=EXCLUDED.subcategory,
                state=EXCLUDED.state, district=EXCLUDED.district,
                activity=EXCLUDED.activity, last_agm=EXCLUDED.last_agm,
                last_bal_sheet=EXCLUDED.last_bal_sheet, email=EXCLUDED.email,
                address=EXCLUDED.address, list_status=EXCLUDED.list_status,
                last_sync=CURRENT_TIMESTAMP
        """, (
            cin, details.get('company_name'), details.get('statusname'),
            details.get('incorporation_date'), 
            clean_numeric(details.get('auth_capital')),
            clean_numeric(details.get('paid_capital')), 
            details.get('pincode'),
            details.get('category'), details.get('class'), details.get('roc'),
            details.get('subcategory'), details.get('state'), details.get('district'),
            details.get('activity'), filings.get('last_agm'), filings.get('last_bal_sheet'),
            contacts.get('email'), contacts.get('address'), details.get('list_status')
        ))

        # 2. Two-layer director sync
        directors_list = data.get('directors', [])
        if isinstance(directors_list, list) and directors_list:
            cur.execute("SELECT din FROM directors_master.directors WHERE din IS NOT NULL")
            group_dins = {r[0] for r in cur.fetchall()}
            company_name = details.get('company_name')

            for d in directors_list:
                din   = d.get('din')
                name  = d.get('director_name')
                desig = d.get('designation')
                appt  = d.get('appointment_date')
                if not din: continue

                # Layer A: Full external catalogue (always)
                cur.execute("""
                    INSERT INTO directors_master.external_board_members
                        (din, name, cin, company_name, designation, appointment_date, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (din, cin) DO UPDATE SET
                        name=EXCLUDED.name, company_name=EXCLUDED.company_name,
                        designation=EXCLUDED.designation, appointment_date=EXCLUDED.appointment_date,
                        status=EXCLUDED.status
                """, (din, name, cin, company_name, desig, appt, details.get('statusname')))

                # Layer B: RESERVED FOR DIN SYNC SCRIPT ONLY
                # We no longer update external_board_members from the Company API 
                # to prevent data conflicts with the Director-centric sync.
                pass

        # 3. Charges — store amount as TEXT to preserve API values exactly
        cur.execute("DELETE FROM directors_data.company_charges WHERE cin = %s", (cin,))
        # Try both 'charges_borrowings' and 'charges' keys
        charges = data.get('charges_borrowings') or data.get('charges') or []
        
        if isinstance(charges, list):
            for chg in charges:
                # Robust key detection for Amount, ID, and Holder
                raw_amt = chg.get('amount') or chg.get('amount_charge') or chg.get('charge_amount') or chg.get('charge_amt')
                ch_id   = chg.get('chargeid') or chg.get('charge_id') or chg.get('id')
                holder  = chg.get('charge_holder') or chg.get('holder') or chg.get('bank_name')
                
                amt_str = str(raw_amt) if raw_amt is not None and str(raw_amt).strip() != "" else "0"
                
                cur.execute("""
                    INSERT INTO directors_data.company_charges
                        (cin, charge_id, amount, holder, creation_date, closure_date)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (cin, ch_id, amt_str, holder, 
                      chg.get('creation_date'), chg.get('closure_date')))

        conn.commit()
        return True, "ok"

    except Exception as e:
        conn.rollback()
        # Only print the short version of the error to keep console clean
        # The full error is caught by sync_one and logged to file
        print(f"   [DB WRITE ERROR] {str(e)[:100]}")
        return False, ERROR_DB
    finally:
        conn.close()


# --- Single CIN Sync -----------------------------------------------------
def sync_one(cin: str, idx: int = 1, total: int = 1, session: requests.Session = None) -> str:
    """
    Syncs a single CIN.
    Returns: 'ok' | error_code string
    """
    prefix = f"  [{idx:>4}/{total:>4}]"
    report_progress(idx, total, f"Syncing {cin}")

    # 1. Fetch
    data, err = fetch_from_api(cin, session)

    if err:
        label = {
            ERROR_PROXY:   "PROXY UNREACHABLE",
            ERROR_SSL:     "SSL ERROR",
            ERROR_TIMEOUT: "TIMEOUT",
            ERROR_EMPTY:   "EMPTY RESPONSE",
        }.get(err, err)
        print(f"{prefix} [FAIL] {cin:<22}  ->  {label}")
        log_failure(cin, err)
        return err

    # 2. Save
    name = data.get('company_details', {}).get('company_name', 'Unknown')
    try:
        ok, err_code = save_company_to_db(data)
        if ok:
            boards = len(data.get('directors', []))
            charges = len(data.get('charges_borrowings', []))
            # Clean up the name for display
            display_name = (name[:45] + '...') if len(name) > 45 else name
            print(f"{prefix} [OK]   {cin:<22}  ->  {display_name:<48} ({boards} dirs, {charges} charges)")
            return "ok"
        else:
            label = {
                ERROR_MISSING_CIN: "API RESPONSE MISSING CIN",
                ERROR_DB:          "DATABASE WRITE FAILED"
            }.get(err_code, err_code)
            print(f"{prefix} [FAIL] {cin:<22}  ->  {label}")
            log_failure(cin, err_code, f"company={name}")
            return err_code
    except Exception as e:
        print(f"{prefix} [FAIL] {cin:<22}  ->  EXCEPTION: {str(e)[:50]}")
        log_failure(cin, ERROR_UNKNOWN, str(e))
        return ERROR_UNKNOWN


# --- Batch Sync ----------------------------------------------------------
def sync_all_cin_from_db(max_workers: int = 15):
    conn = get_db_connection()
    if not conn:
        print("  [FATAL] Cannot connect to database.")
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT cin FROM directors_master.external_board_members
            WHERE cin IS NOT NULL AND cin != ''
        """)
        cins = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

    total = len(cins)
    print(f"\n  Found {total} unique CINs to sync. Using {max_workers} parallel workers.\n")
    print(f"  {'─'*70}")

    # Clear old failure log for fresh run
    if os.path.exists(LOG_FAILED):
        os.remove(LOG_FAILED)

    stats = {"ok": 0, "proxy": 0, "ssl": 0, "timeout": 0, "api": 0, "db": 0, "other": 0}
    stats_lock = threading.Lock()
    start_time = time.time()

    # Use a persistent session with proxies pre-configured
    session = requests.Session()
    session.proxies = PROXIES
    session.verify = False

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cin = {
                executor.submit(sync_one, cin, i, total, session): cin 
                for i, cin in enumerate(cins, 1)
            }
            
            for future in as_completed(future_to_cin):
                result = future.result()
                
                with stats_lock:
                    if result == "ok":
                        stats["ok"] += 1
                    elif result == ERROR_PROXY:
                        stats["proxy"] += 1
                    elif result == ERROR_SSL:
                        stats["ssl"] += 1
                    elif result == ERROR_TIMEOUT:
                        stats["timeout"] += 1
                    elif result and ERROR_API_STATUS in result:
                        stats["api"] += 1
                    elif result == ERROR_DB:
                        stats["db"] += 1
                    else:
                        stats["other"] += 1

                    # Optional: Rate limit safety even in parallel
                    # time.sleep(DELAY / max_workers) 

    finally:
        session.close()

    elapsed = time.time() - start_time
    report_progress(total, total, "Complete")
    _write_summary(stats, total, elapsed, cins)


# --- Retry Failed --------------------------------------------------------
def retry_failed(max_workers: int = 15):
    if not os.path.exists(LOG_FAILED):
        print("  No failed CINs log found. Run a full sync first.")
        return

    with open(LOG_FAILED, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    cins = list({line.split("|")[1].strip() for line in lines if "|" in line})
    total = len(cins)
    print(f"\n  Retrying {total} previously failed CINs using {max_workers} workers...\n")

    # Clear for fresh retry log
    open(LOG_FAILED, "w").close()

    stats = {"ok": 0, "proxy": 0, "ssl": 0, "timeout": 0, "api": 0, "db": 0, "other": 0}
    stats_lock = threading.Lock()
    start = time.time()
    
    session = requests.Session()
    session.proxies = PROXIES
    session.verify = False

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cin = {
                executor.submit(sync_one, cin, i, total, session): cin 
                for i, cin in enumerate(cins, 1)
            }
            
            for future in as_completed(future_to_cin):
                result = future.result()
                with stats_lock:
                    category = (
                        "ok" if result == "ok"
                        else "proxy" if result == ERROR_PROXY
                        else "ssl" if result == ERROR_SSL
                        else "timeout" if result == ERROR_TIMEOUT
                        else "api" if result and ERROR_API_STATUS in result
                        else "db" if result == ERROR_DB
                        else "other"
                    )
                    stats[category] += 1
    finally:
        session.close()

    _write_summary(stats, total, time.time() - start, cins)


# --- Summary Writer ------------------------------------------------------
def _write_summary(stats: dict, total: int, elapsed: float, cins: list):
    failed = total - stats["ok"]
    lines = [
        "===============================================================",
        "  AEGIS COMPANY SYNC - FINAL REPORT",
        f"  Run completed : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "===============================================================",
        f"  Total CINs attempted : {total}",
        f"  [OK]   Successfully synced  : {stats['ok']}",
        f"  [FAIL] Failed total         : {failed}",
        "  -------------------------------------------------------------",
        f"     Proxy unreachable  : {stats['proxy']}",
        f"     SSL errors         : {stats['ssl']}",
        f"     Timeouts           : {stats['timeout']}",
        f"     API HTTP errors    : {stats['api']}",
        f"     DB write errors    : {stats['db']}",
        f"     Other errors       : {stats['other']}",
        "  -------------------------------------------------------------",
        f"  Time elapsed : {elapsed:.1f}s  ({elapsed/60:.1f} min)",
    ]
    if failed > 0:
        lines += [
            f"  Failed CINs logged to : sync_failed_cins.log",
            f"  To retry:  python sync_company_registry.py --retry",
        ]
    lines.append("===============================================================")

    output = "\n".join(lines)
    print(f"\n{output}\n")

    with open(LOG_SUMMARY, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"  Summary saved to: {LOG_SUMMARY}")


# --- Entry Point ---------------------------------------------------------
if __name__ == "__main__":
    print("\n  AEGIS COMPANY INTELLIGENCE SYNC")
    print(f"  Proxy : {PROXY}")
    print(f"  DB    : {os.getenv('POSTGRES_HOST', 'NOT CONFIGURED')} / {os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system')}")
    print()

    if not init_company_schema():
        print("  [FATAL] Schema init failed — check DB connection and exit.")
        sys.exit(1)

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--retry":
            retry_failed()
        elif arg == "--all":
            sync_all_cin_from_db()
        else:
            # Single CIN mode
            sync_one(arg, 1, 1)
    else:
        print("  Select mode:")
        print("  [1] Sync ALL CINs from database")
        print("  [2] Sync a single CIN")
        print("  [3] Retry previously failed CINs")
        choice = input("\n  Enter choice (1/2/3): ").strip()

        if choice == "1":
            sync_all_cin_from_db()
        elif choice == "2":
            cin = input("  Enter CIN/LLPIN: ").strip()
            if cin:
                sync_one(cin)
        elif choice == "3":
            retry_failed()
        else:
            print("  Invalid choice.")
