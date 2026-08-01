import sqlite3
import os

def check_summaries_table():
    """Check the structure of the summaries table"""
    db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute('PRAGMA table_info(document_summaries)')
    columns = cursor.fetchall()
    print('Table structure:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check record count
    cursor.execute('SELECT COUNT(*) FROM document_summaries')
    count = cursor.fetchone()[0]
    print(f'\nRecords: {count}')
    
    conn.close()

if __name__ == "__main__":
    check_summaries_table()