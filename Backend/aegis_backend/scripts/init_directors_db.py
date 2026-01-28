#!/usr/bin/env python3
"""
Script to initialize the directors database from the Excel file
"""

import sqlite3
import pandas as pd
import os

def init_directors_db():
    """Initialize the directors database from the Excel file"""
    # Define paths
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    excel_file = os.path.join(backend_dir, "public", "List of Directors.xlsx")
    db_file = os.path.join(backend_dir, "public", "directors.db")
    
    # Check if Excel file exists
    if not os.path.exists(excel_file):
        print(f"Excel file not found: {excel_file}")
        return False
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file, sheet_name="Sheet2")
        print(f"Loaded {len(df)} directors from Excel file")
        
        # Clean the data
        df = df.dropna(subset=['Name', 'DIN'])
        df['DIN'] = df['DIN'].astype(str)
        print(f"Found {len(df)} valid directors after cleaning")
        
        # Create database connection
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create directors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                din TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert directors data
        inserted_count = 0
        for _, row in df.iterrows():
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO directors (name, din) VALUES (?, ?)",
                    (row['Name'], str(row['DIN']))
                )
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting director {row['Name']}: {e}")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print(f"Successfully inserted {inserted_count} directors into database")
        print(f"Database created at: {db_file}")
        return True
        
    except Exception as e:
        print(f"Error initializing directors database: {e}")
        return False

if __name__ == "__main__":
    init_directors_db()