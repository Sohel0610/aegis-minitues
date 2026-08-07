import sqlite3

# Connect to the database
conn = sqlite3.connect('directors_data.db')
cursor = conn.cursor()

print("=== CHECKING FOR DUPLICATE COMPANY NAMES ===")

# Check for duplicate company names in the companies table
cursor.execute("""
    SELECT name, COUNT(*) as count 
    FROM companies 
    GROUP BY name 
    HAVING COUNT(*) > 1
    ORDER BY count DESC
""")

duplicates = cursor.fetchall()

if duplicates:
    print(f"Found {len(duplicates)} duplicate company names:")
    for name, count in duplicates:
        print(f"  - {name} (appears {count} times)")
else:
    print("No duplicate company names found.")

print("\n=== CHECKING FOR SIMILAR COMPANY NAMES (potential duplicates) ===")

# Check for company names that are very similar (might be duplicates with slight variations)
cursor.execute("""
    SELECT name, COUNT(*) as count 
    FROM companies 
    GROUP BY UPPER(TRIM(name)) 
    HAVING COUNT(*) > 1
    ORDER BY count DESC
""")

similar_names = cursor.fetchall()

if similar_names:
    print(f"Found {len(similar_names)} groups of similar company names:")
    for name, count in similar_names:
        print(f"  - {name} (appears {count} times)")
else:
    print("No similar company names found.")

# Get total count of companies
cursor.execute("SELECT COUNT(*) FROM companies")
total_companies = cursor.fetchone()[0]
print(f"\nTotal companies in database: {total_companies}")

conn.close()
print("\nDuplicate check complete.")