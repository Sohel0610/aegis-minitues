import sqlite3
import os

def add_summaries_table():
    """Add a summaries table to the directors_data.db database"""
    db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the summaries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            director_name TEXT NOT NULL,
            din TEXT,
            file_path TEXT NOT NULL,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create an index on file_path for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_summaries_file_path 
        ON document_summaries (file_path)
    ''')
    
    # Create an index on director_name for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_summaries_director_name 
        ON document_summaries (director_name)
    ''')
    
    conn.commit()
    conn.close()
    print("Summaries table created successfully!")

if __name__ == "__main__":
    add_summaries_table()