import sqlite3
import os

# Connect to the email database
db_path = "email_data.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create admin_credentials table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert default admin user if it doesn't exist
    cursor.execute("""
        INSERT OR IGNORE INTO admin_credentials (username, password)
        VALUES (?, ?)
    """, ("admin@aegis.com", "aegis"))
    
    # Commit changes
    conn.commit()
    
    # Verify the admin user was inserted
    cursor.execute("SELECT * FROM admin_credentials WHERE username = ?", ("admin@aegis.com",))
    admin_user = cursor.fetchone()
    
    if admin_user:
        print("Default admin user created successfully:")
        print(f"  ID: {admin_user[0]}")
        print(f"  Username: {admin_user[1]}")
        print(f"  Password: {admin_user[2]}")
        print(f"  Created at: {admin_user[3]}")
    else:
        print("Failed to create default admin user")
        
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")