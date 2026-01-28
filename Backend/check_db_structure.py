import sqlite3

# Connect to the database
conn = sqlite3.connect('directors_data.db')
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

# Get counts
cursor.execute('SELECT COUNT(*) FROM directors')
print('Directors count:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM companies')
print('Companies count:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM directorships')
print('Directorships count:', cursor.fetchone()[0])

# Get sample data
print('\nSample directors:')
cursor.execute('SELECT * FROM directors LIMIT 5')
directors = cursor.fetchall()
for director in directors:
    print(director)

print('\nSample companies:')
cursor.execute('SELECT * FROM companies LIMIT 5')
companies = cursor.fetchall()
for company in companies:
    print(company)

print('\nSample directorships:')
cursor.execute('SELECT * FROM directorships LIMIT 5')
directorships = cursor.fetchall()
for directorship in directorships:
    print(directorship)

# Get companies with director counts
print('\nCompanies with director counts:')
cursor.execute('''
    SELECT c.name, c.type, COUNT(d.id) as director_count
    FROM companies c
    LEFT JOIN directorships d ON c.id = d.company_id
    GROUP BY c.id, c.name, c.type
    ORDER BY director_count DESC
    LIMIT 10
''')
companies_with_counts = cursor.fetchall()
for company in companies_with_counts:
    print(company)

conn.close()