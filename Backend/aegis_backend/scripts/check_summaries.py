import sqlite3
import os

def check_summaries():
    """Check the summaries in the database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM document_summaries')
        count = cursor.fetchone()[0]
        print(f'Summaries in database: {count}')
        
        cursor.execute('SELECT file_path, LENGTH(summary) FROM document_summaries LIMIT 5')
        rows = cursor.fetchall()
        print('Sample summaries:')
        for row in rows:
            print(f'  {row[0]}: {row[1]} characters')
        
        conn.close()
    except Exception as e:
        print(f"Error checking summaries: {e}")

if __name__ == "__main__":
    check_summaries()