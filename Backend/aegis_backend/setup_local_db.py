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
        from routes.director_data_analysis import init_database as init_director_db
        logger.info("Initializing Director Analysis Tables...")
        init_director_db()
        
        # 2. RBAC Tables
        from routes.rbac import init_rbac_pg_tables
        from routes.user_management import init_rbac_db
        logger.info("Initializing RBAC & User Management...")
        init_rbac_pg_tables()
        init_rbac_db()
        
        # 3. Visits & Tracking
        from utils.db_init import init_postgres_tracking
        logger.info("Initializing Visit Tracking & Places...")
        init_postgres_tracking()
        
        # 4. Minutes & Resolutions
        from routes.minutes import init_minutes_pg
        logger.info("Initializing Meeting Minutes Tables...")
        init_minutes_pg()
        
        # 5. Director Changes (if it exists)
        try:
             from routes.director_changes import init_db as init_changes_db
             logger.info("Initializing Director Changes Log...")
             init_changes_db()
        except ImportError:
             logger.warning("Director Changes module not found, skipping...")

        logger.info("AEG-IS Local Database Setup COMPLETE!")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_setup()
