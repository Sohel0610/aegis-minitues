import sqlite3
import os

# Connect to the email database
db_path = os.path.join("email_data.db")

conn = None
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in the database:")
    for table in tables:
        print(f"  - {table[0]}")
        
    # Check if admin_credentials table exists
    cursor.execute("PRAGMA table_info(admin_credentials)")
    columns = cursor.fetchall()
    
    if columns:
        print("\nadmin_credentials table structure:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
    else:
        print("\nadmin_credentials table does not exist")
        
    # Check if we have any admin users
    try:
        cursor.execute("SELECT COUNT(*) FROM admin_credentials")
        count = cursor.fetchone()[0]
        print(f"\nNumber of admin users: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, username FROM admin_credentials")
            admins = cursor.fetchall()
            print("Admin users:")
            for admin in admins:
                print(f"  - ID: {admin[0]}, Username: {admin[1]}")
    except sqlite3.OperationalError as e:
        print(f"\nError querying admin_credentials: {e}")
        
except Exception as e:
    print(f"Error connecting to database: {e}")
finally:
    if conn:
        conn.close()