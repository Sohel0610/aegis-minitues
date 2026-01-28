import sqlite3

# Connect to the database
conn = sqlite3.connect('directors_data.db')
cursor = conn.cursor()

# Get company types
cursor.execute('SELECT type, COUNT(*) FROM companies GROUP BY type')
results = cursor.fetchall()

print('Company types:')
for r in results:
    print(f'  {r[0]}: {r[1]}')

# Get sample companies by type
print('\nSample companies by type:')
for r in results:
    print(f'\n{r[0]} companies:')
    cursor.execute('SELECT name FROM companies WHERE type = ? LIMIT 3', (r[0],))
    companies = cursor.fetchall()
    for company in companies:
        print(f'  - {company[0]}')

conn.close()