
import os
import sqlite3
import random

def create_dummy_data():
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public_dir = os.path.join(base_dir, "public")
    insider_dir = os.path.join(public_dir, "AdaniInsiderTraders")
    
    # Create main directory if not exists
    if not os.path.exists(insider_dir):
        os.makedirs(insider_dir)
        print(f"Created directory: {insider_dir}")
     
    # Define companies to create dummy data for
    companies = ["AdaniGreen", "AdaniEnt", "AdaniPower", "AmbujaCements"]
    
    for company in companies:
        company_folder = f"user_{company}"
        company_path = os.path.join(insider_dir, company_folder)
        
        if not os.path.exists(company_path):
            os.makedirs(company_path)
            print(f"Created company folder: {company_path}")
            
        # Create a database file simulating a depository file
        db_file = os.path.join(company_path, f"BENPOS-CDSL_{company}.db")
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 1. Create Summary Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Summary (
                STATUS TEXT,
                COUNT INTEGER
            )
        ''')
        
        # Populate Summary
        summary_data = [
            ('ADDED', random.randint(5, 50)),
            ('REMOVED', random.randint(5, 50)),
            ('CHANGED', random.randint(10, 100)),
            ('UNCHANGED', random.randint(100, 500))
        ]
        cursor.executemany("INSERT INTO Summary (STATUS, COUNT) VALUES (?, ?)", summary_data)
        
        # 2. Create All_Data Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS All_Data (
                id INTEGER PRIMARY KEY,
                POSITION_latest INTEGER
            )
        ''')
        
        # Populate All_Data (dummy records for total count and shares)
        total_records = sum(x[1] for x in summary_data)
        all_data = [(random.randint(100, 10000),) for _ in range(total_records)]
        cursor.executemany("INSERT INTO All_Data (POSITION_latest) VALUES (?)", all_data)
        
        # 3. Create Added Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Added (
                PANGIR1 TEXT,
                NAME1_latest TEXT,
                EMAIL1_latest TEXT,
                POSITION_latest INTEGER,
                POSITION_older INTEGER,
                POSITION_DIFFERENCE INTEGER,
                STATUS TEXT
            )
        ''')
        
        # Populate Added
        added_count = summary_data[0][1]
        added_rows = []
        for i in range(added_count):
            shares = random.randint(100, 5000)
            added_rows.append((
                f"ABCDE{random.randint(1000,9999)}A",
                f"Investor {i}",
                f"investor{i}@example.com",
                shares,
                0,
                shares,
                "ADDED"
            ))
        cursor.executemany("INSERT INTO Added VALUES (?, ?, ?, ?, ?, ?, ?)", added_rows)
        
        # 4. Create Removed Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Removed (
                PANGIR1 TEXT,
                NAME1_older TEXT,
                EMAIL1_older TEXT,
                POSITION_latest INTEGER,
                POSITION_older INTEGER,
                POSITION_DIFFERENCE INTEGER,
                STATUS TEXT
            )
        ''')
        
        # Populate Removed
        removed_count = summary_data[1][1]
        removed_rows = []
        for i in range(removed_count):
            shares = random.randint(100, 5000)
            removed_rows.append((
                f"FGHIJ{random.randint(1000,9999)}B",
                f"Exited Investor {i}",
                f"exited{i}@example.com",
                0,
                shares,
                -shares,
                "REMOVED"
            ))
        cursor.executemany("INSERT INTO Removed VALUES (?, ?, ?, ?, ?, ?, ?)", removed_rows)
        
        # 5. Create Changed Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Changed (
                PANGIR1 TEXT,
                NAME1_latest TEXT,
                EMAIL1_latest TEXT,
                POSITION_latest INTEGER,
                POSITION_older INTEGER,
                POSITION_DIFFERENCE INTEGER,
                STATUS TEXT
            )
        ''')
        
        # Populate Changed
        changed_count = summary_data[2][1]
        changed_rows = []
        for i in range(changed_count):
            old_shares = random.randint(1000, 10000)
            diff = random.randint(-500, 500)
            if diff == 0: diff = 10 # ensure change
            new_shares = old_shares + diff
            changed_rows.append((
                f"KLMNO{random.randint(1000,9999)}C",
                f"Active Trader {i}",
                f"trader{i}@example.com",
                new_shares,
                old_shares,
                diff,
                "CHANGED"
            ))
        cursor.executemany("INSERT INTO Changed VALUES (?, ?, ?, ?, ?, ?, ?)", changed_rows)
        
        conn.commit()
        conn.close()
        print(f"Created database: {db_file}")

if __name__ == "__main__":
    create_dummy_data()
