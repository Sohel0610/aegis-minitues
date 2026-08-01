#rescue_data.py

import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# Load credentials from .env
env_path = os.path.join(os.path.dirname(__file__), "aegis_backend", ".env")
load_dotenv(dotenv_path=env_path)

def rescue_document_summaries():
    # 1. Local SQLite connection
    sqlite_path = 'aegis_backend/directors_data.db'
    if not os.path.exists(sqlite_path):
        print(f"Error: {sqlite_path} not found.")
        return
        
    sconn = sqlite3.connect(sqlite_path)
    sconn.row_factory = sqlite3.Row
    scursor = sconn.cursor()
    
    # Check what we have locally
    scursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_summaries'")
    if not scursor.fetchone():
        print("Error: Table 'document_summaries' does not exist in SQLite.")
        return
        
    scursor.execute("SELECT count(*) FROM document_summaries")
    total_local = scursor.fetchone()[0]
    print(f"Total records found locally in SQLite: {total_local}")

    # 2. Azure PG connection
    pconn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DATABASE_DIRECTOR')
    )
    pcursor = pconn.cursor()
    
    # 3. Force Migration using UPSERT (Update if conflict)
    print("Moving data to Azure (Force Overwrite)...")
    scursor.execute("SELECT * FROM document_summaries")
    rows = scursor.fetchall()
    
    count = 0
    for r in rows:
        try:
            # We use ON CONFLICT (file_path) DO UPDATE to ensure we don't duplicate but we DO overwrite
            pcursor.execute("""
                INSERT INTO directors_data.document_summaries 
                (director_name, din, file_path, full_text, summary)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (file_path) DO UPDATE SET
                    director_name = EXCLUDED.director_name,
                    din = EXCLUDED.din,
                    full_text = EXCLUDED.full_text,
                    summary = EXCLUDED.summary,
                    updated_at = CURRENT_TIMESTAMP
            """, (r['director_name'], r['din'], r['file_path'], r['full_text'], r['summary']))
            count += 1
        except Exception as e:
            print(f"Failed to migrate record {r['director_name']}: {e}")
            
    pconn.commit()
    print(f"Successfully migrated {count} records to Azure.")
    
    sconn.close()
    pconn.close()

if __name__ == "__main__":
    rescue_document_summaries()
