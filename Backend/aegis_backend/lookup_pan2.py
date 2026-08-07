import psycopg2
import pandas as pd
conn = psycopg2.connect('postgresql://postgres:postgres@192.168.0.56:5436/aegis_insider')

pan = 'AQRPG9761D'

# 1. Check in shareholder_records (BENPOS Master Data)
df_shareholder = pd.read_sql_query(f"SELECT id, pangir, name, company_id, batch_id, depository_id, position_latest, status FROM public.shareholder_records WHERE pangir = '{pan}'", conn)
print("=== SHAREHOLDER RECORDS (BENPOS Data) ===")
if df_shareholder.empty:
    print(f"No records found for PAN {pan}")
else:
    print(df_shareholder)

# 2. Check in compliance_cache_violations (ServiceNow Compliance)
df_compliance = pd.read_sql_query(f"SELECT id, source_type, pan_card, declared_qty, position_difference, shareholder_position FROM public.compliance_cache_violations WHERE pan_card = '{pan}'", conn)
print("\n=== SERVICENOW COMPLIANCE VIOLATIONS ===")
if df_compliance.empty:
    print(f"No records found for PAN {pan}")
else:
    print(df_compliance)
