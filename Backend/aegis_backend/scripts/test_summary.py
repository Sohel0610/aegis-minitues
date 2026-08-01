import os
import sqlite3
import sys

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from llm_utils import get_summary_from_db

# Test the summary retrieval and display
def test_summary():
    # Connect to the database
    db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get a sample record
    cursor.execute('''
        SELECT file_path, summary FROM document_summaries LIMIT 1
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        file_path, summary = result
        print(f"File: {file_path}")
        print("=" * 50)
        print("Summary from database:")
        print(summary)
        print("=" * 50)
        print("Summary with repr (to see special characters):")
        print(repr(summary))
    else:
        print("No summary found in database")

if __name__ == "__main__":
    test_summary()