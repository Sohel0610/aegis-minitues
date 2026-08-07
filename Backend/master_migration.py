import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import logging
from dotenv import load_dotenv
import io
from datetime import datetime

# Load .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "aegis_backend", ".env"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_remote_pg_conn():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DATABASE'),
        connect_timeout=15
    )

def get_local_pg_conn():
    return psycopg2.connect(
        host='localhost',
        user='postgres',
        password='postgres',
        port=5436,
        database='aegis_insider'
    )

def create_schemas():
    conn = get_remote_pg_conn()
    try:
        with conn.cursor() as cur:
            schemas = [
                'rbac', 'tracking', 'minutes', 'directors', 
                'bse', 'sebi', 'rbi',
                'directors_master', 'directors_data', 'directors_profile', 'family_information'
            ]
            # Drop schemas to ensure clean recreation
            for s in schemas:
                cur.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")

            for s in schemas:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")
            
            # Insider Tables
            cur.execute("DROP TABLE IF EXISTS shareholder_records CASCADE")
            cur.execute("DROP TABLE IF EXISTS summary CASCADE")
            cur.execute("DROP TABLE IF EXISTS result_batches CASCADE")
            cur.execute("DROP TABLE IF EXISTS depository_types CASCADE")
            cur.execute("DROP TABLE IF EXISTS companies CASCADE")
            
            cur.execute("CREATE TABLE IF NOT EXISTS companies (id SERIAL PRIMARY KEY, company_name TEXT UNIQUE NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS depository_types (id SERIAL PRIMARY KEY, type_name TEXT UNIQUE NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS result_batches (id SERIAL PRIMARY KEY, batch_name TEXT UNIQUE NOT NULL, older_date DATE, latest_date DATE, created_at TIMESTAMPTZ DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS summary (id SERIAL PRIMARY KEY, company_id INTEGER, batch_id INTEGER, depository_id INTEGER, added_count INTEGER, removed_count INTEGER, changed_count INTEGER, unchanged_count INTEGER, total_count INTEGER, empty_pangir_latest INTEGER, empty_pangir_older INTEGER)")
            cur.execute("CREATE TABLE IF NOT EXISTS shareholder_records (id BIGSERIAL PRIMARY KEY, company_id INTEGER, batch_id INTEGER, depository_id INTEGER, pangir TEXT, name TEXT, email TEXT, position_latest NUMERIC, position_older NUMERIC, position_difference NUMERIC, status TEXT)")

            # Directors Master
            cur.execute("CREATE TABLE IF NOT EXISTS directors_master.directors (id SERIAL PRIMARY KEY, name TEXT NOT NULL, din TEXT UNIQUE, created_at TIMESTAMPTZ DEFAULT NOW())")
            
            # Directors Data
            cur.execute("CREATE TABLE IF NOT EXISTS directors_data.directors (din TEXT PRIMARY KEY, name TEXT, source_file TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS directors_data.companies (id SERIAL PRIMARY KEY, name TEXT UNIQUE, type TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS directors_data.directorships (id SERIAL PRIMARY KEY, din TEXT, company_id INTEGER, position TEXT, appointment_date TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS directors_data.document_summaries (id SERIAL PRIMARY KEY, director_name TEXT NOT NULL, din TEXT, file_path TEXT NOT NULL UNIQUE, full_text TEXT, summary TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())")

            # Directors Profile
            cur.execute("CREATE TABLE IF NOT EXISTS directors_profile.directors_profile (id SERIAL PRIMARY KEY, din TEXT UNIQUE, pan TEXT, name_of_director TEXT, address TEXT, date_of_birth DATE, qualification TEXT, experience TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())")

            # Family Information
            cur.execute("CREATE TABLE IF NOT EXISTS family_information.director_family (id SERIAL PRIMARY KEY, director_name TEXT NOT NULL, section_2_77_i TEXT, section_2_77_ii TEXT, section_2_77_iii TEXT, father TEXT, mother TEXT, son TEXT, sons_wife TEXT, daughter TEXT, daughters_husband TEXT, brother TEXT, sister TEXT, father_pan TEXT, mother_pan TEXT, father_pan_file TEXT, mother_pan_file TEXT, is_submitted INTEGER DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW())")

            # RBAC
            cur.execute("CREATE TABLE IF NOT EXISTS rbac.route_permissions (email TEXT, route_path TEXT, permission_type TEXT, is_active BOOLEAN, PRIMARY KEY(email, route_path))")
            cur.execute("CREATE TABLE IF NOT EXISTS rbac.allowed_emails (email TEXT PRIMARY KEY)")

            # Tracking
            cur.execute("CREATE TABLE IF NOT EXISTS tracking.visits (id SERIAL PRIMARY KEY, count INTEGER, last_updated TIMESTAMP)")
            cur.execute("CREATE TABLE IF NOT EXISTS tracking.places (id SERIAL PRIMARY KEY, name TEXT, address TEXT, is_default BOOLEAN DEFAULT FALSE)")

            # Minutes
            cur.execute("CREATE TABLE IF NOT EXISTS minutes.generated_minutes (id SERIAL PRIMARY KEY, company_name TEXT, meeting_type TEXT, meeting_date TEXT, file_path TEXT)")
            cur.execute("CREATE TABLE IF NOT EXISTS minutes.resolution_templates (id SERIAL PRIMARY KEY, template_name TEXT, resolution_text TEXT)")

            # BSE/SEBI/RBI
            cur.execute("CREATE TABLE IF NOT EXISTS bse.daily_logs (id SERIAL PRIMARY KEY, sr_no TEXT, entity_name TEXT, link TEXT, nature TEXT, summary TEXT, record_date DATE, created_at TIMESTAMPTZ DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS sebi.excel_summaries (id SERIAL PRIMARY KEY, date_key TEXT, row_index INTEGER, pdf_link TEXT, summary TEXT, inserted_at TIMESTAMP DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS rbi.master_summaries (id SERIAL PRIMARY KEY, run_date TEXT, pdf_link TEXT, summary TEXT, created_at TIMESTAMP DEFAULT NOW())")

        conn.commit()
    finally:
        conn.close()

