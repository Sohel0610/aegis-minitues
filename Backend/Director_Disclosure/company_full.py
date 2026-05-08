import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import date, datetime
from decimal import Decimal

# Load configuration from .env
# Assuming .env is in the parent backend folder
env_path = os.path.join(os.path.dirname(__file__), '..', 'aegis_backend', '.env')
load_dotenv(env_path)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError ("Type %s not serializable" % type(obj))

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
        print(f"Error connecting to database: {e}")
        return None

def fetch_company_data(cin):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Fetch Company Record
        cur.execute("""
            SELECT * FROM directors_data.companies 
            WHERE cin = %s
        """, (cin,))
        company_details = cur.fetchone()
        
        if not company_details:
            return {"error": f"No company found with CIN: {cin}"}
            
        # 2. Fetch Directors associated with this Company
        cur.execute("""
            SELECT 
                a.din,
                d.name as director_name,
                a.designation,
                a.appointment_date,
                d.din_status,
                d.gender,
                d.nationality,
                d.dir3_kyc,
                d.approve_date as din_approve_date
            FROM directors_master.external_associations a
            LEFT JOIN directors_master.directors d ON a.din = d.din
            WHERE a.cin = %s
            ORDER BY a.appointment_date DESC
        """, (cin,))
        directors = cur.fetchall()
        
        # Combine into single object
        result = {
            "company_info": company_details,
            "directors": directors,
            "total_directors": len(directors)
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()

def main():
    # Example CIN from previous output (Adani Green Energy Limited)
    cin_to_fetch = "L40106GJ2015PLC082007"
    
    print(f"Fetching full data for CIN: {cin_to_fetch}...")
    data = fetch_company_data(cin_to_fetch)
    
    if data:
        # Output as formatted JSON
        print(json.dumps(data, indent=2, default=json_serial))
        
        # Save to file for user convenience
        output_filename = f"company_data_{cin_to_fetch}.json"
        with open(output_filename, "w") as f:
            json.dump(data, f, indent=2, default=json_serial)
        print(f"\n[OK] Data saved to {output_filename}")

if __name__ == "__main__":
    main()
