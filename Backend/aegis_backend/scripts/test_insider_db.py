import os
import logging
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    load_dotenv(env_path)

    try:
        host     = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST')
        user     = os.getenv('DB_USER') or os.getenv('POSTGRES_USER')
        password = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD')
        database = os.getenv('DB_NAME')
        port     = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT') or '5432'
        
        db_config = {
            'host': host,
            'port': int(port),
            'database': database,
            'user': user,
            'password': password,
            'connect_timeout': 10
        }

        _sslmode = os.getenv('DB_SSLMODE') or os.getenv('POSTGRES_SSLMODE')
        if _sslmode:
            db_config['sslmode'] = _sslmode
        elif host and 'azure.com' in host.lower():
            db_config['sslmode'] = 'require'

        logger.info(f"Connecting to {host}...")
        try:
            conn = psycopg2.connect(**db_config)
        except Exception as e:
            if "could not translate host name" in str(e) or "Name or service not known" in str(e):
                db_config['host'] = "10.212.154.132"
                conn = psycopg2.connect(**db_config)
            else:
                raise e
        
        cur = conn.cursor()
        cur.execute("SELECT version();")
        logger.info(f"SUCCESS: {cur.fetchone()[0]}")
        
        cur.execute("SELECT id, company_name FROM companies LIMIT 5;")
        print("\nSAMPLE COMPANIES:")
        for c in cur.fetchall():
            print(f" - {c[1]}")

        cur.execute("SELECT id, batch_name, latest_date FROM result_batches ORDER BY latest_date DESC LIMIT 5;")
        print("\nSAMPLE BATCHES:")
        for b in cur.fetchall():
            print(f" - {b[1]} ({b[2]})")

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"FAILED: {e}")

if __name__ == "__main__":
    test_connection()