def migrate_table(sqlite_db, sqlite_query, pg_schema, pg_table, pg_columns, conflict_clause=None):
    sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", sqlite_db)
    if not os.path.exists(sqlite_path):
        sqlite_path = os.path.join(os.path.dirname(__file__), "aegis_backend", "public", sqlite_db)
        if not os.path.exists(sqlite_path): return
    with sqlite3.connect(sqlite_path) as s_conn:
        s_conn.row_factory = sqlite3.Row
        with get_remote_pg_conn() as p_conn:
            with p_conn.cursor() as p_cur:
                s_cur = s_conn.cursor()
                s_cur.execute(sqlite_query)
                rows = s_cur.fetchall()
                if not rows: return
                
                cols_str = ",".join(pg_columns)
                q = f"INSERT INTO {pg_schema}.{pg_table} ({cols_str}) VALUES %s"
                if conflict_clause: q += f" {conflict_clause}"
                
                data = []
                for row in rows:
                    vals = []
                    for c in pg_columns:
                        try:
                             val = row[c]
                        except:
                             val = row[rows[0].keys().index(c)] if hasattr(row, 'keys') else row[0]
                        
                        # Clean values for PostgreSQL types
                        if val in ('--', 'N/A', 'NA', 'None', '', 'null'): val = None
                        if c in ('is_default', 'is_active', 'is_submitted'): val = bool(val) if val is not None else None
                        
                        # Handle specific date type columns
                        if c == 'date_of_birth' and isinstance(val, str):
                            # Ensure it's a valid date or set to None
                            try:
                                datetime.strptime(val, '%Y-%m-%d')
                            except:
                                val = None
                        
                        vals.append(val)
                    data.append(tuple(vals))
                
                execute_values(p_cur, q, data)
                p_conn.commit()
                logger.info(f"Migrated {len(rows)} to {pg_schema}.{pg_table}")

def migrate_insider_data():
    l_conn = get_local_pg_conn()
    r_conn = get_remote_pg_conn()
    try:
        for table in ['companies', 'depository_types', 'result_batches', 'summary']:
            with l_conn.cursor() as l_cur:
                l_cur.execute(f"SELECT * FROM {table}")
                rows = l_cur.fetchall()
                if rows:
                    col_names = [desc[0] for desc in l_cur.description]
                    with r_conn.cursor() as r_cur:
                        execute_values(r_cur, f"INSERT INTO {table} ({','.join(col_names)}) VALUES %s ON CONFLICT DO NOTHING", rows)
            r_conn.commit()
        
        with l_conn.cursor(name='insider_migrate_cursor') as l_cur:
            l_cur.itersize = 100000
            l_cur.execute("SELECT * FROM shareholder_records")
            count = 0
            while True:
                rows = l_cur.fetchmany(100000)
                if not rows: break
                f = io.StringIO()
                for row in rows: f.write('\t'.join([str(val) if val is not None else '\\N' for val in row]) + '\n')
                f.seek(0)
                with r_conn.cursor() as r_cur: r_cur.copy_from(f, 'shareholder_records')
                r_conn.commit()
                count += len(rows)
                logger.info(f"Streamed {count} insider records...")
    finally:
        l_conn.close()
        r_conn.close()

