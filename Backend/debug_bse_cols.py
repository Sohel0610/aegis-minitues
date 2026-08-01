import sqlite3
import os

db_path = "/home/cognitbotz/aegis-platform/Backend/aegis_backend/public/notifications.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    cur.execute("PRAGMA table_info(DailyLogs)")
    cols = cur.fetchall()
    print(f"Columns in DailyLogs:")
    for c in cols:
         print(f" - {c[1]} ({c[2]})")
except Exception as e:
    print(f"Error: {e}")
conn.close()
