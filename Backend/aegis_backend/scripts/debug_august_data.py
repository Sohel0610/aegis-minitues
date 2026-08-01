import sqlite3
import os
from collections import defaultdict

def debug_august_data():
    """Debug the August data processing"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'public', 'notifications.db')
        print(f"Database path: {db_path}")
        
        if not os.path.exists(db_path):
            print("Database file not found!")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all August 2025 records with valid links
        cursor.execute("""
            SELECT SrNo, EntityName, Link, Nature, Summary, Date 
            FROM DailyLogs 
            WHERE Date IS NOT NULL 
            AND strftime('%m', Date) = '08' 
            AND strftime('%Y', Date) = '2025'
            AND Link IS NOT NULL 
            AND Link != 'NIL'
            ORDER BY Date
        """)
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} August 2025 records with valid links")
        
        # Group by date to see distribution
        date_count = defaultdict(int)
        for row in rows:
            date = row[5]  # Date column
            date_count[date] += 1
            
        print("\nAugust 2025 records by date:")
        for date in sorted(date_count.keys()):
            print(f"  {date}: {date_count[date]} records")
            
        # Check some sample records
        print("\nSample records:")
        for i, row in enumerate(rows[:10]):
            print(f"  {i+1}. Date: {row[5]}, Entity: {row[1][:50]}, Link: {row[2][:50]}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error debugging August data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_august_data()