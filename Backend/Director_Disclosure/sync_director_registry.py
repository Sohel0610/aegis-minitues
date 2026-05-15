import os
import requests
import json
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "sync_progress_din.json")

def report_progress(current, total, status="Syncing..."):
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump({"current": current, "total": total, "status": status, "timestamp": time.time()}, f)
    except:
        pass

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
            ("last_api_sync", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("last_mca_updated", "TIMESTAMP")
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
        
        # 2. Create external associations table (Standardized to external_board_members for UI)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS directors_master.external_board_members (
                id SERIAL PRIMARY KEY,
                din VARCHAR(20) REFERENCES directors_master.directors(din) ON DELETE CASCADE,
                cin VARCHAR(30),
                company_name TEXT,
                designation VARCHAR(100),
                appointment_date DATE,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(din, cin)
            );
        """)
        
        # 3. Migrate legacy data if exists
        cur.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'directors_master' AND TABLE_NAME = 'external_associations') THEN
                    INSERT INTO directors_master.external_board_members (din, cin, company_name, designation, appointment_date)
                    SELECT din, cin, company_name, designation, appointment_date 
                    FROM directors_master.external_associations
                    ON CONFLICT (din, cin) DO NOTHING;
                    
                    -- Optional: Drop the old table after migration
                    -- DROP TABLE directors_master.external_associations;
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("Schema update and data migration complete.")
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

def sync_worker(director, adani_universe, session, idx, total, stats_lock, stats):
    """Worker function for threading: Syncs a single director."""
    din = director['din']
    name = director['name']
    
    api_data = fetch_director_registry(din)
    if not api_data:
        return False
        
    # Safety Check: Ensure api_data is a dictionary
    if isinstance(api_data, list):
        if len(api_data) > 0:
            api_data = api_data[0]
        else:
            return False
            
    if not isinstance(api_data, dict):
        return False
            
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Upsert Master Record
        indian_raw = (api_data.get('indian') or "").upper()
        nationality = 'Indian' if indian_raw in ['Y', 'YES'] else 'External'
        
        cur.execute("""
            INSERT INTO directors_master.directors 
            (din, name, din_status, gender, nationality, dir3_kyc, approve_date, last_mca_updated, last_api_sync)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (din) DO UPDATE SET
                name = EXCLUDED.name,
                din_status = EXCLUDED.din_status,
                gender = EXCLUDED.gender,
                nationality = EXCLUDED.nationality,
                dir3_kyc = EXCLUDED.dir3_kyc,
                approve_date = EXCLUDED.approve_date,
                last_mca_updated = EXCLUDED.last_mca_updated,
                last_api_sync = CURRENT_TIMESTAMP
        """, (
            din,
            api_data.get('name') or name,
            api_data.get('din_status'),
            api_data.get('gender'),
            nationality,
            api_data.get('dir3_kyc'),
            api_data.get('approve_date') if api_data.get('approve_date') != 'N/A' else None,
            api_data.get('updated_at')
        ))
        
        # 2. Sync Associations
        associations = api_data.get('association', [])
        for assoc in associations:
            cin = assoc.get('cin')
            com_name = assoc.get('com_name', 'Unknown')
            if not cin or cin == 'N/A': continue
            
            # Use a conditional update for status: 
            # If the current status is 'Resigned', don't let the (potentially stale) 
            # Director API overwrite it back to 'Active' unless it's a very fresh update.
            cur.execute("""
                INSERT INTO directors_master.external_board_members 
                (din, cin, company_name, designation, appointment_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (din, cin) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    designation = EXCLUDED.designation,
                    appointment_date = EXCLUDED.appointment_date,
                    status = CASE 
                        WHEN directors_master.external_board_members.status = 'Resigned' THEN 'Resigned'
                        ELSE EXCLUDED.status 
                    END
            """, (
                din, cin, com_name, assoc.get('designation'),
                assoc.get('appointment') if assoc.get('appointment') != 'N/A' else None,
                assoc.get('status', 'Active')
            ))
        
        conn.commit()
        with stats_lock:
            stats['count'] += 1
            report_progress(stats['count'], total, f"Syncing {name}")
            print(f"  [{stats['count']}/{total}] Synced: {name} (DIN: {din})", end="\r")
        return True
    except Exception as e:
        conn.rollback()
        print(f"\nError syncing DIN {din}: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def sync_all_directors(max_workers=15):
    """Multi-threaded sync for all directors."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    try:
        # 0. Fetch the Adani Universe
        cur.execute("SELECT cin FROM directors_data.companies")
        adani_universe = {r['cin'] for r in cur.fetchall()}
        
        # Get all directors
        cur.execute("SELECT din, name FROM directors_master.directors ORDER BY din")
        directors = cur.fetchall()
        cur.close()
        conn.close()
        
        total = len(directors)
        print(f"\n[START] Starting Multi-threaded Sync for {total} directors (Workers: {max_workers})...\n")
        
        stats = {'count': 0}
        stats_lock = threading.Lock()
        
        # Use a single session with proxy pre-configured
        session = requests.Session()
        session.proxies = {
            "http": "http://cloudproxy.adani.com:8080",
            "https": "http://cloudproxy.adani.com:8080"
        }
        session.verify = False
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(sync_worker, d, adani_universe, session, i, total, stats_lock, stats)
                for i, d in enumerate(directors, 1)
            ]
            for future in as_completed(futures):
                future.result() # Wait for all to complete
                
        elapsed = time.time() - start_time
        report_progress(total, total, "Complete")
        print(f"\n\n[SUCCESS] Successfully synced {total} directors in {elapsed:.1f} seconds.")
        
    except Exception as e:
        print(f"\nCritical error during batch sync: {e}")

