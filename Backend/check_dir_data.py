import sqlite3
import os

db_path = "/home/cognitbotz/aegis-platform/Backend/aegis_backend/directors_data.db"
if os.path.exists(db_path):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print(f"Tables in {db_path}:")
        for t in tables:
            print(f" - {t[0]}")
else:
    print(f"Not found: {db_path}")
