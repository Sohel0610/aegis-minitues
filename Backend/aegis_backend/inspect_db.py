import os
from dotenv import load_dotenv
from utils.pgsql_service import get_pg_connection, get_pg_cursor

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

def inspect_postgresql():
    """Audit every database mentioned in the .env and summarize tables."""
    
    # Identify all database variables in .env
    db_env_vars = [
        'POSTGRES_DATABASE',
        'POSTGRES_DATABASE_DIRECTOR',
        'POSTGRES_DATABASE_BSE',
        'POSTGRES_DATABASE_RBI',
        'POSTGRES_DATABASE_SEBI',
        'POSTGRES_DATABASE_VISITS',
        'POSTGRES_DATABASE_RBAC',
        'POSTGRES_DATABASE_MINUTES',
        'POSTGRES_DATABASE_INSIDER'
    ]
    
    # Unique database names
    target_dbs = {os.getenv(var) for var in db_env_vars if os.getenv(var)}
    
    print("\n" + "="*60)
    print("      AEGIS PLATFORM - POSTGRESQL INSTANCE INSPECTOR")
    print("="*60)
    print(f"Server: {os.getenv('POSTGRES_HOST')}\n")
    
    for db_name in sorted(target_dbs):
        print(f"\nAUDITING DATABASE: [{db_name}]")
        print("-" * 30)
        
        conn = get_pg_connection(db_name)
        if not conn:
            print(f"  ❌ FAILED: Database [{db_name}] does not exist or access denied.")
            continue
            
        try:
            cursor = get_pg_cursor(conn)
            # Query all user-defined tables and their schemas
            cursor.execute("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog') 
                ORDER BY table_schema, table_name
            """)
            
            rows = cursor.fetchall()
            if not rows:
                print("  ⚠️  Database is EMPTY (no user tables found).")
            else:
                current_schema = None
                for row in rows:
                    schema = row['table_schema']
                    table = row['table_name']
                    
                    if schema != current_schema:
                        print(f"  📂 Schema: {schema}")
                        current_schema = schema
                    print(f"     └─ {table}")
                    
        except Exception as e:
            print(f"  ❌ Error reading tables from {db_name}: {e}")
        finally:
            conn.close()

    print("\n" + "="*60)
    print("                INSPECTION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    inspect_postgresql()
