import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

host     = os.getenv('DB_HOST')
user     = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_NAME')
port     = int(os.getenv('DB_PORT', 5432))

print(f"Connecting to {host}:{port}/{database}...")

conn_params = {
    'host': host, 'user': user, 'password': password,
    'port': port, 'database': database, 'connect_timeout': 15
}
if host and 'azure.com' in host.lower():
    conn_params['sslmode'] = 'require'

try:
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cur = conn.cursor()

    indexes = [
        ("idx_records_batch_company_depository_status", "CREATE INDEX IF NOT EXISTS idx_records_batch_company_depository_status ON shareholder_records(batch_id, company_id, depository_id, status)"),
        ("idx_records_batch_company", "CREATE INDEX IF NOT EXISTS idx_records_batch_company ON shareholder_records(batch_id, company_id)"),
        ("idx_records_status", "CREATE INDEX IF NOT EXISTS idx_records_status ON shareholder_records(status)"),
        ("idx_records_pagination", "CREATE INDEX IF NOT EXISTS idx_records_pagination ON shareholder_records(id)"),
        ("idx_summary_batch_company_depository", "CREATE INDEX IF NOT EXISTS idx_summary_batch_company_depository ON summary(batch_id, company_id, depository_id)"),
        ("idx_records_company_id", "CREATE INDEX IF NOT EXISTS idx_records_company_id ON shareholder_records(company_id)"),
        ("idx_records_batch_id", "CREATE INDEX IF NOT EXISTS idx_records_batch_id ON shareholder_records(batch_id)"),
        ("idx_records_depository_id", "CREATE INDEX IF NOT EXISTS idx_records_depository_id ON shareholder_records(depository_id)"),
        ("idx_summary_company_id", "CREATE INDEX IF NOT EXISTS idx_summary_company_id ON summary(company_id)"),
        ("idx_summary_batch_id", "CREATE INDEX IF NOT EXISTS idx_summary_batch_id ON summary(batch_id)"),
        ("idx_summary_depository_id", "CREATE INDEX IF NOT EXISTS idx_summary_depository_id ON summary(depository_id)"),
    ]

    for name, sql in indexes:
        try:
            print(f"  Creating {name}...", end=" ")
            cur.execute(sql)
            print("OK")
        except Exception as e:
            print(f"SKIP ({e})")

    print("\nRunning ANALYZE on all tables...")
    for table in ['companies', 'result_batches', 'depository_types', 'summary', 'shareholder_records']:
        try:
            cur.execute(f"ANALYZE {table}")
            print(f"  ANALYZE {table} OK")
        except Exception as e:
            print(f"  ANALYZE {table} SKIP ({e})")

    cur.close()
    conn.close()
    print("\nMIGRATION COMPLETE")

except Exception as e:
    print(f"\nFAILED: {e}")
