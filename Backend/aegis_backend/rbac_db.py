import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def inspect_schema():
    db_name = os.getenv('POSTGRES_DATABASE_RBAC')
    host = os.getenv('POSTGRES_HOST')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    port = os.getenv('POSTGRES_PORT', '5432')
    sslmode = os.getenv('POSTGRES_SSLMODE', 'require')

    print(f"Connecting to {db_name}...")
    conn = psycopg2.connect(
        host=host,
        database=db_name,
        user=user,
        password=password,
        port=port,
        sslmode=sslmode
    )
    cur = conn.cursor()
    
    print("\n--- SCHEMA: rbac.route_definitions ---")
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'rbac' AND table_name = 'route_definitions'
    """)
    for row in cur.fetchall():
        print(f"Column: {row[0]} | Type: {row[1]} | Nullable: {row[2]}")
        
    conn.close()

if __name__ == "__main__":
    inspect_schema()
