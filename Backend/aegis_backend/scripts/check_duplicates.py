import sqlite3

# Connect to the database
conn = sqlite3.connect('directors_data.db')
cursor = conn.cursor()

# First, let's see what tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(f"  - {table[0]}")

# Check for company names in the database
# Let's assume there's a table with company information
# We'll try common table names
possible_tables = ['companies', 'company', 'directors', 'director']

for table_name in possible_tables:
    try:
        # Try to get company names from the table
        cursor.execute(f"SELECT name FROM {table_name} LIMIT 5;")
        sample_data = cursor.fetchall()
        print(f"\nSample data from '{table_name}' table:")
        for row in sample_data:
            print(f"  - {row[0]}")
    except sqlite3.OperationalError:
        # Table doesn't exist
        continue

# Let's try to find company names in any table
print("\nChecking for duplicate company names...")
try:
    # This query looks for duplicate company names across the database
    # We'll need to adjust this based on the actual schema
    cursor.execute("""
        SELECT name, COUNT(*) as count 
        FROM (
            SELECT 'company_name' as name FROM sqlite_master WHERE type='table'
            UNION ALL
            SELECT name FROM sqlite_master WHERE type='table'
        ) 
        GROUP BY name 
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print("Duplicate company names found:")
        for name, count in duplicates:
            print(f"  - {name} (appears {count} times)")
    else:
        print("No obvious duplicates found with this query.")
        
except sqlite3.OperationalError as e:
    print(f"Query error: {e}")

conn.close()
print("\nDatabase check complete.")