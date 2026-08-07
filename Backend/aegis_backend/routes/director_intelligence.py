# director_intelligence.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import os
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

router = APIRouter(
    prefix="/director-intelligence",
    tags=["Director Intelligence"]
)

# Load environment variables from the parent aegis_backend folder
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

def get_db_connection():
    try:
        # Check if environment variables are loaded
        host = os.getenv('POSTGRES_HOST')
        if not host:
            print("WARNING: POSTGRES_HOST not found in router. Check .env path.")
            
        conn = psycopg2.connect(
            host=host,
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@router.get("/summary")
async def get_intelligence_summary():
    """Returns high-level KPIs for enriched director data."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        # 1. Total Enriched vs Total
        cur.execute("SELECT COUNT(*) as total, COUNT(last_api_sync) as enriched FROM directors_master.directors")
        counts = cur.fetchone()
        
        # 2. DIN Status Breakdown
        cur.execute("""
            SELECT d.din_status, COUNT(DISTINCT d.din) as count 
            FROM directors_master.directors d
            INNER JOIN directors_master.external_board_members ea ON d.din = ea.din
            LEFT JOIN directors_data.companies c ON ea.cin = c.cin
            WHERE d.last_api_sync IS NOT NULL 
            AND (ea.status IS NULL OR ea.status = '' OR ea.status = 'None' OR ea.status ILIKE 'ACTIVE%%')
            AND (c.status IS NULL OR c.status = '' OR c.status = 'None' OR c.status ILIKE 'ACTIVE%%')
            GROUP BY d.din_status
        """)
        status_breakdown = cur.fetchall()
        
        # 3. Gender Breakdown - Strict Male/Female only
        cur.execute("""
            SELECT d.gender, COUNT(DISTINCT d.din) as count 
            FROM directors_master.directors d
            INNER JOIN directors_master.external_board_members ea ON d.din = ea.din
            LEFT JOIN directors_data.companies c ON ea.cin = c.cin
            WHERE d.last_api_sync IS NOT NULL 
            AND UPPER(d.gender) IN ('MALE', 'FEMALE')
            AND (ea.status IS NULL OR ea.status = '' OR ea.status = 'None' OR ea.status ILIKE 'ACTIVE%%')
            AND (c.status IS NULL OR c.status = '' OR c.status = 'None' OR c.status ILIKE 'ACTIVE%%')
            GROUP BY 1
        """)
        gender_breakdown = cur.fetchall()
        
        # 4. DIR-3 KYC Breakdown
        cur.execute("""
            SELECT COALESCE(d.dir3_kyc, 'Pending') as status, COUNT(DISTINCT d.din) as count 
            FROM directors_master.directors d
            INNER JOIN directors_master.external_board_members ea ON d.din = ea.din
            LEFT JOIN directors_data.companies c ON ea.cin = c.cin
            WHERE d.last_api_sync IS NOT NULL
            AND (ea.status IS NULL OR ea.status = '' OR ea.status = 'None' OR ea.status ILIKE 'ACTIVE%%')
            AND (c.status IS NULL OR c.status = '' OR c.status = 'None' OR c.status ILIKE 'ACTIVE%%')
            GROUP BY 1
        """)
        kyc_breakdown = cur.fetchall()

        # 5. Total Associations tracked (Excluding Amalgamated/Resigned)
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM directors_master.external_board_members ea
            LEFT JOIN directors_data.companies c ON ea.cin = c.cin
            WHERE (ea.status IS NULL OR ea.status = '' OR ea.status = 'None' OR ea.status ILIKE 'ACTIVE%%')
              AND (c.status IS NULL OR c.status = '' OR c.status = 'None' OR c.status ILIKE 'ACTIVE%%')
        """)
        assoc_count = cur.fetchone()

        return {
            "counts": counts,
            "status": status_breakdown,
            "gender": gender_breakdown,
            "kyc": kyc_breakdown,
            "total_external_boards": assoc_count['total']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@router.get("/directors")
async def get_enriched_directors():
    """Returns all directors with their registry status and association counts."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cur.execute("""
            SELECT 
                d.din, 
                d.name, 
                d.din_status, 
                d.gender, 
                d.nationality, 
                d.dir3_kyc,
                d.last_api_sync,
                d.last_mca_updated,
                COALESCE(eb_counts.cnt, 0) as external_board_count
            FROM directors_master.directors d
            LEFT JOIN (
                SELECT ea.din, COUNT(*) as cnt
                FROM directors_master.external_board_members ea
                LEFT JOIN directors_data.companies c ON ea.cin = c.cin
                WHERE ea.din IS NOT NULL
                  AND (ea.status IS NULL OR ea.status = '' OR ea.status = 'None' OR ea.status ILIKE 'ACTIVE%%')
                  AND (c.status IS NULL OR c.status = '' OR c.status = 'None' OR c.status ILIKE 'ACTIVE%%')
                GROUP BY ea.din
            ) eb_counts ON d.din = eb_counts.din
            WHERE d.last_api_sync IS NOT NULL
            ORDER BY d.name
        """)
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@router.get("/associations/{din}")
async def get_director_associations(din: str):
    """Returns all external board associations for a specific director, excluding Amalgamated."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cur.execute("""
            SELECT 
                ea.cin, 
                ea.company_name, 
                ea.designation, 
                ea.appointment_date, 
                COALESCE(ea.status, 'Active') as status,
                COALESCE(c.is_adani, FALSE) as is_group
            FROM directors_master.external_board_members ea
            LEFT JOIN directors_data.companies c ON ea.cin = c.cin
            WHERE ea.din = %s
              AND (ea.status IS NULL OR ea.status = '' OR ea.status = 'None' OR ea.status ILIKE 'ACTIVE%%')
              AND (c.status IS NULL OR c.status = '' OR c.status = 'None' OR c.status ILIKE 'ACTIVE%%')
            ORDER BY ea.appointment_date DESC NULLS LAST
        """, (din,))
        results = cur.fetchall()
        return results
    except Exception as e:
        print(f"CRITICAL SQL ERROR in get_director_associations for DIN {din}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
