import os
import sys
import logging
from dotenv import load_dotenv

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment (which we already pointed to localhost:5435)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_local_db")

def run_setup():
    logger.info("Starting AEG-IS Local Database Schema Creation...")
    
    try:
        # 1. Director Analysis / Registry
        # from routes.director_data_analysis import init_database as init_director_db
        # logger.info("Initializing Director Analysis Tables...")
        # init_director_db()
        
        # 2. RBAC Tables
        # from routes.rbac import init_rbac_pg_tables
        # from routes.user_management import init_rbac_db
        # logger.info("Initializing RBAC & User Management...")
        # init_rbac_pg_tables()
        # init_rbac_db()
        
        # 3. Visits & Tracking
        # from utils.db_init import init_postgres_tracking
        # logger.info("Initializing Visit Tracking & Places...")
        # init_postgres_tracking()
        
        # 4. Minutes & Resolutions
        from routes.minutes import init_minutes_pg
        logger.info("Initializing Meeting Minutes Tables...")
        init_minutes_pg()
        
        # Seed local database with sample data
        from utils.pgsql_service import get_pg_connection, get_pg_cursor
        target_db = os.getenv('POSTGRES_DATABASE_MINUTES')
        conn = get_pg_connection(target_db)
        if conn:
            try:
                cursor = get_pg_cursor(conn)
                
                # Check and seed places
                cursor.execute("SELECT COUNT(*) as count FROM places")
                if cursor.fetchone()['count'] == 0:
                    logger.info("Seeding sample places...")
                    places = [
                        ('Adani Corporate House, Ahmedabad', 'Shantigram, Near Vaishno Devi Circle, Ahmedabad, Gujarat 382421', True),
                        ('Adani House, Gurgaon', 'Plot No. 83, Sector 32, Institutional Area, Gurgaon, Haryana 122001', False),
                        ('Adani House, Mumbai', 'Adani House, Near Mithakhali Crossing, Navrangpura, Ahmedabad', False)
                    ]
                    for name, address, is_default in places:
                        cursor.execute(
                            "INSERT INTO places (name, address, is_default) VALUES (%s, %s, %s)",
                            (name, address, is_default)
                        )
                
                # Check and seed resolution templates
                cursor.execute("SELECT COUNT(*) as count FROM resolution_templates")
                if cursor.fetchone()['count'] == 0:
                    logger.info("Seeding sample resolutions...")
                    resolutions = [
                        ('Approval of Financial Results', 'RESOLVED THAT the audited financial results of the Company for the quarter and financial year ended March 31, 2026, along with the Auditors\' Report thereon, be and are hereby approved.'),
                        ('Appointment of Statutory Auditors', 'RESOLVED THAT pursuant to Section 139 of the Companies Act, 2013, M/s. SRBC & CO LLP, Chartered Accountants, be and are appointed as Statutory Auditors of the Company.'),
                        ('Disclosure of Interest by Directors', 'RESOLVED THAT the general notice of disclosure of interest in Form MBP-1 received from the Directors of the Company under Section 184 of the Companies Act, 2013, be and is hereby noted.')
                    ]
                    for name, text in resolutions:
                        cursor.execute(
                            "INSERT INTO resolution_templates (template_name, resolution_text) VALUES (%s, %s)",
                            (name, text)
                        )
                
                conn.commit()
                logger.info("Seeding completed successfully!")
            except Exception as e:
                conn.rollback()
                logger.error(f"Seeding failed: {e}")
            finally:
                conn.close()

        logger.info("AEG-IS Local Database Setup COMPLETE!")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_setup()
