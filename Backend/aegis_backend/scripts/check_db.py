import sqlite3

# Connect to the database
conn = sqlite3.connect('directors_data.db')
cursor = conn.cursor()

# Check what tables exist
print("=== DATABASE TABLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table[0])

# Check the first few entries of each table to understand the structure
for table in tables:
    if table[0] != 'sqlite_sequence':  # Skip internal SQLite table
        print(f"\n=== SAMPLE DATA FROM {table[0]} ===")
        try:
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3;")
            rows = cursor.fetchall()
            # Get column names
            column_names = [description[0] for description in cursor.description]
            print("Columns:", column_names)
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error reading table {table[0]}: {e}")

conn.close()