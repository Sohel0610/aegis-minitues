import sqlite3
import os

db_path = r"d:\Adani_Project\aegis_phase_2_dev\Backend\aegis_backend\public\Director_Family_Information.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

new_columns = [
    "Father_PAN TEXT",
    "Mother_PAN TEXT",
    "Father_PAN_File TEXT",
    "Mother_PAN_File TEXT"
]

for col in new_columns:
    try:
        cursor.execute(f"ALTER TABLE Sheet1 ADD COLUMN {col}")
        print(f"Added column: {col}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column already exists: {col}")
        else:
            print(f"Error adding {col}: {e}")

conn.commit()
conn.close()
print("Migration completed successfully.")
