import sqlite3
import os

def check_notifications():
    db_path = "/home/cognitbotz/aegis-platform/Backend/aegis_backend/public/notifications.db"
    if not os.path.exists(db_path):
        print(f"File not found: {db_path}")
        return
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print(f"Tables in notifications.db:")
        for t in tables:
            print(f" - {t[0]}")
            
if __name__ == "__main__":
    check_notifications()
