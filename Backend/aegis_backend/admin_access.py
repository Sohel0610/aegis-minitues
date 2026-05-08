import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# List of standard routes to initialize if missing
STANDARD_ROUTES = [
    ("/data-source", "Data Source", "excel"),
    ("/analytics", "Analytics Dashboard", "analytics"),
    ("/director-analysis", "Director Analysis", "director_analysis"),
    ("/directors-disclosure", "Directors Disclosure", "directors_disclosure"),
    ("/minutes", "Minutes Preparation", "minutes"),
    ("/rbi-sebi-compliance", "RBI/SEBI Compliance", "rbi"),
    ("/admin-panel", "Admin Control Center", "admin"),
    ("/insider-trading", "Insider Trading Monitor", "insider_trading"),
    ("/director-intelligence", "Director Intelligence", "director_intelligence"),
    ("/institutional-risk", "Institutional Risk", "institutional_risk")
]

def grant_admin_access(email):
    email = email.lower().strip()
    db_name = os.getenv('POSTGRES_DATABASE_RBAC')
    host = os.getenv('POSTGRES_HOST')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    port = os.getenv('POSTGRES_PORT', '5432')
    sslmode = os.getenv('POSTGRES_SSLMODE', 'require')

    if not all([host, db_name, user, password]):
        print("Error: Missing database credentials in .env file.")
        return

    print(f"Connecting to {db_name} at {host}...")
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=db_name,
            user=user,
            password=password,
            port=port,
            sslmode=sslmode
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if hasattr(psycopg2.extras, 'RealDictCursor') else conn.cursor()

        # 1. Pre-populate standard routes if they don't exist
        print("Checking/Initializing standard route definitions...")
        for path, display, module in STANDARD_ROUTES:
            cur.execute("""
                INSERT INTO rbac.route_definitions (route_path, route_name, display_name, module_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (route_path) DO NOTHING
            """, (path, display, display, module))
        
        # 2. Add to global user_roles table
        print(f"Granting global Admin role in rbac.user_roles...")
        cur.execute("""
            INSERT INTO rbac.user_roles (email, role)
            VALUES (%s, %s)
            ON CONFLICT (email, role) DO NOTHING
        """, (email, 'admin'))

        # 3. Get all routes for granular permissions
        cur.execute("SELECT route_path FROM rbac.route_definitions")
        routes = cur.fetchall()
        
        if not routes:
            print("No routes found. Something went wrong with initialization.")
            return

        print(f"Found {len(routes)} routes. Granting granular admin access to {email}...")

        # 4. Grant admin access for each route
        for row in routes:
            route_path = row[0] if isinstance(row, tuple) else row['route_path']
            cur.execute("""
                INSERT INTO rbac.route_permissions (email, route_path, permission_type, assigned_by, notes, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email, route_path) 
                DO UPDATE SET permission_type = EXCLUDED.permission_type, is_active = TRUE
            """, (email, route_path, 'admin', 'System Script', 'Full Admin Access Granted', True))
        
        conn.commit()
        print(f"\n[SUCCESS] Full Admin Access granted to {email} across all {len(routes)} modules.")
        print(f"You can now log in as {email} to access the Admin Panel and all products.")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to grant access: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grant_admin_access.py <email>")
    else:
        grant_admin_access(sys.argv[1])
