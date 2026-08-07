import os
import psycopg2

# Hardcoded Azure Credentials for direct verification
DB_CONFIG = {
    'host': "az10psqldmrcbtp01.postgres.database.azure.com",
    'port': "5432",
    'user': "psqladmin",
    'password': "1k8h02grUu+qJ2uHZb<{lB3LF%+Yj-Ar",
    'dbname': "director_disclosure_system",
    'sslmode': 'require'
}

def check_db():
    print(f"Connecting DIRECTLY to Azure: {DB_CONFIG['host']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Total Directors Enriched
        cur.execute("SELECT count(*) FROM directors_master.directors WHERE din_status IS NOT NULL")
        enriched_count = cur.fetchone()[0]
        
        # 2. Total Associations
        cur.execute("SELECT count(*) FROM directors_master.external_associations")
        assoc_count = cur.fetchone()[0]
        
        # 3. Sample Data
        cur.execute("SELECT name, din_status, gender, last_api_sync FROM directors_master.directors WHERE last_api_sync IS NOT NULL LIMIT 3")
        samples = cur.fetchall()
        
        print("\n" + "="*40)
        print("   AZURE CLOUD DATA VERIFICATION (DIRECT)")
        print("="*40)
        print(f"Database: {DB_CONFIG['dbname']}")
        print(f"Status:   CONNECTED")
        print(f"Total Enriched Directors: {enriched_count}")
        print(f"Total Associations Found: {assoc_count}")
        print("-" * 40)
        print("SAMPLE DATA FROM AZURE:")
        for s in samples:
            print(f" Director: {s[0]}")
            print(f" Status:   {s[1]}")
            print(f" Gender:   {s[2]}")
            print(f" Synced:   {s[3]}")
            print("-" * 20)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"\nFATAL DATABASE ERROR: {e}")

if __name__ == "__main__":
    check_db()
