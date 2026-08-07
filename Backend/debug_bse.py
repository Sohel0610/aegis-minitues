import sqlite3
import os

db_path = "/home/cognitbotz/aegis-platform/Backend/aegis_backend/public/notifications.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    cur.execute("SELECT COUNT(*) FROM DailyLogs")
    print(f"DailyLogs count: {cur.fetchone()[0]}")
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"Actual tables: {cur.fetchall()}")
except Exception as e:
    print(f"Error: {e}")
conn.close()
