"""
Database Migration Script for Route-Based RBAC System
This script creates the necessary tables for the new permission system
and seeds initial data.
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path to import from aegis_backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def get_db_path():
    """Get the path to the email_data.db database"""
    db_path = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "aegis_backend", 
        "public", 
        "email_data.db"
    )
    return os.path.abspath(db_path)

def create_tables(conn):
    """Create all necessary tables for RBAC system"""
    cursor = conn.cursor()
    
    print("Creating route_permissions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) NOT NULL,
            route_path VARCHAR(255) NOT NULL,
            permission_type VARCHAR(50) NOT NULL,
            assigned_by VARCHAR(255),
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            notes TEXT,
            CONSTRAINT chk_permission_type CHECK (permission_type IN ('view', 'admin', 'edit')),
            CONSTRAINT chk_email_domain CHECK (
                email LIKE '%@adani.com' OR 
                email LIKE '%@pspprojects.com' OR
                email LIKE '%@adaniltd.onmicrosoft.com' OR
                email LIKE '%@adani-total.in' OR
                email LIKE '%@ndtv.com' OR
                email LIKE '%@itdcem.co.in'
            ),
            UNIQUE(email, route_path, permission_type)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_permissions_email ON route_permissions(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_permissions_route ON route_permissions(route_path)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_permissions_active ON route_permissions(is_active)")
    
    print("Creating route_definitions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_path VARCHAR(255) NOT NULL UNIQUE,
            route_name VARCHAR(255) NOT NULL,
            description TEXT,
            application VARCHAR(100) NOT NULL,
            parent_route VARCHAR(255),
            requires_admin BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_definitions_application ON route_definitions(application)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_route_definitions_parent ON route_definitions(parent_route)")
    
    print("Creating access_requests table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            requested_route VARCHAR(255) NOT NULL,
            requested_permission VARCHAR(50) NOT NULL,
            justification TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_by VARCHAR(255),
            reviewed_at TIMESTAMP,
            review_notes TEXT,
            CONSTRAINT chk_requested_permission CHECK (requested_permission IN ('view', 'admin', 'edit')),
            CONSTRAINT chk_status CHECK (status IN ('pending', 'approved', 'rejected'))
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_requests_email ON access_requests(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_requests_status ON access_requests(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_requests_route ON access_requests(requested_route)")
    
    print("Creating auth_audit_logs table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            event_details TEXT,
            ip_address VARCHAR(45),
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            application VARCHAR(100) DEFAULT 'aegis'
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_email ON auth_audit_logs(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON auth_audit_logs(event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON auth_audit_logs(timestamp)")
    
    conn.commit()
    print("[OK] All tables created successfully")

def seed_route_definitions(conn):
    """Seed initial route definitions"""
    cursor = conn.cursor()
    
    print("Seeding route definitions...")
    
    routes = [
        ('/bse-alerts', 'BSE Alerts', 'BSE regulatory alerts and notifications', 'bse', None, 0),
        ('/rbi-dashboard', 'RBI Dashboard', 'RBI compliance dashboard', 'rbi', None, 0),
        ('/sebi-dashboard', 'SEBI Dashboard', 'SEBI regulatory dashboard', 'sebi', None, 0),
        ('/insider-trading', 'Insider Trading', 'Insider trading monitoring and compliance', 'insider-trading', None, 0),
        ('/directors-disclosure', 'Directors Disclosure', 'Directors disclosure management with tabs: Data Source, Master Data, Companies Master Data', 'directors-disclosure', None, 0),
        ('/minutes-preparation', 'Minutes Preparation', 'Board meeting minutes preparation', 'minutes-preparation', None, 1),
    ]
    
    for route in routes:
        try:
            cursor.execute("""
                INSERT INTO route_definitions (route_path, route_name, description, application, parent_route, requires_admin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, route)
        except sqlite3.IntegrityError:
            print(f"  Route {route[0]} already exists, skipping...")
    
    conn.commit()
    print(f"[OK] Seeded {len(routes)} route definitions")

def seed_permissions(conn):
    """Seed initial permissions from initial_permissions_seed.sql"""
    cursor = conn.cursor()
    
    print("Seeding initial permissions...")
    
    # Read and execute the seed SQL file
    seed_file = os.path.join(os.path.dirname(__file__), '..', '..', 'initial_permissions_seed.sql')
    
    if not os.path.exists(seed_file):
        print(f"Warning: Seed file not found at {seed_file}")
        print("Skipping permission seeding. Run initial_permissions_seed.sql manually.")
        return
    
    with open(seed_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Execute the SQL script
    try:
        cursor.executescript(sql_script)
        conn.commit()
        
        # Count inserted permissions
        cursor.execute("SELECT COUNT(*) FROM route_permissions")
        count = cursor.fetchone()[0]
        print(f"[OK] Seeded {count} permission entries")
    except Exception as e:
        print(f"Error seeding permissions: {e}")
        print("You may need to run initial_permissions_seed.sql manually")

def migrate_existing_admin(conn):
    """Migrate existing admin user from LOCAL_USER_ROLES to database"""
    cursor = conn.cursor()
    
    print("Migrating existing admin user...")
    
    # Check if cogn206112@adani.com already has permissions
    cursor.execute("""
        SELECT COUNT(*) FROM route_permissions 
        WHERE email = 'cogn206112@adani.com'
    """)
    
    if cursor.fetchone()[0] > 0:
        print("  Admin user already migrated, skipping...")
        return
    
    # This will be handled by the seed file
    print("  Admin user will be added via seed file")

def verify_migration(conn):
    """Verify that migration was successful"""
    cursor = conn.cursor()
    
    print("\nVerifying migration...")
    
    # Check tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('route_permissions', 'route_definitions', 'access_requests', 'auth_audit_logs')
    """)
    tables = cursor.fetchall()
    print(f"[OK] Found {len(tables)} tables")
    
    # Check route definitions
    cursor.execute("SELECT COUNT(*) FROM route_definitions")
    route_count = cursor.fetchone()[0]
    print(f"[OK] Route definitions: {route_count}")
    
    # Check permissions
    cursor.execute("SELECT COUNT(*) FROM route_permissions")
    perm_count = cursor.fetchone()[0]
    print(f"[OK] Permissions: {perm_count}")
    
    # Show permission breakdown by route
    cursor.execute("""
        SELECT route_path, permission_type, COUNT(*) as user_count
        FROM route_permissions
        GROUP BY route_path, permission_type
        ORDER BY route_path, permission_type
    """)
    
    print("\nPermission breakdown:")
    for row in cursor.fetchall():
        print(f"  {row[0]:<45} {row[1]:<10} {row[2]:>3} users")
    
    print("\n[OK] Migration verification complete!")

def main():
    """Main migration function"""
    print("=" * 70)
    print("Route-Based RBAC Migration Script")
    print("=" * 70)
    
    db_path = get_db_path()
    print(f"\nDatabase: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
    
    # Backup database
    backup_path = db_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print("[OK] Backup created")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Run migration steps
        create_tables(conn)
        seed_route_definitions(conn)
        seed_permissions(conn)
        migrate_existing_admin(conn)
        verify_migration(conn)
        
        print("\n" + "=" * 70)
        print("Migration completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        print("Rolling back changes...")
        conn.rollback()
        print("Restoring from backup...")
        shutil.copy2(backup_path, db_path)
        print("Database restored to previous state")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
