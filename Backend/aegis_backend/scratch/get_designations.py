import os
import sys

# Add parent directory to path to find utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.pgsql_service import get_pg_connection
    from dotenv import load_dotenv
    
    # Load .env from the aegis_backend directory
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    
    def get_unique_designations():
        conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_DIRECTOR'))
        if not conn:
            print("Failed to connect to database.")
            return

        try:
            cursor = conn.cursor()
            query = "SELECT DISTINCT designation FROM directors_master.external_board_members WHERE designation IS NOT NULL AND designation != '' ORDER BY designation"
            cursor.execute(query)
            designations = cursor.fetchall()
            
            print("\n" + "="*50)
            print(f"UNIQUE DESIGNATIONS IN DATABASE ({len(designations)} found)")
            print("="*50)
            for i, (desig,) in enumerate(designations, 1):
                print(f"{i}. {desig}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"Error executing query: {e}")
        finally:
            conn.close()

    if __name__ == "__main__":
        get_unique_designations()

except ImportError as e:
    print(f"Import error: {e}. Make sure you are running from the Backend/aegis_backend directory or have PYTHONPATH set.")
