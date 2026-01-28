import sqlite3
import os
from collections import defaultdict

def test_full_monthly_data():
    """Test that all months are properly processed for the chart"""
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
        
        # Find min and max years
        years = set()
        for key in month_year_set:
            year = int(key.split('-')[1])
            years.add(year)
        
        min_year = min(years) if years else 2025
        max_year = max(years) if years else 2025
        
        print(f"Year range: {min_year} to {max_year}")
        
        # Create complete month-year set
        complete_month_year_set = set()
        for year in range(min_year, max_year + 1):
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for month in month_names:
                complete_month_year_set.add(f"{month}-{year}")
        
        # Add missing months with 0 count
        for key in complete_month_year_set:
            if key not in monthly_map:
                monthly_map[key] = 0
        
        # Sort all months
        sorted_months = sorted(list(complete_month_year_set), key=lambda x: (
            int(x.split('-')[1]),  # year
            ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(x.split('-')[0])  # month
        ))
        
        print("\nAll months with notification counts:")
        for month_key in sorted_months:
            count = monthly_map.get(month_key, 0)
            status = "NO DATA" if count == 0 else f"{count} notifications"
            print(f"  {month_key}: {count} ({status})")
            
        conn.close()
        
        # Verify August is in the data
        aug_2025_key = "Aug-2025"
        if aug_2025_key in monthly_map:
            print(f"\n✓ August 2025 data found: {monthly_map[aug_2025_key]} notifications")
        else:
            print(f"\n✗ August 2025 data NOT found")
            
    except Exception as e:
        print(f"Error testing full monthly data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_monthly_data()