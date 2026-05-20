import os
import sys
import time
import requests
import psycopg2
import urllib3
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_KEY = "tgNuM80eYUxtV0TX!Aa3furfuUcg"
UPDATE_URL = "https://www.falconebiz.com/api/request_update"
PROXY = "http://cloudproxy.adani.com:8080"
PROXIES = {"http": PROXY, "https": PROXY}
MAX_WORKERS = 10

def get_db_connection():
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'aegis_backend', '.env'))
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
        print(f"Database connection error: {e}")
        return None

def trigger_refresh_for_cin(cin, idx, total, session):
    headers = {
        "Content-Type": "application/json",
        "Authorization": API_KEY,
        "Company": str(cin)
    }
    try:
        response = session.get(UPDATE_URL, headers=headers, timeout=20)
        if response.status_code == 200:
            print(f"[{idx:>4}/{total:>4}] Triggered refresh for CIN: {cin} -> Success")
            return True, cin, "Success"
        else:
            print(f"[{idx:>4}/{total:>4}] Triggered refresh for CIN: {cin} -> API Error {response.status_code}")
            return False, cin, f"HTTP {response.status_code}"
    except Exception as e:
        print(f"[{idx:>4}/{total:>4}] Triggered refresh for CIN: {cin} -> Exception: {e}")
        return False, cin, str(e)

def main():
    print("\n=== Aegis Batch Company MCA Refresh Tool ===")
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database. Make sure environment variables are correct.")
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT cin FROM directors_master.external_board_members
            WHERE cin IS NOT NULL AND cin != ''
        """)
        cins = [r[0] for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()

    total = len(cins)
    if total == 0:
        print("No CINs found in the database.")
        return

    print(f"Found {total} distinct CINs in the database.")
    confirm = input(f"Do you want to trigger MCA refresh for all {total} CINs? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return

    print(f"\nStarting refresh triggers with {MAX_WORKERS} workers...")
    
    session = requests.Session()
    session.proxies = PROXIES
    session.verify = False

    success_count = 0
    fail_count = 0

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(trigger_refresh_for_cin, cin, idx, total, session): cin
            for idx, cin in enumerate(cins, 1)
        }
        
        for future in as_completed(futures):
            success, cin, msg = future.result()
            if success:
                success_count += 1
            else:
                fail_count += 1

    session.close()
    elapsed = time.time() - start_time
    print("\n" + "="*50)
    print("REFRESH TRIGGER COMPLETED")
    print(f"Successfully Triggered: {success_count}")
    print(f"Failed to Trigger: {fail_count}")
    print(f"Total Attempted: {total}")
    print(f"Time Taken: {elapsed:.2f} seconds")
    print("="*50)
    print("\n[NOTE] MCA updates take approximately 2 to 5 minutes to process on the Falconebiz side.")
    print("Please wait 5 minutes before running the sync command (sync_company_registry.py) to fetch the latest updated data.")
    print("="*50)

if __name__ == "__main__":
    main()