if __name__ == "__main__":
    import sys
    # Ensure tables are ready
    initialize_schema()
    
    if len(sys.argv) > 1:
        din = sys.argv[1]
        if din == "--all":
            sync_all_directors()
        else:
            # Sync single director
            # Need a single-director sync wrapper or just call the logic for one
            # Refactoring slightly for single sync
            print(f"Syncing single director: {din}")
            conn = get_connection()
            cur = conn.cursor(cursor_factory=extras.RealDictCursor)
            try:
                # Get the director name first
                cur.execute("SELECT name FROM directors_master.directors WHERE din = %s", (din,))
                res = cur.fetchone()
                name = res['name'] if res else "Unknown"
                
                # Use existing logic flow
                cur.execute("SELECT cin FROM directors_data.companies")
                adani_universe = {r['cin'] for r in cur.fetchall()}
                
                api_data = fetch_director_registry(din)
                if api_data:
                    if isinstance(api_data, list) and len(api_data) > 0: api_data = api_data[0]
                    if isinstance(api_data, dict):
                        # 1. Update Master
                        indian_raw = (api_data.get('indian') or "").upper()
                        nationality = 'Indian' if indian_raw in ['Y', 'YES'] else 'External'
                        # 1. Upsert Master
                        cur.execute("""
                            INSERT INTO directors_master.directors 
                            (din, name, din_status, gender, nationality, dir3_kyc, approve_date, last_mca_updated, last_api_sync)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (din) DO UPDATE SET
                                name = EXCLUDED.name,
                                din_status = EXCLUDED.din_status,
                                gender = EXCLUDED.gender,
                                nationality = EXCLUDED.nationality,
                                dir3_kyc = EXCLUDED.dir3_kyc,
                                approve_date = EXCLUDED.approve_date,
                                last_mca_updated = EXCLUDED.last_mca_updated,
                                last_api_sync = CURRENT_TIMESTAMP
                        """, (
                            din,
                            api_data.get('name') or name,
                            api_data.get('din_status'),
                            api_data.get('gender'),
                            nationality,
                            api_data.get('dir3_kyc'),
                            api_data.get('approve_date') if api_data.get('approve_date') != 'N/A' else None,
                            api_data.get('updated_at')
                        ))
                        
                        # 2. Sync Associations
                        associations = api_data.get('association', [])
                        for assoc in associations:
                            cin = assoc.get('cin')
                            com_name = assoc.get('com_name', 'Unknown')
                            if not cin or cin == 'N/A': continue
                            is_adani = "ADANI" in com_name.upper()
                            
                            cur.execute("""
                                INSERT INTO directors_master.external_board_members 
                                (din, cin, company_name, designation, appointment_date, status)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (din, cin) DO UPDATE SET
                                    company_name = EXCLUDED.company_name,
                                    designation = EXCLUDED.designation,
                                    appointment_date = EXCLUDED.appointment_date,
                                    status = CASE 
                                        WHEN directors_master.external_board_members.status = 'Resigned' THEN 'Resigned'
                                        ELSE EXCLUDED.status 
                                    END
                            """, (din, cin, com_name, assoc.get('designation'),
                                assoc.get('appointment') if assoc.get('appointment') != 'N/A' else None,
                                assoc.get('status', 'Active')))
                        conn.commit()
                        print(f"Successfully synced DIN {din}")
            finally:
                cur.close()
                conn.close()
    else:
        # Default behavior: sync all
        sync_all_directors()
