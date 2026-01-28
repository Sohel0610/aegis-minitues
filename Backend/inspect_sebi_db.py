import sqlite3
import os

db_path = r"d:\Adani_Project\aegis_phase_2_dev\Backend\aegis_backend\public\sebi_excel_master.db"

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Table: excel_summaries ---")
    cursor.execute("PRAGMA table_info(excel_summaries)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    
    print("\n--- Sample Data (First 5 rows) ---")
    cursor.execute("SELECT * FROM excel_summaries LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    print("\n--- Rows with NULL or 'NIL' or empty values in key columns ---")
    # Assuming columns based on generic naming, will adjust if needed
    cursor.execute("SELECT COUNT(*) FROM excel_summaries")
    total = cursor.fetchone()[0]
    print(f"Total rows: {total}")
    
    conn.close()
