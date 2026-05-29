import os
import sys
import time
import requests
import psycopg2
from dotenv import load_dotenv
import subprocess
import urllib3
from datetime import datetime

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load configuration
env_path = os.path.join(os.path.dirname(__file__), '..', 'aegis_backend', '.env')
load_dotenv(env_path)

# API Configuration
API_KEY = "tgNuM80eYUxtV0TX!Aa3furfuUcg"
UPDATE_URL = "https://www.falconebiz.com/api/request_update"
PROXIES = {
    "http": "http://cloudproxy.adani.com:8080",
    "https": "http://cloudproxy.adani.com:8080"
}

def log_info(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

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
        log_info(f"[ERROR] DB connection failed: {e}")
        return None

def trigger_refresh(items, type="DIN"):
    log_info(f"[PHASE 1] Triggering MCA Updates for {len(items)} {type}s...")
    start_time = time.time()
    success_count = 0
    
    for idx, item in enumerate(items, 1):
        headers = {
            "Content-Type": "application/json",
            "Authorization": API_KEY
        }
        if type == "DIN":
            headers["Din"] = str(item)
        else:
            headers["Company"] = str(item)

        try:
            # We use a short timeout and ignore errors to keep moving
            resp = requests.get(UPDATE_URL, headers=headers, proxies=PROXIES, verify=False, timeout=10)
            if resp.status_code == 200:
                success_count += 1
            print(f"  [{idx}/{len(items)}] {item}: {resp.status_code}", end="\r")
        except Exception as e:
            # Print to side or logs if needed, keep CLI progress clean
            print(f"  [{idx}/{len(items)}] {item}: FAILED", end="\r")
        
        # Rate limit safety
        time.sleep(0.1)
    
    elapsed = time.time() - start_time
    log_info(f"[DONE] Triggered {success_count}/{len(items)} updates successfully. (Duration: {elapsed:.1f}s)")

def run_sync_script(script_name):
    log_info(f"[PHASE 3] Starting Sync: {script_name}...")
    start_time = time.time()
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    try:
        subprocess.run([sys.executable, script_path, "--all"], check=True)
        elapsed = time.time() - start_time
        log_info(f"[SUCCESS] Completed {script_name} (Duration: {elapsed:.1f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        log_info(f"[ERROR] Sync failed for {script_name}: {e} (Duration: {elapsed:.1f}s)")

def main():
    overall_start = time.time()
    log_info("="*60)
    log_info("STARTING FULL REGISTRY REFRESH PIPELINE")
    log_info("="*60)

    # 1. Handle DINs
    log_info("Fetching DINs from database...")
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT din FROM directors_master.directors WHERE din IS NOT NULL")
            dins = [r[0] for r in cur.fetchall()]
            log_info(f"Retrieved {len(dins)} DINs from database.")
        except Exception as e:
            log_info(f"[ERROR] Failed to query DINs: {e}")
            dins = []
        finally:
            cur.close()
            conn.close()
    else:
        dins = []
    
    if dins:
        trigger_refresh(dins, "DIN")
        log_info("[WAIT] Waiting 2 minutes for DIN data to propagate in Falconebiz...")
        time.sleep(120)
        run_sync_script("sync_director_registry.py")
    else:
        log_info("No DINs found to sync.")
    
    # 2. Handle CINs
    log_info("Fetching CINs from database...")
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT cin FROM directors_data.companies WHERE cin IS NOT NULL")
            cins = [r[0] for r in cur.fetchall()]
            log_info(f"Retrieved {len(cins)} CINs from database.")
        except Exception as e:
            log_info(f"[ERROR] Failed to query CINs: {e}")
            cins = []
        finally:
            cur.close()
            conn.close()
    else:
        cins = []
    
    if cins:
        trigger_refresh(cins, "CIN")
        log_info("[WAIT] Waiting 5 minutes for CIN data to propagate in Falconebiz...")
        time.sleep(300)
        run_sync_script("sync_company_registry.py")
    else:
        log_info("No CINs found to sync.")

    overall_elapsed = time.time() - overall_start
    print("\n" + "="*60)
    log_info(f"FULL REGISTRY REFRESH COMPLETED (Total Time: {overall_elapsed/60:.1f} minutes)")
    print("="*60)

if __name__ == "__main__":
    main()
