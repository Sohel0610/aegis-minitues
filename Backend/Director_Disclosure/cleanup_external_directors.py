import os
import psycopg2
from dotenv import load_dotenv

# Load configuration from .env
env_path = os.path.join(os.path.dirname(__file__), '..', 'aegis_backend', '.env')
load_dotenv(env_path)

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
        print(f"Error: {e}")
        return None

def cleanup_directors():
    conn = get_db_connection()
    if not conn: return
    
    try:
        cur = conn.cursor()
        
        print("Starting cleanup of non-Adani directors...")
        
        # 1. Count before
        cur.execute("SELECT COUNT(*) FROM directors_master.directors")
        before_count = cur.fetchone()[0]
        
        # 2. Delete directors who have NO Adani associations 
        # (either in the registry external associations or in our primary directorships table)
        cur.execute("""
            DELETE FROM directors_master.directors
            WHERE din NOT IN (
                SELECT DISTINCT din FROM directors_master.external_associations
            )
            AND din NOT IN (
                SELECT DISTINCT din FROM directors_data.directorships
            )
        """)
        
        deleted_count = cur.rowcount
        conn.commit()
        
        # 3. Count after
        cur.execute("SELECT COUNT(*) FROM directors_master.directors")
        after_count = cur.fetchone()[0]
        
        print(f"Cleanup complete.")
        print(f"  - Total directors before: {before_count}")
        print(f"  - Removed (non-Adani):    {deleted_count}")
        print(f"  - Adani directors kept:   {after_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_directors()
