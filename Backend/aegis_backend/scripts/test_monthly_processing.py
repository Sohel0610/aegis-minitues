import sqlite3
import os
from collections import defaultdict

def test_monthly_processing():
    """Test the monthly data processing logic"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'public', 'notifications.db')
        print(f"Database path: {db_path}")
        
        if not os.path.exists(db_path):
            print("Database file not found!")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all records with valid links and dates
        cursor.execute("""
            SELECT Date 
            FROM DailyLogs 
            WHERE Date IS NOT NULL 
            AND Link IS NOT NULL 
            AND Link != 'NIL'
            ORDER BY Date
        """)
        rows = cursor.fetchall()
        
        print(f"Total records with valid links and dates: {len(rows)}")
        
        # Group by month-year for monthly chart
        monthly_map = {}
        month_year_set = set()
        
        for row in rows:
            date = row[0]  # Date column
            if date:
                try:
                    # Parse YYYY-MM-DD format
                    parts = date.split('-')
                    if len(parts) == 3:
                        year = int(parts[0])
                        month = int(parts[1]) - 1  # JS months are 0-indexed
                        day = int(parts[2])
                        
                        # Create month-year key (e.g., "Sep-2025")
                        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_name = month_names[month] if 0 <= month < 12 else 'Unknown'
                        key = f"{month_name}-{year}"
                        
                        # Add to set of unique month-year combinations
                        month_year_set.add(key)
                        
                        if key not in monthly_map:
                            monthly_map[key] = 0
                        monthly_map[key] += 1
                except Exception as e:
                    print(f"Error parsing date {date}: {e}")
        
        # Sort month-year combinations
        sorted_months = sorted(list(month_year_set), key=lambda x: (
            int(x.split('-')[1]),  # year
            ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(x.split('-')[0])  # month
        ))
        
        print("\nMonthly data:")
        for month_key in sorted_months:
            print(f"  {month_key}: {monthly_map.get(month_key, 0)} records")
            
        conn.close()
        
    except Exception as e:
        print(f"Error testing monthly processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monthly_processing()