import time
import os
import sys

# Add the parent directory to Python path so we can import from utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.pgsql_service import get_pg_connection

def build_indexes():
    print("==================================================")
    print("   Starting Production Index Build Process")
    print("==================================================")
    print("Connecting to database...")
    
    conn_proxy = get_pg_connection()
    if not conn_proxy:
        print("Failed to get database connection from utils.pgsql_service")
        sys.exit(1)
        
    # Get the raw psycopg2 connection object from the proxy to set autocommit
    conn = conn_proxy._conn
    conn.autocommit = True
    cur = conn.cursor()
    
    indexes_to_build = [
        {
            "name": "idx_sr_pangir",
            "desc": "B-Tree on shareholder_records (pangir) for fast PAN lookup",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sr_pangir ON public.shareholder_records (pangir);"
        },
        {
            "name": "idx_sr_name_lower",
            "desc": "B-Tree on shareholder_records (lower(name)) with varchar_pattern_ops for fast text prefix search",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sr_name_lower ON public.shareholder_records (lower(name) varchar_pattern_ops);"
        },
        {
            "name": "idx_sr_email_lower",
            "desc": "B-Tree on shareholder_records (lower(email)) with varchar_pattern_ops for fast text prefix search",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sr_email_lower ON public.shareholder_records (lower(email) varchar_pattern_ops);"
        },
        {
            "name": "idx_ccv_pancard",
            "desc": "B-Tree on compliance_cache_violations (pan_card) for fast PAN lookup",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ccv_pancard ON public.compliance_cache_violations (pan_card);"
        },
        {
            "name": "idx_ccv_name_lower",
            "desc": "B-Tree on compliance_cache_violations (lower(declared_name)) for fast text search",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ccv_name_lower ON public.compliance_cache_violations (lower(declared_name) varchar_pattern_ops);"
        },
        {
            "name": "idx_ccv_email_lower",
            "desc": "B-Tree on compliance_cache_violations (lower(email)) for fast text search",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ccv_email_lower ON public.compliance_cache_violations (lower(email) varchar_pattern_ops);"
        },
        {
            "name": "idx_sr_perf_filters",
            "desc": "Composite Covering Index for Analytics and Master Data filtering",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sr_perf_filters ON public.shareholder_records (company_id, batch_id, depository_id, status, id);"
        }
    ]
    
    print("==================================================")
    print("   Starting Production Index Build Process")
    print("==================================================")
    print("Building indexes concurrently. This does not lock the table")
    print("so the application can continue running normally.\n")
    
    total_start = time.time()
    for idx in indexes_to_build:
        print(f"--> Building {idx['name']}...")
        print(f"    ({idx['desc']})")
        start = time.time()
        try:
            cur.execute(idx['sql'])
            print(f"    [OK] Built in {time.time() - start:.2f} seconds\n")
        except Exception as e:
            print(f"    [FAILED] Error: {e}\n")
    
    print("==================================================")
    print(f"   Finished in {time.time() - total_start:.2f} seconds total!")
    print("   Your production database is now fully optimized.")
    print("==================================================")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    build_indexes()
