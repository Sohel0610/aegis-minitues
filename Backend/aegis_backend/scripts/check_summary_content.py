import sqlite3
import os

def check_summary_content():
    """Check the actual content of a summary"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT summary FROM document_summaries WHERE file_path = "Abhilash Mehta_MBP.docx"')
        summary = cursor.fetchone()[0]
        print(f"Summary content: {summary}")
        
        conn.close()
    except Exception as e:
        print(f"Error checking summary content: {e}")

if __name__ == "__main__":
    check_summary_content()