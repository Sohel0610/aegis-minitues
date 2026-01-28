#!/usr/bin/env python3
"""
Script to initialize the places database with default places
"""

import sqlite3
import os

def init_places_db():
    # Define paths
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(backend_dir, "public", "places.db")
    
    # Connect to database (this will create the file if it doesn't exist)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create places table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            address TEXT NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default place
    default_place = {
        'name': 'Adani Corporate House',
        'address': 'Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421, Gujarat, India',
        'is_default': True
    }
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO places (name, address, is_default)
            VALUES (?, ?, ?)
        ''', (default_place['name'], default_place['address'], default_place['is_default']))
        
        # If no default place exists, set the first one as default
        cursor.execute('''
            UPDATE places 
            SET is_default = CASE WHEN id = (SELECT MIN(id) FROM places) THEN 1 ELSE 0 END
        ''')
        
        conn.commit()
        print("Places database initialized successfully!")
        print(f"Database location: {db_file}")
        
        # Show all places
        cursor.execute('SELECT * FROM places')
        places = cursor.fetchall()
        print("\nCurrent places in database:")
        for place in places:
            print(f"- {place[1]}: {place[2]} (Default: {bool(place[3])})")
            
    except Exception as e:
        print(f"Error initializing places database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_places_db()