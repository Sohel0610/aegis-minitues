import sqlite3

# Connect to the database
conn = sqlite3.connect('directors_data.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in the database:")
for table in tables:
    print(f"- {table[0]}")

print("\nTable structures:")

# Get structure of each table
for table_name in ['directors', 'companies', 'directorships']:
    print(f"\nTable: {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
        
    # Get sample data
    print(f"\nSample data from {table_name}:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()