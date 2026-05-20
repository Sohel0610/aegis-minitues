import psycopg2
import os
from dotenv import load_dotenv

def setup_database():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(env_path)

    db_host = os.getenv('DB_HOST') or '192.168.0.56'
    db_port = os.getenv('DB_PORT') or '5436'
    db_name = os.getenv('DB_NAME') or 'aegis_insider'
    db_user = os.getenv('DB_USER') or 'postgres'
    db_password = os.getenv('DB_PASSWORD') or 'postgres'

    print(f"Connecting to database: {db_name} @ {db_host}:{db_port}")

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("Creating tables if they do not exist...")

        # 1. Master table for Self-Declarations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.servicenow_declarations (
                ritm_number VARCHAR(50) PRIMARY KEY,
                requested_for VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                employee_code VARCHAR(50),
                designation VARCHAR(255),
                declaration_date DATE,
                phase VARCHAR(50),
                fiscal_year VARCHAR(50),
                state VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  - Table 'servicenow_declarations' created/verified.")

        # 2. Normalized Holdings per Person and Company
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.servicenow_holdings (
                id SERIAL PRIMARY KEY,
                ritm_number VARCHAR(50) REFERENCES public.servicenow_declarations(ritm_number) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                relationship VARCHAR(100) NOT NULL,
                pan_card VARCHAR(20) NOT NULL,
                company_id INTEGER REFERENCES public.companies(id),
                declared_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  - Table 'servicenow_holdings' created/verified.")

        # 3. Master table for Pre-Clearance requests
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.servicenow_preclearances (
                ritm_number VARCHAR(50) PRIMARY KEY,
                requested_for VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                employee_code VARCHAR(50),
                designation VARCHAR(255),
                phase VARCHAR(50),
                fiscal_year VARCHAR(50),
                state VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  - Table 'servicenow_preclearances' created/verified.")

        # 4. Approved Pre-Clearance Details
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.servicenow_preclearance_details (
                id SERIAL PRIMARY KEY,
                ritm_number VARCHAR(50) REFERENCES public.servicenow_preclearances(ritm_number) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                relationship VARCHAR(100) NOT NULL,
                pan_card VARCHAR(20) NOT NULL,
                approved_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("  - Table 'servicenow_preclearance_details' created/verified.")

        # Indexes for fast querying
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sn_holdings_pan_comp ON public.servicenow_holdings(pan_card, company_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sn_preclearance_pan ON public.servicenow_preclearance_details(pan_card);
        """)
        print("  - Indexes created/verified.")

        conn.close()
        print("Database schema successfully set up!")
        return True
    except Exception as e:
        print(f"Error during database setup: {e}")
        return False

if __name__ == "__main__":
    setup_database()
