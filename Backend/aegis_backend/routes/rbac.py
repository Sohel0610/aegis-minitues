"""
RBAC (Role-Based Access Control) Route Module
This module handles route-based permission management and access requests using PostgreSQL.
No more SQLite legacy.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import logging
import asyncio
import concurrent.futures
from datetime import datetime
import json
from utils.pgsql_service import get_pg_connection, get_pg_cursor
from utils.email_service import (
    send_email, 
    get_admin_request_template, 
    get_user_confirmation_template, 
    ADMIN_EMAILS,
    format_application_name
)

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for RBAC endpoints
router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

class RoutePermission(BaseModel):
    email: EmailStr
    route_path: str
    permission_type: str
    can_view: bool = False
    can_edit: bool = False
    can_admin: bool = False

class UserPermissionsResponse(BaseModel):
    email: str
    permissions: List[Dict[str, Any]]
    accessible_routes: List[str]

class PermissionCheckResponse(BaseModel):
    has_access: bool
    permission_type: Optional[str] = None
    can_view: bool = False
    can_edit: bool = False
    can_admin: bool = False
    message: Optional[str] = None
    can_request_access: bool = True

class AssignPermissionRequest(BaseModel):
    email: EmailStr
    route: str
    permission_type: str
    notes: Optional[str] = None

class RevokePermissionRequest(BaseModel):
    email: EmailStr
    route: str

class AccessRequestSubmit(BaseModel):
    email: EmailStr
    name: str
    requested_route: str
    requested_permission: str
    justification: str

class AccessRequestResponse(BaseModel):
    id: int
    email: str
    name: str
    requested_route: str
    requested_permission: str
    justification: str
    status: str
    requested_at: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None

class ReviewAccessRequestRequest(BaseModel):
    review_notes: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

def init_rbac_pg_tables():
    """Verify and initialize the RBAC tables in PostgreSQL."""
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            
            # Route Definitions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS route_definitions (
                    route_path TEXT PRIMARY KEY,
                    display_name TEXT,
                    module_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Route Permissions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS route_permissions (
                    email TEXT NOT NULL,
                    route_path TEXT NOT NULL,
                    permission_type TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_by TEXT,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    PRIMARY KEY (email, route_path)
                )
            """)
            
            # Access Requests Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_requests (
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    name TEXT,
                    requested_route TEXT NOT NULL,
                    requested_permission TEXT NOT NULL,
                    justification TEXT,
                    status TEXT DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_by TEXT,
                    reviewed_at TIMESTAMP,
                    review_notes TEXT
                )
            """)

            # Auth Audit Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_audit_logs (
                    id SERIAL PRIMARY KEY,
                    email TEXT,
                    event_type TEXT,
                    event_details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    application TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Admin Credentials (for explicit admin login)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_credentials (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Allowed Emails list
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS allowed_emails (
                    email TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("RBAC PostgreSQL tables verified")
        except Exception as e:
            conn.rollback()
            logger.error(f"RBAC init error: {e}")
        finally:
            conn.close()

def log_auth_event(email: str, event_type: str, details: str, request: Request = None):
    """Log an authentication event to PostgreSQL."""
    try:
        ip = request.client.host if request else None
        ua = request.headers.get("user-agent") if request else None
        
        def insert():
            conn = get_pg_connection()
            if conn:
                try:
                    cursor = get_pg_cursor(conn)
                    cursor.execute("""
                        INSERT INTO auth_audit_logs (email, event_type, event_details, ip_address, user_agent, application)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (email, event_type, details, ip, ua, "Aegis Platform"))
                    conn.commit()
                finally:
                    conn.close()
        
        asyncio.get_event_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        logger.error(f"Failed to log auth event: {e}")

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/rbac/my-permissions", response_model=UserPermissionsResponse)
async def get_my_permissions(email: str):
    """Retrieve all route permissions for a specific user."""
    try:
        def fetch():
            conn = get_pg_connection()
            if not conn: return [], []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT rp.route_path, rp.permission_type, rd.display_name
                    FROM route_permissions rp
                    LEFT JOIN route_definitions rd ON rp.route_path = rd.route_path
                    WHERE LOWER(rp.email) = LOWER(%s) AND rp.is_active = TRUE
                """, (email,))
                rows = cursor.fetchall()
                perms = []
                routes = []
                for row in rows:
                    perms.append({
                        "route": row["route_path"],
                        "permission": row["permission_type"],
                        "name": row["display_name"] or row["route_path"]
                    })
                    routes.append(row["route_path"])
                return perms, routes
            finally:
                conn.close()
        
        perms, routes = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return UserPermissionsResponse(email=email, permissions=perms, accessible_routes=routes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rbac/check-access", response_model=PermissionCheckResponse)
@router.post("/rbac/check-access", response_model=PermissionCheckResponse)
async def check_route_access(email: str, route: str):
    """Check if a user has access to a specific route."""
    # Sanitize route
    clean_route = route.split('?')[0].rstrip('/')
    
    try:
        def check():
            conn = get_pg_connection()
            if not conn: return None
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT permission_type FROM route_permissions
                    WHERE LOWER(email) = LOWER(%s) AND route_path = %s AND is_active = TRUE
                """, (email, clean_route))
                row = cursor.fetchone()
                return row["permission_type"] if row else None
            finally:
                conn.close()
        
        perm = await asyncio.get_event_loop().run_in_executor(thread_pool, check)
        
        if perm:
            return PermissionCheckResponse(
                has_access=True, 
                permission_type=perm,
                can_view=True,
                can_edit=(perm in ('edit', 'admin')),
                can_admin=(perm == 'admin'),
                message="Access granted"
            )
        
        return PermissionCheckResponse(has_access=False, message="Access denied", can_request_access=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rbac/assign", response_model=Dict[str, Any])
async def assign_permission(req: AssignPermissionRequest):
    """Assign a route permission to a user."""
    try:
        def assign():
            conn = get_pg_connection()
            if not conn: return False
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    INSERT INTO route_permissions (email, route_path, permission_type, assigned_by, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (email, route_path) 
                    DO UPDATE SET permission_type = EXCLUDED.permission_type, notes = EXCLUDED.notes, is_active = TRUE
                """, (req.email.lower(), req.route, req.permission_type, "System Admin", req.notes))
                conn.commit()
                return True
            finally:
                conn.close()
        
        success = await asyncio.get_event_loop().run_in_executor(thread_pool, assign)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rbac/request-access", response_model=Dict[str, Any])
async def submit_access_request(req: AccessRequestSubmit):
    """Submit a request for route access."""
    try:
        def request_access():
            conn = get_pg_connection()
            if not conn: return None
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT 1 FROM access_requests WHERE LOWER(email) = LOWER(%s) AND requested_route = %s AND status = 'pending'", (req.email, req.requested_route))
                if cursor.fetchone():
                     return "duplicate"
                
                cursor.execute("INSERT INTO access_requests (email, name, requested_route, requested_permission, justification) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                             (req.email.lower(), req.name, req.requested_route, req.requested_permission, req.justification))
                req_id = cursor.fetchone()["id"]
                conn.commit()
                return req_id
            finally:
                conn.close()
        
        res = await asyncio.get_event_loop().run_in_executor(thread_pool, request_access)
        
        if res == "duplicate":
            return {"success": False, "message": "A pending request for this route already exists."}
            
        if res:
            # Trigger background email notification
            try:
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, send_access_request_emails, req.email, req.name, req.requested_route, req.requested_permission, req.justification)
            except Exception as e:
                logger.error(f"Email notification failed: {e}")
                
            return {"success": True, "request_id": res}
            
        return {"success": False, "message": "Failed to submit request"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def send_access_request_emails(email, name, route, perm, justification):
    """Send emails to admins about the new request and a confirmation to the user."""
    try:
        app_name = format_application_name(route)
        
        # 1. Notify Admins
        admin_content = get_admin_request_template(name, email, app_name, perm, justification)
        send_email(
            to_emails=ADMIN_EMAILS,
            subject=f"New Access Request: {app_name} ({name})",
            body=admin_content
        )
        
        # 2. Confirm to User
        user_content = get_user_confirmation_template(name, app_name)
        send_email(
            to_emails=[email],
            subject=f"Access Request Received: {app_name}",
            body=user_content
        )
    except Exception as e:
        logger.error(f"RBAC Email Sync Error: {e}")

@router.get("/rbac/requests", response_model=List[AccessRequestResponse])
async def get_all_requests():
    """Get all access requests from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection()
            if not conn: return []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT id, email, name, requested_route, requested_permission, justification, status, requested_at, reviewed_by, reviewed_at, review_notes FROM access_requests ORDER BY requested_at DESC")
                rows = cursor.fetchall()
                return [AccessRequestResponse(**{k: (str(v) if v and k in ('requested_at', 'reviewed_at') else v) for k, v in dict(r).items()}) for r in rows]
            finally:
                conn.close()
        return await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
