import os
import sys
import json
import subprocess
from dotenv import load_dotenv

# Set up paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR) # Backend/aegis_backend
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR) # project root aegis-prod-final

# Load environment variables
env_path = os.path.join(_BACKEND_DIR, ".env")
load_dotenv(env_path)

def print_header():
    print("=" * 70)
    print("      AEGIS - ServiceNow Offline Full Data Reconciliation Tool")
    print("=" * 70)
    print("This script runs the complete ingestion and PIT compliance analysis")
    print("offline. It will process your dataset and refresh the UI cache.")
    print("-" * 70)

def run_reconciliation():
    print_header()

    # 1. Fetch data directly from DB instead of JSON
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_servicenow_data():
        """Fetches ServiceNow data from DB instead of JSON file using .env credentials"""
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5436"),
            database=os.getenv("DB_NAME", "aegis_insider"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Fetch Declarations and their Holdings
        cur.execute("SELECT * FROM servicenow_declarations")
        declarations = cur.fetchall()
        for decl in declarations:
            cur.execute("SELECT * FROM servicenow_holdings WHERE ritm_number = %s", (decl['ritm_number'],))
            decl['holdings'] = [dict(row) for row in cur.fetchall()]
            
        # Fetch Preclearances and their Details
        cur.execute("SELECT * FROM servicenow_preclearances")
        preclearances = cur.fetchall()
        for precl in preclearances:
            cur.execute("SELECT * FROM servicenow_preclearance_details WHERE ritm_number = %s", (precl['ritm_number'],))
            precl['details'] = [dict(row) for row in cur.fetchall()]
            
        conn.close()
        
        return {
            "declarations": [dict(d) for d in declarations],
            "preclearances": [dict(p) for p in preclearances]
        }

    try:
        servicenow_data = get_servicenow_data()
        print(f"[OK] Fetched {len(servicenow_data['declarations'])} declarations and {len(servicenow_data['preclearances'])} preclearances directly from Postgres DB!")
    except Exception as e:
        print(f"[ERROR] Failed to fetch data from Postgres DB: {e}")
        sys.exit(1)

    # 3. Run Compliance Pre-calculation
    print("\n[STEP 2/2] Running compliance pre-calculation checks...")
    print("This executes PIT compliance queries on PostgreSQL and updates the UI cache.")
    print("-" * 60)
    
    precalc_script = os.path.join(_SCRIPT_DIR, "precalculate_compliance.py")
    if not os.path.exists(precalc_script):
        print(f"[ERROR] Precalculation script not found at {precalc_script}")
        sys.exit(1)
        
    try:
        # Run precalculate_compliance.py as a subprocess to keep environments isolated
        result = subprocess.run(
            [sys.executable, precalc_script],
            cwd=_BACKEND_DIR,
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print("[ERROR] Compliance precalculation failed.")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to run precalculation: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("  [SUCCESS] OFFLINE RECONCILIATION COMPLETE!")
    print("  The database is fully updated and cached.")
    print("  Open the Aegis UI ServiceNow Reconciliation dashboard to see the results.")
    print("=" * 70)

if __name__ == "__main__":
    run_reconciliation()
