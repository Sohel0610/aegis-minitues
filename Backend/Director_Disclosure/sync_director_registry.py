import os
import requests
import json
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import time
import urllib3

# Suppress SSL warnings due to corporate proxy SSL interception
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load configuration from .env
# Assuming .env is in the parent backend folder
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'aegis_backend', '.env'))

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'dbname': os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
    'sslmode': 'require'
}

# API Configuration
API_KEY = "tgNuM80eYUxtV0TX!Aa3furfuUcg"
API_URL = "https://www.falconebiz.com/api/director_details"

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def initialize_schema():
    """Adds enrichment columns to master directors table and creates associations table."""
    conn = get_connection()
    cur = conn.cursor()
    
    print("Initializing Database Schema for Enrichment...")
    
    try:
        # 1. Add columns to directors_master.directors if they don't exist
        columns_to_add = [
            ("din_status", "VARCHAR(50)"),
            ("gender", "VARCHAR(20)"),
            ("nationality", "VARCHAR(50)"),
            ("dir3_kyc", "VARCHAR(50)"),
            ("approve_date", "DATE"),
            ("last_api_sync", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_type in columns_to_add:
            cur.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                                   WHERE TABLE_SCHEMA = 'directors_master' 
                                   AND TABLE_NAME = 'directors' 
                                   AND COLUMN_NAME = '{col_name}') THEN
                        ALTER TABLE directors_master.directors ADD COLUMN {col_name} {col_type};
                    END IF;
                END $$;
            """)
        
        # 2. Create external associations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS directors_master.external_associations (
                id SERIAL PRIMARY KEY,
                din VARCHAR(20) REFERENCES directors_master.directors(din) ON DELETE CASCADE,
                cin VARCHAR(30),
                company_name TEXT,
                designation VARCHAR(100),
                appointment_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(din, cin)
            );
        """)
        
        conn.commit()
        print("Schema update complete.")
    except Exception as e:
        conn.rollback()
        print(f"Error during schema update: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def fetch_director_registry(din):
    """Calls Falconebiz API for a specific DIN with proxy and SSL bypass."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": API_KEY,
        "Din": din
    }
    
    # Configure Adani Cloud Proxy
    proxies = {
        "http": "http://cloudproxy.adani.com:8080",
        "https": "http://cloudproxy.adani.com:8080"
    }
    
    try:
        # Note: verify=False is used to bypass corporate SSL interception issues
        response = requests.get(
            API_URL, 
            headers=headers, 
            proxies=proxies, 
            verify=False, 
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error for DIN {din}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception for DIN {din}: {e}")
        return None

def sync_all_directors():
    """Main loop to sync all directors from DB with the API."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    try:
        # ─── 0. Fetch the Adani Universe (Only sync associations for these CINs) ───
        cur.execute("SELECT cin FROM directors_data.companies")
        adani_universe = {r['cin'] for r in cur.fetchall()}
        print(f"  [UNIVERSE] Tracking associations for {len(adani_universe)} Adani companies.\n")

        # Get all directors who need sync
        cur.execute("SELECT din, name FROM directors_master.directors ORDER BY din")
        directors = cur.fetchall()
        
        total = len(directors)
        print(f"Found {total} directors to sync.")
        
        for i, director in enumerate(directors, 1):
            din = director['din']
            name = director['name']
            
            print(f"[{i}/{total}] Syncing: {name} (DIN: {din})...", end="\r")
            
            api_data = fetch_director_registry(din)
            if not api_data:
                continue
            
            # Safety Check: Ensure api_data is a dictionary
            if isinstance(api_data, list):
                if len(api_data) > 0:
                    api_data = api_data[0] # Grab first object if it's a list
                else:
                    continue
            
            if not isinstance(api_data, dict):
                print(f"Unexpected data format for DIN {din}: {type(api_data)}")
                continue
                
            # 1. Update Master Record
            indian_raw = (api_data.get('indian') or "").upper()
            nationality = 'Indian' if indian_raw in ['Y', 'YES'] else 'External'
            
            cur.execute("""
                UPDATE directors_master.directors
                SET din_status = %s,
                    gender = %s,
                    nationality = %s,
                    dir3_kyc = %s,
                    approve_date = %s,
                    last_api_sync = CURRENT_TIMESTAMP
                WHERE din = %s
            """, (
                api_data.get('din_status'),
                api_data.get('gender'),
                nationality,
                api_data.get('dir3_kyc'),
                api_data.get('approve_date') if api_data.get('approve_date') != 'N/A' else None,
                din
            ))
            
            # 2. Sync Associations
            associations = api_data.get('association', [])
            for assoc in associations:
                cin = assoc.get('cin')
                if not cin or cin == 'N/A': continue
                
                # Filter: Only allow companies from our Adani universe
                if cin not in adani_universe:
                    continue
                
                cur.execute("""
                    INSERT INTO directors_master.external_associations 
                    (din, cin, company_name, designation, appointment_date)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (din, cin) DO UPDATE SET
                        company_name = EXCLUDED.company_name,
                        designation = EXCLUDED.designation,
                        appointment_date = EXCLUDED.appointment_date
                """, (
                    din,
                    cin,
                    assoc.get('com_name'),
                    assoc.get('designation'),
                    assoc.get('appointment') if assoc.get('appointment') != 'N/A' else None
                ))
            
            # Commit every 10 records to avoid long-running transaction loss
            if i % 10 == 0:
                conn.commit()
                
        conn.commit()
        print(f"\nSuccessfully synced {total} directors with Registry data.")
        
    except Exception as e:
        conn.rollback()
        print(f"\nCritical error during sync: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # Ensure tables are ready
    initialize_schema()
    
    # Run the sync
    sync_all_directors()
