import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

def get_family_info(din):
    """
    Fetches family information for a specific DIN by joining 
    directors_master and family_information tables.
    """
    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), '..', 'aegis_backend', '.env')
    load_dotenv(env_path)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
            sslmode='require'
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query to join directors and family info
        query = """
            SELECT 
                d.din, 
                d.name as director_name,
                f.father,
                f.mother,
                f.son,
                f.sons_wife,
                f.daughter,
                f.daughters_husband,
                f.brother,
                f.sister,
                f.section_2_77_i as huf,
                f.section_2_77_ii as spouse
            FROM directors_master.directors d
            JOIN family_information.director_family f ON d.name = f.director_name
            WHERE d.din = %s
        """
        
        cur.execute(query, (din,))
        result = cur.fetchone()
        
        if result:
            print(f"\nFamily Information for DIN: {din} ({result['director_name']})")
            print("-" * 50)
            for key, value in result.items():
                if key not in ['din', 'director_name']:
                    print(f"{key.replace('_', ' ').title():<20}: {value or 'NIL'}")
        else:
            print(f"No family information found for DIN: {din}")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error fetching family info: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_family_info(sys.argv[1])
    else:
        print("Usage: python get_family_info.py <DIN>")
