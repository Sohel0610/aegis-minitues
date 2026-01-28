import sqlite3
import os
from collections import defaultdict

def check_notifications_db():
    """Check the content of the notifications database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'public', 'notifications.db')
        print(f"Database path: {db_path}")
        
        if not os.path.exists(db_path):
            print("Database file not found!")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # Check DailyLogs table structure
        cursor.execute("PRAGMA table_info(DailyLogs)")
        columns = cursor.fetchall()
        print("\nDailyLogs table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check total number of records
        cursor.execute('SELECT COUNT(*) FROM DailyLogs')
        total_count = cursor.fetchone()[0]
        print(f'\nTotal records in DailyLogs: {total_count}')
        
        # Check records with valid links
        cursor.execute("SELECT COUNT(*) FROM DailyLogs WHERE Link IS NOT NULL AND Link != 'NIL'")
        valid_link_count = cursor.fetchone()[0]
        print(f'Records with valid links: {valid_link_count}')
        
        # Check date range
        cursor.execute("SELECT MIN(Date), MAX(Date) FROM DailyLogs WHERE Date IS NOT NULL")
        min_date, max_date = cursor.fetchone()
        print(f'Date range: {min_date} to {max_date}')
        
        # Check distinct months and years
        cursor.execute("""
            SELECT DISTINCT 
                strftime('%Y', Date) as year,
                strftime('%m', Date) as month,
                strftime('%Y-%m', Date) as year_month
            FROM DailyLogs 
            WHERE Date IS NOT NULL
            ORDER BY year_month
        """)
        months = cursor.fetchall()
        print(f"\nAvailable months in data:")
        for month in months:
            print(f"  {month[0]}-{month[1]} ({month[2]})")
        
        # Check August data specifically
        cursor.execute("""
            SELECT COUNT(*) 
            FROM DailyLogs 
            WHERE Date IS NOT NULL AND strftime('%m', Date) = '08'
        """)
        aug_count = cursor.fetchone()[0]
        print(f"\nTotal August records: {aug_count}")
        
        # Check August data by year
        cursor.execute("""
            SELECT 
                strftime('%Y', Date) as year,
                COUNT(*) as count
            FROM DailyLogs 
            WHERE Date IS NOT NULL AND strftime('%m', Date) = '08'
            GROUP BY strftime('%Y', Date)
            ORDER BY year
        """)
        aug_by_year = cursor.fetchall()
        print(f"August records by year:")
        for year_data in aug_by_year:
            print(f"  {year_data[0]}: {year_data[1]} records")
        
        # Show sample August records
        print('\nSample August records:')
        cursor.execute("""
            SELECT SrNo, EntityName, Link, Nature, Summary, Date 
            FROM DailyLogs 
            WHERE Date IS NOT NULL AND strftime('%m', Date) = '08'
            LIMIT 5
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f"  Date: {row[5]}, Entity: {row[1]}, Nature: {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking notifications database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_notifications_db()