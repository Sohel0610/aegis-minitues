import requests
import json
import urllib3
import sys
import time
import os
import psycopg2
from dotenv import load_dotenv

# Suppress SSL warnings for corporate proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_KEY = "tgNuM80eYUxtV0TX!Aa3furfuUcg"
DOMAIN = "adani.com"
FETCH_DIN_URL = "https://www.falconebiz.com/api/director_details"
UPDATE_DIN_URL = "https://www.falconebiz.com/api/request_update"
FETCH_CIN_URL = "https://www.falconebiz.com/api/company_details"

DIN = "11284690"

# Adani Cloud Proxy
PROXIES = {
    "http": "http://cloudproxy.adani.com:8080",
    "https": "http://cloudproxy.adani.com:8080"
}

def get_db_connection():
    # Assuming .env is in the parent backend folder
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

def fetch_raw(url, headers):
    try:
        response = requests.get(url, headers=headers, proxies=PROXIES, verify=False, timeout=30)
        return response
    except Exception as e:
        print(f"API Error: {e}")
        return None

def verify_and_update_associations(din):
    print(f"\n[STEP 1] Fetching associations from Director API for DIN: {din}...")
    headers = {"Content-Type": "application/json", "Authorization": API_KEY, "Din": din}
    resp = fetch_raw(FETCH_DIN_URL, headers)
    
    if not resp or resp.status_code != 200:
        print("Failed to fetch director details.")
        return

    data = resp.json()
    associations = data.get('association', [])
    print(f"Found {len(associations)} potential associations in Director Registry.")

    conn = get_db_connection()
    if not conn: return
    cur = conn.cursor()

    verified_count = 0
    resigned_count = 0

    for idx, assoc in enumerate(associations, 1):
        cin = assoc.get('cin')
        com_name = assoc.get('com_name')
        if not cin: continue

        print(f"\n[{idx}/{len(associations)}] Verifying CIN: {cin} ({com_name})...")
        
        # Call Company API to see current directors
        cin_headers = {
            "Content-Type": "application/json", 
            "Authorization": API_KEY, 
            "Company": cin, 
            "Domain": DOMAIN
        }
        c_resp = fetch_raw(FETCH_CIN_URL, cin_headers)
        
        if c_resp and c_resp.status_code == 200:
            c_data = c_resp.json()
            current_directors = [str(d.get('din')) for d in c_data.get('directors', [])]
            
            if din in current_directors:
                print(f"  √ VERIFIED: Director is ACTIVE in this company.")
                status = "Active"
                verified_count += 1
            else:
                print(f"  × RESIGNED: Director NOT found in company's current director list.")
                status = "Resigned"
                resigned_count += 1
            
            # Update Database
            cur.execute("""
                INSERT INTO directors_master.external_board_members 
                (din, cin, company_name, designation, appointment_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (din, cin) DO UPDATE SET
                    status = EXCLUDED.status,
                    company_name = EXCLUDED.company_name
            """, (din, cin, com_name, assoc.get('designation'), assoc.get('appointment'), status))
            conn.commit()
        else:
            print(f"  ! Skip: Could not fetch company details for {cin}")

    print("\n" + "="*50)
    print(f"SYNC COMPLETE FOR DIN: {din}")
    print(f"Verified Active: {verified_count}")
    print(f"Marked Resigned: {resigned_count}")
    print("="*50)
    
    cur.close()
    conn.close()

def main():
    print("\n--- Advanced Director Verification Tool ---")
    print(f"Target DIN: {DIN}")
    print("-" * 30)
    print("Select Action:")
    print("[1] Update API (Trigger MCA Refresh for DIN)")
    print("[2] Fetch API (Show Raw Director Response)")
    print("[3] Recursive Sync (Verify all associations via CIN API & Update DB)")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        headers = {"Content-Type": "application/json", "Authorization": API_KEY, "Din": DIN}
        resp = fetch_raw(UPDATE_DIN_URL, headers)
        print(f"Status: {resp.status_code}\nResponse: {resp.text}")
    elif choice == '2':
        headers = {"Content-Type": "application/json", "Authorization": API_KEY, "Din": DIN}
        resp = fetch_raw(FETCH_DIN_URL, headers)
        print(f"Status: {resp.status_code}\nHeaders: {resp.headers}\nBody: {resp.text}")
    elif choice == '3':
        verify_and_update_associations(DIN)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()