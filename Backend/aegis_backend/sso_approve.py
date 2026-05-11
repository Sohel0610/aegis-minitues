"""
One-time script to approve all pending RBAC access requests and seed route definitions.
Run from: Backend/aegis_backend/
Usage: python approve_pending.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from utils.pgsql_service import get_pg_connection, get_pg_cursor

DB_NAME = os.getenv('POSTGRES_DATABASE_RBAC', 'visit_tracking_system')
APPROVED_BY = "system-bootstrap"

def run():
    print(f"Connecting to: {DB_NAME}...")
    conn = get_pg_connection(DB_NAME)
    if not conn:
        print("ERROR: Cannot connect.")
        return

    cursor = get_pg_cursor(conn)

    # Step 1: Seed route_definitions (must happen before permissions due to FK)
    print("\n[1/3] Seeding route_definitions...")
    routes = [
        ('/bse-alerts',           'BSE Alerts',           'BSE regulatory alerts and notifications',         'bse',                  'bse'),
        ('/rbi-dashboard',        'RBI Dashboard',         'RBI compliance and policy dashboard',             'rbi',                  'rbi'),
        ('/sebi-dashboard',       'SEBI Dashboard',        'SEBI regulatory filings dashboard',               'sebi',                 'sebi'),
        ('/insider-trading',      'Insider Trading',       'Insider trading monitoring and compliance',        'insider-trading',      'insider-trading'),
        ('/directors-disclosure', 'Directors Disclosure',  'Director shareholding and disclosure management',  'directors-disclosure', 'directors-disclosure'),
        ('/minutes-preparation',  'Minutes Preparation',   'Board/committee meeting minutes preparation',      'minutes-preparation',  'minutes-preparation'),
    ]
    for route_path, route_name, description, application, module_name in routes:
        cursor.execute("""
            INSERT INTO rbac.route_definitions
                (route_path, route_name, description, application, display_name, module_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (route_path) DO UPDATE SET
                route_name   = EXCLUDED.route_name,
                description  = EXCLUDED.description,
                application  = EXCLUDED.application,
                display_name = EXCLUDED.display_name,
                module_name  = EXCLUDED.module_name
        """, (route_path, route_name, description, application, route_name, module_name))
        print(f"  ✓ {route_path} → {route_name}")
    conn.commit()

    # Step 2: Fetch all pending requests
    print("\n[2/3] Fetching pending access requests...")
    cursor.execute("SELECT * FROM rbac.access_requests WHERE status = 'pending' ORDER BY id")
    pending = cursor.fetchall()

    if not pending:
        print("  No pending requests found.")
    else:
        print(f"  Found {len(pending)} pending request(s):")
        for req in pending:
            print(f"    ID={req['id']} | {req['email']} | {req['requested_route']} | {req['requested_permission']}")

    # Step 3: Approve all pending
    print("\n[3/3] Approving all pending requests...")
    approved = 0
    for req in pending:
        try:
            # Mark as approved
            cursor.execute("""
                UPDATE rbac.access_requests
                SET status = 'approved', reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP,
                    review_notes = 'Bootstrap approved via script'
                WHERE id = %s
            """, (APPROVED_BY, req['id']))

            # Grant permission (using named constraint for UPSERT)
            cursor.execute("""
                INSERT INTO rbac.route_permissions
                    (email, route_path, permission_type, assigned_by, notes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT route_permissions_email_route_path_key
                DO UPDATE SET
                    permission_type = EXCLUDED.permission_type,
                    assigned_by     = EXCLUDED.assigned_by,
                    notes           = EXCLUDED.notes,
                    is_active       = TRUE,
                    updated_at      = CURRENT_TIMESTAMP
            """, (
                req['email'],
                req['requested_route'],
                req['requested_permission'],
                APPROVED_BY,
                f"Approved via bootstrap script (request #{req['id']})"
            ))
            conn.commit()
            approved += 1
            print(f"  ✓ Approved #{req['id']}: {req['email']} → {req['requested_route']} ({req['requested_permission']})")
        except Exception as e:
            conn.rollback()
            print(f"  ✗ Failed #{req['id']}: {e}")

    # Step 4: Verify
    print("\n[VERIFY] Current route_permissions:")
    cursor.execute("SELECT email, route_path, permission_type, is_active FROM rbac.route_permissions ORDER BY email, route_path")
    perms = cursor.fetchall()
    if perms:
        for p in perms:
            status = "✓ ACTIVE" if p['is_active'] else "✗ INACTIVE"
            print(f"  {status} | {p['email']} → {p['route_path']} ({p['permission_type']})")
    else:
        print("  No permissions found.")

    print(f"\n✅ Done. Approved {approved}/{len(pending)} requests.")
    print("   → Restart FastAPI server and log in again to get has_access=True")
    conn.close()

if __name__ == "__main__":
    run()
