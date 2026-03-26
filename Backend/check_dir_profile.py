import sqlite3
import os

db_path = "/home/cognitbotz/aegis-platform/Backend/aegis_backend/public/directors_profile.db"
if os.path.exists(db_path):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(directors_profile);")
        cols = cur.fetchall()
        print(f"Cols in {db_path}: {[c[1] for c in cols]}")
else:
    print(f"Not found: {db_path}")
