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

    # 1. Locate the JSON file
    default_json = os.path.join(_PROJECT_ROOT, "servicenow_data.json")
    backend_json = os.path.join(_BACKEND_DIR, "servicenow_data.json")
    
    selected_json = None
    if os.path.exists(default_json):
        selected_json = default_json
    elif os.path.exists(backend_json):
        selected_json = backend_json

    if not selected_json:
        print(f"[ERROR] Could not find 'servicenow_data.json'.")
        print(f"Please export your full ServiceNow dataset as a JSON file and place it at:")
        print(f"  {default_json}")
        print("\nAborting reconciliation.")
        sys.exit(1)
        
    print(f"[OK] Found dataset JSON at: {selected_json}")
    file_size_mb = os.path.getsize(selected_json) / (1024 * 1024)
    print(f"     File size: {file_size_mb:.2f} MB")
    
    # 2. Run Database Ingestion
    print("\n[STEP 1/2] Running database ingestion parser...")
    print("This reads the JSON dataset and upserts records into PostgreSQL.")
    print("-" * 60)
    
    # Make sure we are in Backend/aegis_backend directory so paths resolve correctly
    try:
        # Import run_ingestion
        sys.path.insert(0, _BACKEND_DIR)
        from routes.servicenow_ingestion import run_ingestion
        
        success = run_ingestion()
        if not success:
            print("[ERROR] Database Ingestion engine reported failure.")
            sys.exit(1)
        print("[SUCCESS] Data successfully ingested into the database tables.")
    except Exception as e:
        print(f"[ERROR] Failed to run ingestion: {e}")
        import traceback
        traceback.print_exc()
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
