import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# CHANGE THIS EMAIL TO THE DESIRED ADMIN USER
# ==========================================
EMAIL_TO_GRANT = "user@example.com"


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
        cur = conn.cursor()

        # 1. Ensure the user exists with 'admin' role in user_roles
        print(f"Granting global Admin role in rbac.user_roles for {email}...")
        cur.execute("""
            INSERT INTO rbac.user_roles (email, role)
            VALUES (%s, %s)
            ON CONFLICT (email, role) DO NOTHING
        """, (email, 'admin'))

        # 2. Retrieve all active route paths
        cur.execute("SELECT route_path FROM rbac.route_definitions")
        routes = cur.fetchall()

        if not routes:
            print("No routes found in rbac.route_definitions.")
            return

        print(f"Found {len(routes)} routes. Granting granular admin access...")

        # 3. Insert or update permissions for all routes to 'admin'
        for row in routes:
            route_path = row[0]
            cur.execute("""
                INSERT INTO rbac.route_permissions (email, route_path, permission_type, assigned_by, notes, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email, route_path) 
                DO UPDATE SET permission_type = EXCLUDED.permission_type, is_active = TRUE
            """, (email, route_path, 'admin', 'System Script', 'Full Admin Access Granted', True))

        conn.commit()
        print(f"\n[SUCCESS] Full Admin Access granted to {email} across all modules.")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to grant access: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if not EMAIL_TO_GRANT or EMAIL_TO_GRANT == "user@example.com":
        print("Please edit the script to replace 'user@example.com' with the actual email address.")
    else:
        grant_admin_access(EMAIL_TO_GRANT)
