import os
import psycopg2
from dotenv import load_dotenv

# Load configuration from .env
env_path = os.path.join(os.path.dirname(__file__), '..', 'aegis_backend', '.env')
load_dotenv(env_path)

def backfill_status():
    """
    Backfills the 'status' column in external_board_members 
    using data from the companies master table.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
            sslmode='require'
        )
        cur = conn.cursor()

        print("\n[DB] Starting backfill of company statuses...")

        # Update query: Sync status from companies -> external_board_members
        update_query = """
            UPDATE directors_master.external_board_members ea
            SET status = c.status
            FROM directors_data.companies c
            WHERE ea.cin = c.cin 
            AND (ea.status IS NULL OR ea.status = 'None' OR ea.status = '');
        """
        
        cur.execute(update_query)
        updated_count = cur.rowcount
        conn.commit()

        print(f"[DB] SUCCESS: Updated {updated_count} rows in external_board_members.")
        
        cur.close()
    except Exception as e:
        print(f"[DB ERROR] Backfill failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    backfill_status()
