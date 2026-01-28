import requests
import json

try:
    response = requests.get('/special-sheets-data/2025-08.xlsx')
    if response.status_code == 200:
        data = response.json()
        
        print("=== FULL WEEKLY TREND DATA ===")
        print(f"Total records: {len(data['weekly_trend_data'])}")
        
        # Print all records with their indices
        for i, record in enumerate(data['weekly_trend_data']):
            print(f"{i:3d}. {record}")
            
        print("\n=== COLUMN NAMES ===")
        print(data['weekly_trend_columns'])
        
        print("\n=== FIRST 10 RECORDS (excluding header) ===")
        # Skip the first record which is the header
        for i, record in enumerate(data['weekly_trend_data'][1:11]):
            print(f"{i+1:2d}. {record}")
            
        # Count total notifications
        total_notifications = 0
        for record in data['weekly_trend_data'][1:]:  # Skip header
            count_key = "Unnamed: 1"
            if count_key in record:
                count = record[count_key]
                if isinstance(count, (int, float)):
                    total_notifications += count
                elif isinstance(count, str) and count.isdigit():
                    total_notifications += int(count)
                    
        print(f"\n=== TOTAL NOTIFICATIONS ===")
        print(f"Total: {total_notifications}")
        
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Exception: {e}")