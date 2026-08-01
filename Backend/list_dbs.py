import psycopg2
import os
from dotenv import load_dotenv

# Load .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "aegis_backend", ".env"))

def list_dbs():
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    
    print(f"Checking for all databases on {host}:{port} as {user}...")
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            port=int(port),
            database='postgres', # connect to default
            connect_timeout=15
        )
        with conn.cursor() as cur:
            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            dbs = cur.fetchall()
            print("Databases found:")
            for db in dbs:
                print(f" - {db[0]}")
        conn.close()
    except Exception as e:
        print(f"❌ ERROR: Failed to list DBs: {e}")

if __name__ == "__main__":
    list_dbs()
