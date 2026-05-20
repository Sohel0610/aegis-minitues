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
FETCH_CIN_URL = "https://www.falconebiz.com/api/company_details"
UPDATE_CIN_URL = "https://www.falconebiz.com/api/request_update"

CIN = "U35105GJ2025PLC167975"  # Default Adani Green Energy Limited CIN

# Adani Cloud Proxy
PROXIES = {
    "http": "http://cloudproxy.adani.com:8080",
    "https": "http://cloudproxy.adani.com:8080"
}

def get_db_connection():
    # Assuming .env is in the parent backend folder (aegis_backend)
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

def clean_numeric(val):
    if val is None: return None
    s = str(val).strip().replace(',', '').replace('₹', '')
    if not s or s.lower() in ['n/a', 'null', 'none', '-']: return None
    try:
        if '.' in s: return float(s)
        return int(s)
    except: return None

def sync_company_details(cin):
    print(f"\n[STEP 1] Fetching company details from API for CIN: {cin}...")
    headers = {
        "Content-Type": "application/json", 
        "Authorization": API_KEY, 
        "Company": cin, 
        "Domain": DOMAIN
    }
    resp = fetch_raw(FETCH_CIN_URL, headers)
    
    if not resp or resp.status_code != 200:
        print("Failed to fetch company details from API.")
        return

    data = resp.json()
    details = data.get('company_details', {})
    if not details or not details.get('cin'):
        print("Empty or invalid company response from API.")
        return

    company_name = details.get('company_name', 'Unknown')
    print(f"Successfully retrieved details for: {company_name}")

    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()

        # 1. Upsert company record
        print("\n[STEP 2] Upserting company details into directors_data.companies...")
        cur.execute("""
            INSERT INTO directors_data.companies (
                cin, name, status, incorporation_date, auth_capital, paid_capital,
                pincode, category, class, roc, subcategory, state, district,
                activity, last_agm, last_bal_sheet, email, address, list_status, 
                last_mca_updated, last_sync
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)
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
                last_mca_updated=EXCLUDED.last_mca_updated,
                last_sync=CURRENT_TIMESTAMP
        """, (
            cin, company_name, details.get('statusname'),
            details.get('incorporation_date'), 
            clean_numeric(details.get('auth_capital')),
            clean_numeric(details.get('paid_capital')), 
            details.get('pincode'),
            details.get('category'), details.get('class'), details.get('roc'),
            details.get('subcategory'), details.get('state'), details.get('district'),
            details.get('activity'), data.get('filings', {}).get('last_agm'), data.get('filings', {}).get('last_bal_sheet'),
            data.get('contact_details', {}).get('email'), data.get('contact_details', {}).get('address'), details.get('list_status'),
            details.get('last_updated')
        ))

        # 2. Sync Board Members
        directors_list = data.get('directors', [])
        print(f"\n[STEP 3] Syncing {len(directors_list)} board members...")
        
        # Get existing directors in DB for this CIN to identify resignations
        cur.execute("SELECT din FROM directors_master.external_board_members WHERE cin = %s", (cin,))
        existing_dins = {r[0] for r in cur.fetchall()}
        incoming_dins = set()

        for d in directors_list:
            din = str(d.get('din'))
            name = d.get('director_name')
            desig = d.get('designation')
            appt = d.get('appointment_date')
            if not din: continue
            
            incoming_dins.add(din)
            print(f"  - Active Director: {name} (DIN: {din})")

            cur.execute("""
                INSERT INTO directors_master.external_board_members
                    (din, name, cin, company_name, designation, appointment_date, status)
                VALUES (%s,%s,%s,%s,%s,%s,'Active')
                ON CONFLICT (din, cin) DO UPDATE SET
                    name=EXCLUDED.name, company_name=EXCLUDED.company_name,
                    designation=EXCLUDED.designation, appointment_date=EXCLUDED.appointment_date,
                    status='Active'
            """, (din, name, cin, company_name, desig, appt))

        # Mark resigned directors
        resigned_dins = existing_dins - incoming_dins
        for r_din in resigned_dins:
            print(f"  - Resigned Director: DIN {r_din}")
            cur.execute("""
                UPDATE directors_master.external_board_members 
                SET status = 'Resigned' 
                WHERE din = %s AND cin = %s AND status != 'Resigned'
            """, (r_din, cin))

        # 3. Sync Company Charges
        charges = data.get('charges_borrowings') or data.get('charges') or []
        print(f"\n[STEP 4] Syncing {len(charges)} company charges/borrowings...")
        cur.execute("DELETE FROM directors_data.company_charges WHERE cin = %s", (cin,))
        
        for chg in charges:
            raw_amt = chg.get('amount') or chg.get('amount_charge') or chg.get('charge_amount') or chg.get('charge_amt')
            ch_id = chg.get('chargeid') or chg.get('charge_id') or chg.get('id')
            holder = chg.get('charge_holder') or chg.get('holder') or chg.get('bank_name')
            
            amt_str = str(raw_amt) if raw_amt is not None and str(raw_amt).strip() != "" else "0"
            
            cur.execute("""
                INSERT INTO directors_data.company_charges
                    (cin, charge_id, amount, holder, creation_date, closure_date)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (cin, ch_id, amt_str, holder, chg.get('creation_date'), chg.get('closure_date')))

        conn.commit()
        print("\n" + "="*50)
        print(f"SYNC COMPLETE FOR COMPANY: {company_name} ({cin})")
        print(f"Total Directors Processed: {len(directors_list)}")
        print(f"Total Charges Processed: {len(charges)}")
        print("="*50)
        
    except Exception as e:
        conn.rollback()
        print(f"Database update error: {e}")
    finally:
        cur.close()
        conn.close()

def main():
    print("\n--- Advanced Company Verification Tool ---")
    print(f"Default CIN: {CIN}")
    print("-" * 30)
    print("Select Action:")
    print("[1] Update API (Trigger MCA Refresh for CIN)")
    print("[2] Fetch API (Show Raw Company Response)")
    print("[3] Sync Company details to Database")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    target_cin = input(f"Enter target CIN (Press enter for default '{CIN}'): ").strip()
    if not target_cin:
        target_cin = CIN

    if choice == '1':
        headers = {
            "Content-Type": "application/json", 
            "Authorization": API_KEY, 
            "Company": target_cin
        }
        resp = fetch_raw(UPDATE_CIN_URL, headers)
        if resp:
            print(f"Status: {resp.status_code}\nResponse: {resp.text}")
        else:
            print("Failed to reach update API.")
    elif choice == '2':
        headers = {
            "Content-Type": "application/json", 
            "Authorization": API_KEY, 
            "Company": target_cin, 
            "Domain": DOMAIN
        }
        resp = fetch_raw(FETCH_CIN_URL, headers)
        if resp:
            print(f"Status: {resp.status_code}\nHeaders: {resp.headers}\nBody: {resp.text}")
        else:
            print("Failed to reach fetch API.")
    elif choice == '3':
        sync_company_details(target_cin)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
