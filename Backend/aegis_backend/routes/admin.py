# Admin Route Module
# This module handles admin authentication and email management using PostgreSQL
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
import asyncio
import concurrent.futures
import urllib.parse
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for admin endpoints
router = APIRouter()

# Schema for RBAC
PG_SCHEMA = "rbac"

# Request model for admin login
class AdminLoginRequest(BaseModel):
    username: str
    password: str

# Response model for admin login
class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None

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
    """Authenticate admin user from PostgreSQL."""
    try:
        def verify():
            conn = get_pg_connection()
            if not conn: raise RuntimeError("Database connection failed")
            cursor = get_pg_cursor(conn)
            try:
                # In production, use hashed passwords!
                cursor.execute("SELECT id FROM admin_credentials WHERE username = %s AND password = %s",
                             (credentials.username, credentials.password))
                res = cursor.fetchone()
                return res["id"] if res else None
            finally:
                conn.close()
        
        adm_id = await asyncio.get_event_loop().run_in_executor(thread_pool, verify)
        if adm_id:
            return AdminLoginResponse(success=True, message="Login successful", token=f"admin_tok_{adm_id}")
        return AdminLoginResponse(success=False, message="Invalid credentials")
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get all allowed emails
@router.get("/emails", response_model=EmailListResponse)
async def get_emails(search: Optional[str] = None):
    """Get all email addresses from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection()
            if not conn: return []
            cursor = get_pg_cursor(conn)
            try:
                if search:
                    cursor.execute("SELECT email FROM allowed_emails WHERE email ILIKE %s ORDER BY email", (f"%{search}%",))
                else:
                    cursor.execute("SELECT email FROM allowed_emails ORDER BY email")
                rows = cursor.fetchall()
                return [r["email"] for r in rows]
            finally:
                conn.close()
        
        emails = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return EmailListResponse(emails=emails, count=len(emails))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emails", response_model=EmailResponse)
async def add_email(email_entry: EmailEntry):
    """Add a new allowed email address to PostgreSQL."""
    email_lower = email_entry.email.lower().strip()
    if not (email_lower.endswith('@adani.com') or email_lower.endswith('@pspprojects.com')):
         raise HTTPException(status_code=400, detail="Invalid domain")
         
    try:
        def add():
            conn = get_pg_connection()
            if not conn: raise RuntimeError("DB Error")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("INSERT INTO allowed_emails (email) VALUES (%s) ON CONFLICT DO NOTHING", (email_lower,))
                conn.commit()
            finally:
                conn.close()
        await asyncio.get_event_loop().run_in_executor(thread_pool, add)
        return EmailResponse(email=email_lower)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/emails/{email_address}", response_model=EmailResponse)
async def delete_email(email_address: str):
    email = urllib.parse.unquote(email_address).lower().strip()
    try:
        def delete():
            conn = get_pg_connection()
            if not conn: raise RuntimeError("DB Error")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("DELETE FROM allowed_emails WHERE email = %s", (email,))
                conn.commit()
            finally:
                conn.close()
        await asyncio.get_event_loop().run_in_executor(thread_pool, delete)
        return EmailResponse(email=email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))