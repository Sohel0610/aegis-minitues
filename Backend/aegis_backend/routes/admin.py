# Admin Route Module
# This module handles admin authentication and email management functionality
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
import urllib.parse

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for admin endpoints
router = APIRouter()

# Request model for admin login
class AdminLoginRequest(BaseModel):
    username: str
    password: str

# Response model for admin login
class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None

# Response model for admin credentials
class AdminCredentialsResponse(BaseModel):
    id: int
    username: str

# Request model for email entry
class EmailEntry(BaseModel):
    email: str

# Response model for email operations
class EmailResponse(BaseModel):
    email: str

# Response model for email list
class EmailListResponse(BaseModel):
    emails: List[str]
    count: int

# Endpoint to authenticate admin user
@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLoginRequest):
    """Authenticate admin user"""
    try:
        # Define path to the email database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "email_data.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Database file not found")
        
        # Connect to the database and verify credentials
        def verify_admin_credentials():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the provided credentials match any admin user
            cursor.execute("""
                SELECT id, username FROM admin_credentials 
                WHERE username = ? AND password = ?
            """, (credentials.username, credentials.password))
            
            result = cursor.fetchone()
            conn.close()
            
            return result
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        admin_user = await loop.run_in_executor(thread_pool, verify_admin_credentials)
        
        if admin_user:
            # In a real application, you would generate a proper JWT token
            # For now, we'll just return a success response
            return AdminLoginResponse(
                success=True,
                message="Login successful",
                token=f"admin_token_{admin_user[0]}"  # Simple token for demonstration
            )
        else:
            return AdminLoginResponse(
                success=False,
                message="Invalid credentials"
            )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error during admin login: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to authenticate: {error_message}")

# Endpoint to get all email addresses with optional search filter
@router.get("/emails", response_model=EmailListResponse)
async def get_emails(search: Optional[str] = None):
    """Get all email addresses with optional search filter"""
    try:
        # Define path to the email database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "email_data.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Database file not found")
        
        # Connect to the database and fetch emails
        def fetch_emails():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Build query with optional search filter
            if search:
                # Case-insensitive search in email column
                query = "SELECT email FROM email WHERE LOWER(email) LIKE LOWER(?) ORDER BY email"
                search_pattern = f"%{search}%"
                cursor.execute(query, (search_pattern,))
            else:
                # Get all emails
                cursor.execute("SELECT email FROM email ORDER BY email")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        emails = await loop.run_in_executor(thread_pool, fetch_emails)
        
        return EmailListResponse(
            emails=emails,
            count=len(emails)
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error fetching emails: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {error_message}")

# Endpoint to add a new email address (admin only)
@router.post("/emails", response_model=EmailResponse)
async def add_email(email_entry: EmailEntry):
    """Add a new email address (admin only)"""
    try:
        # Validate email format
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email_entry.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate that email is from adani.com or pspprojects.com domain (case-insensitive)
        email_lower = email_entry.email.lower()
        if not email_lower.endswith('@adani.com') and not email_lower.endswith('@pspprojects.com'):
            raise HTTPException(status_code=400, detail="Only emails from adani.com or pspprojects.com domains are allowed")
        
        # Define path to the email database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "email_data.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Database file not found")
        
        # Connect to the database and add email
        def add_email_to_db():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if email already exists (case-insensitive)
            cursor.execute("SELECT COUNT(*) FROM email WHERE LOWER(email) = LOWER(?)", (email_entry.email,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                conn.close()
                raise HTTPException(status_code=409, detail="Email already exists")
            
            # Insert new email
            cursor.execute("INSERT INTO email (email) VALUES (?)", (email_entry.email,))
            conn.commit()
            conn.close()
            
            return email_entry.email
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        email = await loop.run_in_executor(thread_pool, add_email_to_db)
        
        return EmailResponse(email=email)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error adding email: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to add email: {error_message}")

# Endpoint to delete an email address (admin only)
@router.delete("/emails/{email_address}", response_model=EmailResponse)
async def delete_email(email_address: str):
    """Delete an email address (admin only)"""
    try:
        # Decode URL encoded email address
        email = urllib.parse.unquote(email_address)
        
        # Define path to the email database file
        db_path = os.path.join(os.path.dirname(__file__), "..", "public", "email_data.db")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Database file not found")
        
        # Connect to the database and delete email
        def delete_email_from_db():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute("SELECT COUNT(*) FROM email WHERE email = ?", (email,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                conn.close()
                raise HTTPException(status_code=404, detail="Email not found")
            
            # Delete the email
            cursor.execute("DELETE FROM email WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            
            return email
        
        # Run the database operation in a thread pool
        loop = asyncio.get_event_loop()
        deleted_email = await loop.run_in_executor(thread_pool, delete_email_from_db)
        
        return EmailResponse(email=deleted_email)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error deleting email: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {error_message}")