def main():
    logger.info("Starting fresh migration...")
    create_schemas()
    
    # RBAC/Tracking/Minutes
    migrate_table("email_data.db", "SELECT email, route_path, permission_type, is_active FROM route_permissions", "rbac", "route_permissions", ["email", "route_path", "permission_type", "is_active"], conflict_clause="ON CONFLICT (email, route_path) DO NOTHING")
    migrate_table("email_data.db", "SELECT email FROM email", "rbac", "allowed_emails", ["email"], conflict_clause="ON CONFLICT (email) DO NOTHING")
    migrate_table("visits.db", "SELECT id, count FROM visits", "tracking", "visits", ["id", "count"])
    migrate_table("places.db", "SELECT name, address, is_default FROM places", "tracking", "places", ["name", "address", "is_default"])
    migrate_table("minutes.db", "SELECT company_name, meeting_type, meeting_date, file_path FROM generated_minutes", "minutes", "generated_minutes", ["company_name", "meeting_type", "meeting_date", "file_path"])
    
    # Directors Master
    migrate_table("directors.db", "SELECT name, din FROM directors", "directors_master", "directors", ["name", "din"], conflict_clause="ON CONFLICT (din) DO NOTHING")

    # Directors Data
    migrate_table("directors_data.db", "SELECT din, name, source_file FROM directors", "directors_data", "directors", ["din", "name", "source_file"])
    migrate_table("directors_data.db", "SELECT name, type FROM companies", "directors_data", "companies", ["name", "type"], conflict_clause="ON CONFLICT (name) DO NOTHING")
    migrate_table("directors_data.db", "SELECT din, company_id, position, appointment_date FROM directorships", "directors_data", "directorships", ["din", "company_id", "position", "appointment_date"])
    migrate_table("directors_data.db", "SELECT director_name, din, file_path, full_text, summary FROM document_summaries", "directors_data", "document_summaries", ["director_name", "din", "file_path", "full_text", "summary"], conflict_clause="ON CONFLICT (file_path) DO NOTHING")

    # Directors Profile
    migrate_table("directors_profile.db", "SELECT DIN AS din, PAN AS pan, Name_of_Director AS name_of_director, Address AS address, Date_of_Birth AS date_of_birth, Qualification AS qualification, Nature_of_Experience_in_specific_Functional_Areas AS experience FROM directors_profile", "directors_profile", "directors_profile", ["din", "pan", "name_of_director", "address", "date_of_birth", "qualification", "experience"], conflict_clause="ON CONFLICT (din) DO NOTHING")

    # Family Information
    migrate_table("Director_Family_Information.db", 'SELECT Name AS director_name, "Section_2(77)(i)" AS section_2_77_i, "Section_2(77)(ii)" AS section_2_77_ii, "Section_2(77)(iii)" AS section_2_77_iii, Father AS father, Mother AS mother, Son AS son, "Son\'s_Wife" AS sons_wife, Daughter AS daughter, "Daughter\'s_husband" AS daughters_husband, Brother AS brother, Sister AS sister, Father_PAN AS father_pan, Mother_PAN AS mother_pan, Father_PAN_File AS father_pan_file, Mother_PAN_File AS mother_pan_file FROM Sheet1', "family_information", "director_family", ["director_name", "section_2_77_i", "section_2_77_ii", "section_2_77_iii", "father", "mother", "son", "sons_wife", "daughter", "daughters_husband", "brother", "sister", "father_pan", "mother_pan", "father_pan_file", "mother_pan_file"])

    # BSE/SEBI/RBI
    migrate_table("notifications.db", "SELECT SrNo AS sr_no, EntityName AS entity_name, Link AS link, Nature AS nature, Summary AS summary, Date AS record_date FROM DailyLogs", "bse", "daily_logs", ["sr_no", "entity_name", "link", "nature", "summary", "record_date"])
    migrate_table("sebi_excel_master.db", "SELECT date_key, row_index, pdf_link, summary, inserted_at FROM excel_summaries", "sebi", "excel_summaries", ["date_key", "row_index", "pdf_link", "summary", "inserted_at"])
    migrate_table("rbi.db", "SELECT run_date, pdf_link, summary, created_at FROM master_summaries", "rbi", "master_summaries", ["run_date", "pdf_link", "summary", "created_at"])

    # Insider Trading
    migrate_insider_data()

    logger.info("MASTER MIGRATION FINISHED SUCCESSFULLY.")

if __name__ == "__main__":
    main()
