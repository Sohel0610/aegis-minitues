import sqlite3
import os

# Path to the visits database
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'public', 'visits.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query the visits table
cursor.execute("SELECT * FROM visits")
rows = cursor.fetchall()

# Print the results
print("Visits table contents:")
for row in rows:
    print(row)

# Close the connection
conn.close()