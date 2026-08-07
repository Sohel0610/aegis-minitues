import sqlite3
import os

def run():
    dbs = ["rbi.db", "sebi_excel_master.db"]
    for db in dbs:
        db_path = f"/home/cognitbotz/aegis-platform/Backend/aegis_backend/public/{db}"
        if not os.path.exists(db_path):
            print(f"File not found: {db_path}")
            continue
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cur.fetchall()
            print(f"--- {db} ---")
            for t in tables:
                print(f" - {t[0]}")
                if t[0].lower() == 'dailylogs' or t[0].lower() == 'daily_logs':
                    cur.execute(f"PRAGMA table_info({t[0]});")
                    cols = cur.fetchall()
                    print(f"   Cols: {[c[1] for c in cols]}")

if __name__ == "__main__":
    run()
