import os
import psycopg2
from dotenv import load_dotenv

# Search for .env in current and parent directories
env_paths = [
    'aegis_backend/.env',
    '.env',
    '../aegis_backend/.env',
    'Backend/aegis_backend/.env'
]
for path in env_paths:
    if os.path.exists(path):
        load_dotenv(path)
        break

def setup_flag():
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
            sslmode='require'
        )
        cur = conn.cursor()
        
        print("[DB] Adding 'is_adani' column to directors_data.companies...")
        cur.execute("ALTER TABLE directors_data.companies ADD COLUMN IF NOT EXISTS is_adani BOOLEAN DEFAULT TRUE")
        
        print("[DB] Marking Tata Steel (L74899DL1983PLC014942) as non-Adani...")
        cur.execute("UPDATE directors_data.companies SET is_adani = FALSE WHERE cin = 'L74899DL1983PLC014942'")
        
        conn.commit()
        print("[DB] SUCCESS: Database schema updated.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Setup failed: {e}")

if __name__ == "__main__":
    setup_flag()
