import sqlite3
import os

def check_database_content():
    """Check the content of the document summaries in the database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check total number of records
        cursor.execute('SELECT COUNT(*) FROM document_summaries')
        total_count = cursor.fetchone()[0]
        print(f'Total records in database: {total_count}')
        
        # Check records with actual content
        cursor.execute('SELECT COUNT(*) FROM document_summaries WHERE full_text IS NOT NULL AND LENGTH(full_text) > 50')
        content_count = cursor.fetchone()[0]
        print(f'Records with substantial content: {content_count}')
        
        # Check records with summaries
        cursor.execute('SELECT COUNT(*) FROM document_summaries WHERE summary IS NOT NULL AND LENGTH(summary) > 50 AND summary NOT LIKE "Could not extract content%"')
        summary_count = cursor.fetchone()[0]
        print(f'Records with proper summaries: {summary_count}')
        
        # Show sample records
        print('\nSample records:')
        cursor.execute('SELECT file_path, LENGTH(full_text), LENGTH(summary), substr(summary, 1, 100) FROM document_summaries LIMIT 5')
        rows = cursor.fetchall()
        for row in rows:
            print(f'  File: {row[0]}')
            print(f'    Full text length: {row[1]} characters')
            print(f'    Summary length: {row[2]} characters')
            print(f'    Summary preview: {row[3]}...')
            print()
        
        # Check one detailed record
        print('Detailed check of first record:')
        cursor.execute('SELECT director_name, din, file_path, full_text, summary FROM document_summaries LIMIT 1')
        row = cursor.fetchone()
        if row:
            print(f'  Director: {row[0]}')
            print(f'  DIN: {row[1]}')
            print(f'  File: {row[2]}')
            print(f'  Full text length: {len(row[3]) if row[3] else 0} characters')
            print(f'  Summary length: {len(row[4]) if row[4] else 0} characters')
            if row[4]:
                print(f'  Summary preview: {row[4][:200]}...')
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database content: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_content()