import os
import sys
import time
import requests
import psycopg2
from dotenv import load_dotenv
import subprocess
import urllib3

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
        print(f"[ERROR] DB connection failed: {e}")
        return None

def trigger_refresh(items, type="DIN"):
    print(f"\n[PHASE 1] Triggering MCA Updates for {len(items)} {type}s...")
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
        except:
            print(f"  [{idx}/{len(items)}] {item}: FAILED", end="\r")
        
        # Rate limit safety
        time.sleep(0.1)
    
    print(f"\n[DONE] Triggered {success_count} updates successfully.")

def run_sync_script(script_name):
    print(f"\n[PHASE 3] Starting Sync: {script_name}...")
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    try:
        subprocess.run([sys.executable, script_path, "--all"], check=True)
        print(f"\n[SUCCESS] Completed {script_name}")
    except Exception as e:
        print(f"\n[ERROR] Sync failed for {script_name}: {e}")

def main():
    conn = get_db_connection()
    if not conn: return
    
    cur = conn.cursor()
    
    # 1. Handle DINs
    cur.execute("SELECT din FROM directors_master.directors WHERE din IS NOT NULL")
    dins = [r[0] for r in cur.fetchall()]
    
    if dins:
        trigger_refresh(dins, "DIN")
        print(f"\n[WAIT] Waiting 2 minutes for DIN data to propagate in Falconebiz...")
        time.sleep(120)
        run_sync_script("sync_director_registry.py")
    
    # 2. Handle CINs
    cur.execute("SELECT cin FROM directors_data.companies WHERE cin IS NOT NULL")
    cins = [r[0] for r in cur.fetchall()]
    
    if cins:
        trigger_refresh(cins, "CIN")
        print(f"\n[WAIT] Waiting 5 minutes for CIN data to propagate in Falconebiz...")
        time.sleep(300)
        run_sync_script("sync_company_registry.py")

    cur.close()
    conn.close()
    print("\n" + "="*50)
    print("FULL REGISTRY REFRESH COMPLETED")
    print("="*50)

if __name__ == "__main__":
    main()
