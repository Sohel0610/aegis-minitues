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

def fetch_director_data(din):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Fetch Director Master Record
        cur.execute("""
            SELECT * FROM directors_master.directors 
            WHERE din = %s
        """, (din,))
        director_master = cur.fetchone()
        
        if not director_master:
            return {"error": f"No director found with DIN: {din}"}
            
        # 2. Fetch Associations linked with Company Details
        cur.execute("""
            SELECT 
                a.cin, 
                a.company_name, 
                a.designation, 
                a.appointment_date,
                a.status as position_status,
                c.status as company_status,
                c.category as company_category,
                c.class as company_class,
                c.address as company_address,
                c.email as company_email,
                c.paid_capital as company_paid_capital,
                c.auth_capital as company_auth_capital
            FROM directors_master.external_board_members a
            LEFT JOIN directors_data.companies c ON a.cin = c.cin
            WHERE a.din = %s
            ORDER BY a.appointment_date DESC
        """, (din,))
        associations = cur.fetchall()

        # 3. Fetch Professional Profile
        cur.execute("""
            SELECT * FROM directors_profile.directors_profile 
            WHERE din = %s
        """, (din,))
        profile = cur.fetchone()

        # 4. Fetch Family Information (Robust Matching)
        family = None
        potential_names = []
        
        # Strategy A: Full name from Master
        if director_master.get('name'):
            full_name = director_master['name'].strip()
            potential_names.append(full_name)
            
            # Strategy B: First and Last name only (removes middle names)
            parts = full_name.split()
            if len(parts) > 2:
                potential_names.append(f"{parts[0]} {parts[-1]}")

        # Strategy C: Name from Profile (often has Mr./Ms.)
        if profile and profile.get('name_of_director'):
            prof_name = profile['name_of_director'].replace('Mr.', '').replace('Ms.', '').replace('Mrs.', '').strip()
            if prof_name not in potential_names:
                potential_names.append(prof_name)

        # Try matching each potential variation
        for name_variant in potential_names:
            cur.execute("""
                SELECT * FROM family_information.director_family 
                WHERE UPPER(director_name) = UPPER(%s) 
                   OR UPPER(director_name) LIKE UPPER('%%' || %s || '%%')
                LIMIT 1
            """, (name_variant, name_variant))
            family = cur.fetchone()
            if family:
                break
        
        # Combine into single object
        result = {
            "director_info": director_master,
            "profile": profile,
            "family": family,
            "associations": associations,
            "total_associations": len(associations)
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()

def main():
    import sys
    
    # Check for command line argument
    if len(sys.argv) > 1:
        din_to_fetch = sys.argv[1]
    else:
        # Fallback to example DIN
        din_to_fetch = "00006273"
    
    print(f"Fetching complete profile for DIN: {din_to_fetch}...")
    data = fetch_director_data(din_to_fetch)
    
    if data:
        # Output as formatted JSON
        print(json.dumps(data, indent=2, default=json_serial))
        
        # Save to file for user convenience
        with open(f"director_data_{din_to_fetch}.json", "w") as f:
            json.dump(data, f, indent=2, default=json_serial)
        print(f"\n[OK] Data saved to director_data_{din_to_fetch}.json")

if __name__ == "__main__":
    main()
