# Database Initialization Utilities
# This module contains utility functions for initializing various databases used in the application

import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_visits_db():
    """Initialize the visits database with a visits table"""
    db_path = os.path.join(os.path.dirname(__file__), "..", "public", "visits.db")
    
    # Create public directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create database and table if they don't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create visits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Initialize with a default row if table is empty
    cursor.execute("SELECT COUNT(*) FROM visits")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO visits (count) VALUES (0)")
    
    conn.commit()
    conn.close()
    logger.info("Visits database initialized successfully")

def init_places_db():
    """Initialize places database with default Adani Corporate House"""
    db_path = os.path.join(os.path.dirname(__file__), "..", "public", "places.db")
    
    # Create public directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create places table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if default place exists
    cursor.execute("SELECT COUNT(*) FROM places WHERE is_default = 1")
    if cursor.fetchone()[0] == 0:
        # Insert default Adani Corporate House
        cursor.execute('''
            INSERT INTO places (name, address, is_default)
            VALUES (?, ?, ?)
        ''', (
            'Adani Corporate House',
            'Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421, Gujarat, India',
            1
        ))
    
    conn.commit()
    conn.close()
    logger.info("Places database initialized successfully")

# Initialize databases on module import
init_visits_db()
init_places_db()