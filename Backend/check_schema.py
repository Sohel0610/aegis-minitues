import sqlite3
import os

db_path = r"d:\Adani_Project\aegis_phase_2_dev\Backend\public\Director_Family_Information.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Sheet1'")
print(cursor.fetchone()[0])
conn.close()
