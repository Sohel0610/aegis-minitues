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
rbac_router = APIRouter()
router = rbac_router # Alias for backward compatibility if needed

logger.info("RBAC Router initialized")

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

class RouteDefinitionResponse(BaseModel):
    route_path: str
    route: str # Added for frontend compatibility
    display_name: str
    module_name: Optional[str] = None

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

class GrantRoleRequest(BaseModel):
    target_email: str
    role: str = "admin"

class RevokeRoleRequest(BaseModel):
    target_email: str

class AuditLogResponse(BaseModel):
    id: int
    email: Optional[str]
    event_type: Optional[str]
    event_details: Optional[Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    application: Optional[str]
    created_at: str

class AuditLogsListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int

# ============================================================================
# Helper Functions
# ============================================================================

def init_rbac_pg_tables():
    """Verify and initialize the RBAC tables in PostgreSQL."""
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            
            # Create schema if not exists
            cursor.execute("CREATE SCHEMA IF NOT EXISTS rbac")
            
            # Route Definitions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rbac.route_definitions (
                    route_path TEXT PRIMARY KEY,
                    route_name TEXT NOT NULL,
                    display_name TEXT,
                    module_name TEXT,
                    description TEXT,
                    application TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Route Permissions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rbac.route_permissions (
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
                CREATE TABLE IF NOT EXISTS rbac.access_requests (
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
                CREATE TABLE IF NOT EXISTS rbac.auth_audit_logs (
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
            
            # Ensure created_at exists (migration for older tables)
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='rbac' AND table_name='auth_audit_logs' AND column_name='created_at') THEN
                        ALTER TABLE rbac.auth_audit_logs ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    END IF;
                END $$;
            """)

            # Admin Credentials (for explicit admin login)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rbac.admin_credentials (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Allowed Emails list
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rbac.allowed_emails (
                    email TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Platform User Roles (global roles like 'admin')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rbac.user_roles (
                    email TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'admin',
                    granted_by TEXT,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (email, role)
                )
            """)
            # Seed default routes
            default_routes = [
                ("/data-source", "Data Source", "excel"),
                ("/analytics", "Analytics Dashboard", "analytics"),
                ("/director-analysis", "Director Analysis", "director_analysis"),
                ("/directors-disclosure", "Directors Disclosure", "directors_disclosure"),
                ("/minutes", "Minutes Preparation", "minutes"),
                ("/rbi-sebi-compliance", "RBI/SEBI Compliance", "rbi"),
                ("/admin-panel", "Admin Control Center", "admin"),
                ("/insider-trading", "Insider Trading Monitor", "insider_trading"),
                ("/director-intelligence", "Director Intelligence", "director_intelligence"),
                ("/institutional-risk", "Institutional Risk", "institutional_risk")
            ]
            
            for path, name, module in default_routes:
                cursor.execute("""
                    INSERT INTO rbac.route_definitions (route_path, route_name, display_name, module_name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (route_path) DO NOTHING
                """, (path, name, name, module))

            conn.commit()
            logger.info("RBAC PostgreSQL tables verified and seeded")
        except Exception as e:
            conn.rollback()
            logger.error(f"RBAC init error: {e}")
        finally:
            conn.close()

def log_audit_event(email: str, event_type: str, details: Any, request: Request = None):
    """Log an authentication event to PostgreSQL."""
    try:
        ip = request.client.host if request else None
        ua = request.headers.get("user-agent") if request else None
        
        # Ensure details is a string (JSON) for PostgreSQL
        if isinstance(details, (dict, list)):
            details_str = json.dumps(details)
        else:
            details_str = str(details)
            
        def insert():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if conn:
                try:
                    cursor = get_pg_cursor(conn)
                    cursor.execute("""
                        INSERT INTO rbac.auth_audit_logs (email, event_type, event_details, ip_address, user_agent, application)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (email, event_type, details_str, ip, ua, "Aegis Platform"))
                    conn.commit()
                finally:
                    conn.close()
        
        asyncio.get_event_loop().run_in_executor(thread_pool, insert)
    except Exception as e:
        logger.error(f"Failed to log auth event: {e}")

# Alias for backward compatibility
log_auth_event = log_audit_event

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/users/me/permissions", response_model=UserPermissionsResponse)
@router.get("/rbac/my-permissions", response_model=UserPermissionsResponse)
async def get_my_permissions(email: str):
    """Retrieve all route permissions for a specific user."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return [], []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT rp.route_path, rp.permission_type, rd.display_name
                    FROM rbac.route_permissions rp
                    LEFT JOIN rbac.route_definitions rd ON rp.route_path = rd.route_path
                    WHERE LOWER(rp.email) = LOWER(%s) AND rp.is_active = TRUE
                """, (email,))
                rows = cursor.fetchall()
                perms = []
                routes = []
                for row in rows:
                    # Determine boolean flags
                    p_type = row["permission_type"]
                    perms.append({
                        "route": row["route_path"],
                        "route_path": row["route_path"],
                        "permission_type": p_type,
                        "permission": p_type, # Alias for compatibility
                        "route_name": row["display_name"] or row["route_path"],
                        "name": row["display_name"] or row["route_path"],
                        "can_view": True, # Everyone with a record can view
                        "can_edit": p_type in ["edit", "admin"],
                        "can_admin": p_type == "admin"
                    })
                    routes.append(row["route_path"])
                return perms, routes
            finally:
                conn.close()
        
        perms, routes = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        
        # --- GLOBAL ADMIN OVERRIDE ---
        # Check if user has global admin role in user_roles table
        def check_global_admin():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return False
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                return cursor.fetchone() is not None
            finally:
                conn.close()
        
        is_global_admin = await asyncio.get_event_loop().run_in_executor(thread_pool, check_global_admin)
        
        if is_global_admin:
            # Upgrade all permissions to admin
            for p in perms:
                p["can_admin"] = True
                p["can_edit"] = True
                p["permission_type"] = "admin"
            
            # Ensure /admin-panel is in the list
            if "/admin-panel" not in routes:
                routes.append("/admin-panel")
                perms.append({
                    "route": "/admin-panel",
                    "route_path": "/admin-panel",
                    "permission_type": "admin",
                    "permission": "admin",
                    "route_name": "Admin Panel",
                    "name": "Admin Panel",
                    "can_view": True,
                    "can_edit": True,
                    "can_admin": True
                })
        
        return UserPermissionsResponse(email=email, permissions=perms, accessible_routes=routes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rbac/check-access", response_model=PermissionCheckResponse)
@router.post("/rbac/check-access", response_model=PermissionCheckResponse)
@router.get("/permissions/check", response_model=PermissionCheckResponse)
@router.post("/permissions/check", response_model=PermissionCheckResponse)
async def check_route_access(email: str, route: str):
    """Check if a user has access to a specific route."""
    # Sanitize route
    clean_route = route.split('?')[0].rstrip('/')
    
    try:
        def check():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return None
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    SELECT permission_type FROM rbac.route_permissions
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

def check_route_permission(email: str, route: str) -> Optional[str]:
    """
    Synchronous helper to check user permission for a route.
    Used by internal services where async/await is not convenient.
    """
    # Sanitize route
    clean_route = route.split('?')[0].rstrip('/')
    
    conn = get_pg_connection()
    if not conn: return None
    try:
        cursor = get_pg_cursor(conn)
        cursor.execute("""
            SELECT permission_type FROM route_permissions
            WHERE LOWER(email) = LOWER(%s) AND route_path = %s AND is_active = TRUE
        """, (email, clean_route))
        row = cursor.fetchone()
        return row["permission_type"] if row else None
    except Exception as e:
        logger.error(f"Error checking route permission: {e}")
        return None
    finally:
        conn.close()

@router.post("/rbac/assign", response_model=Dict[str, Any])
@router.post("/permissions/assign", response_model=Dict[str, Any])
async def assign_permission(req: AssignPermissionRequest):
    """Assign a route permission to a user."""
    try:
        def assign():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return False
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("""
                    INSERT INTO rbac.route_permissions (email, route_path, permission_type, assigned_by, notes)
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

@router.post("/access-requests", response_model=Dict[str, Any])
@router.post("/rbac/request-access", response_model=Dict[str, Any])
async def submit_access_request(req: AccessRequestSubmit):
    """Submit a request for route access."""
    try:
        def request_access():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return None
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT 1 FROM rbac.access_requests WHERE LOWER(email) = LOWER(%s) AND requested_route = %s AND status = 'pending'", (req.email, req.requested_route))
                if cursor.fetchone():
                     return "duplicate"
                
                cursor.execute("INSERT INTO rbac.access_requests (email, name, requested_route, requested_permission, justification) VALUES (%s, %s, %s, %s, %s) RETURNING id",
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
                loop = asyncio.get_running_loop()
                asyncio.ensure_future(
                    loop.run_in_executor(
                        thread_pool,
                        send_access_request_emails,
                        res,  # Pass the new request_id
                        req.email,
                        req.name,
                        req.requested_route,
                        req.requested_permission,
                        req.justification
                    )
                )
                logger.info(f"Email task scheduled for new access request #{res}")
            except Exception as e:
                logger.error(f"Email notification task submission failed: {e}")
                
            return {"success": True, "request_id": res}
            
        return {"success": False, "message": "Failed to submit request"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def send_access_request_emails(request_id, email, name, route, perm, justification):
    """Send emails to admins about the new request and a confirmation to the user."""
    try:
        app_name = format_application_name(route)
        
        # 1. Notify Admins
        # Signature: (request_id, requester_name, requester_email, requested_route, justification, access_level)
        admin_content = get_admin_request_template(request_id, name, email, route, justification, perm)
        send_email(
            to_emails=ADMIN_EMAILS,
            subject=f"New Access Request: {app_name} ({name})",
            body=admin_content
        )
        
        # 2. Confirm to User
        # Signature: (requester_name, requested_route, status, request_id, access_level)
        user_content = get_user_confirmation_template(name, route, "pending", request_id, perm)
        send_email(
            to_emails=[email],
            subject=f"Access Request Received: {app_name}",
            body=user_content
        )
    except Exception as e:
        logger.error(f"RBAC Email Sync Error: {e}")

@router.get("/access-requests", response_model=Dict[str, Any])
@router.get("/rbac/requests", response_model=Dict[str, Any])
async def get_all_requests(email: Optional[str] = None, requester_email: Optional[str] = None, status: Optional[str] = None):
    """Get access requests with optional filtering. Distinguishes between auth and filters."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return [], 0
            cursor = get_pg_cursor(conn)
            try:
                # 1. Check if the 'email' (caller) is an admin
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                is_admin = cursor.fetchone() is not None
                
                # 2. Build Query
                query = "SELECT * FROM rbac.access_requests"
                params = []
                where_clauses = []
                
                # If requester_email is provided, always filter by it
                if requester_email:
                    where_clauses.append("LOWER(email) = LOWER(%s)")
                    params.append(requester_email)
                # If the caller is NOT an admin, they can ONLY see their own requests
                elif not is_admin and email:
                    where_clauses.append("LOWER(email) = LOWER(%s)")
                    params.append(email)
                
                if status:
                    where_clauses.append("status = %s")
                    params.append(status)
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                query += " ORDER BY requested_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for r in rows:
                    results.append(AccessRequestResponse(
                        id=r["id"],
                        email=r["email"],
                        name=r["name"],
                        requested_route=r["requested_route"],
                        requested_permission=r["requested_permission"],
                        justification=r["justification"],
                        status=r["status"],
                        requested_at=str(r["requested_at"]),
                        reviewed_by=r.get("reviewed_by"),
                        reviewed_at=str(r["reviewed_at"]) if r.get("reviewed_at") else None,
                        review_notes=r.get("review_notes")
                    ))
                return results, len(results)
            finally:
                conn.close()
        
        requests_list, total = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return {"requests": requests_list, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/permissions/all", response_model=Dict[str, Any])
async def get_all_route_permissions(email: str, route: Optional[str] = None):
    """Get all user permissions for a specific route — used by Admin Panel UserPermissions tab."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return None
            cursor = get_pg_cursor(conn)
            try:
                # Verify the caller is an admin
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone():
                    return None  # Unauthorized
                if route:
                    cursor.execute("""
                        SELECT rp.email, rp.permission_type, rp.assigned_at, rp.assigned_by
                        FROM rbac.route_permissions rp
                        WHERE rp.route_path = %s AND rp.is_active = TRUE
                        ORDER BY rp.assigned_at DESC
                    """, (route,))
                else:
                    cursor.execute("""
                        SELECT rp.email, rp.permission_type, rp.assigned_at, rp.assigned_by, rp.route_path
                        FROM rbac.route_permissions rp
                        WHERE rp.is_active = TRUE
                        ORDER BY rp.assigned_at DESC
                    """)
                rows = cursor.fetchall()
                result = []
                for r in rows:
                    perm = dict(r)
                    if perm.get('assigned_at'):
                        perm['assigned_at'] = str(perm['assigned_at'])
                    result.append(perm)
                return result
            finally:
                conn.close()

        result = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        if result is None:
            raise HTTPException(status_code=403, detail="Unauthorized: Admin access required")
        return {"permissions": result, "total": len(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_all_route_permissions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/route-definitions", response_model=List[RouteDefinitionResponse])
@router.get("/rbac/route-definitions", response_model=List[RouteDefinitionResponse])
async def get_route_definitions():
    """Retrieve all defined routes in the system."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return []
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT route_path, display_name, module_name FROM rbac.route_definitions ORDER BY display_name")
                rows = cursor.fetchall()
                return [RouteDefinitionResponse(
                    route_path=r["route_path"],
                    route=r["route_path"], # Duplicate for frontend
                    display_name=r["display_name"],
                    module_name=r["module_name"]
                ) for r in rows]
            finally:
                conn.close()
        return await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit-logs", response_model=AuditLogsListResponse)
async def get_audit_logs(limit: int = 15, offset: int = 0):
    """Retrieve paginated audit logs from PostgreSQL."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return [], 0
            cursor = get_pg_cursor(conn)
            try:
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM rbac.auth_audit_logs")
                total = cursor.fetchone()["count"]
                
                # Get paginated logs
                cursor.execute("""
                    SELECT id, email, event_type, event_details, ip_address, user_agent, application, created_at 
                    FROM rbac.auth_audit_logs 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                rows = cursor.fetchall()
                
                logs = []
                for r in rows:
                    details = r["event_details"]
                    if isinstance(details, dict):
                        details = json.dumps(details)
                    else:
                        details = str(details) if details is not None else None
                        
                    logs.append(AuditLogResponse(
                        id=r["id"],
                        email=r["email"],
                        event_type=r["event_type"],
                        event_details=details,
                        ip_address=r["ip_address"],
                        user_agent=r["user_agent"],
                        application=r["application"],
                        created_at=str(r["created_at"])
                    ))
                return logs, total
            finally:
                conn.close()
        
        logs, total = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        return AuditLogsListResponse(logs=logs, total=total)
    except Exception as e:
        logger.error(f"Audit log fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/access-requests/{request_id}/approve", response_model=Dict[str, Any])
async def approve_request(request_id: int, req: ReviewAccessRequestRequest, email: str):
    """Approve an access request and assign permissions."""
    try:
        def process():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return False, "Database connection failed"
            cursor = get_pg_cursor(conn)
            try:
                # 1. Verify Admin
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone():
                    return False, "Unauthorized: Only administrators can approve requests"
                
                # 2. Get Request Details
                cursor.execute("SELECT * FROM rbac.access_requests WHERE id = %s AND status = 'pending'", (request_id,))
                request = cursor.fetchone()
                if not request:
                    return False, "Request not found or already processed"
                
                # 3. Update Request Status
                cursor.execute("""
                    UPDATE rbac.access_requests 
                    SET status = 'approved', reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP, review_notes = %s
                    WHERE id = %s
                """, (email, req.review_notes, request_id))
                
                # 4. Assign Permission
                cursor.execute("""
                    INSERT INTO rbac.route_permissions (email, route_path, permission_type, assigned_by, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (email, route_path) 
                    DO UPDATE SET permission_type = EXCLUDED.permission_type, notes = EXCLUDED.notes, is_active = TRUE
                """, (request["email"], request["requested_route"], request["requested_permission"], email, req.review_notes))
                
                conn.commit()
                return True, request
            finally:
                conn.close()
        
        success, res_data = await asyncio.get_event_loop().run_in_executor(thread_pool, process)
        if success:
            # Trigger confirmation email
            try:
                loop = asyncio.get_running_loop()
                asyncio.ensure_future(
                    loop.run_in_executor(
                        thread_pool,
                        send_request_outcome_email,
                        res_data["email"],
                        res_data["name"],
                        res_data["requested_route"],
                        "approved",
                        request_id,
                        res_data["requested_permission"]
                    )
                )
                logger.info(f"Approval email scheduled for {res_data['email']}")
            except Exception as e:
                logger.error(f"Outcome email failed: {e}")
            return {"success": True, "message": "Request approved and permission assigned"}
        else:
            raise HTTPException(status_code=400, detail=res_data)
            
    except Exception as e:
        logger.error(f"Approval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/access-requests/{request_id}/reject", response_model=Dict[str, Any])
async def reject_request(request_id: int, req: ReviewAccessRequestRequest, email: str):
    """Reject an access request."""
    try:
        def process():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return False, "Database connection failed"
            cursor = get_pg_cursor(conn)
            try:
                # 1. Verify Admin
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone():
                    return False, "Unauthorized: Only administrators can reject requests"
                
                # 2. Get Request Details
                cursor.execute("SELECT * FROM rbac.access_requests WHERE id = %s AND status = 'pending'", (request_id,))
                request = cursor.fetchone()
                if not request:
                    return False, "Request not found or already processed"
                
                # 3. Update Status
                cursor.execute("""
                    UPDATE rbac.access_requests 
                    SET status = 'rejected', reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP, review_notes = %s
                    WHERE id = %s
                """, (email, req.review_notes, request_id))
                
                conn.commit()
                return True, request
            finally:
                conn.close()
        
        success, res_data = await asyncio.get_event_loop().run_in_executor(thread_pool, process)
        if success:
            # Trigger rejection email
            try:
                loop = asyncio.get_running_loop()
                asyncio.ensure_future(
                    loop.run_in_executor(
                        thread_pool,
                        send_request_outcome_email,
                        res_data["email"],
                        res_data["name"],
                        res_data["requested_route"],
                        "rejected",
                        request_id,
                        res_data["requested_permission"]
                    )
                )
                logger.info(f"Rejection email scheduled for {res_data['email']}")
            except Exception as e:
                logger.error(f"Outcome email failed: {e}")
            return {"success": True, "message": "Request rejected"}
        else:
            raise HTTPException(status_code=400, detail=res_data)
            
    except Exception as e:
        logger.error(f"Rejection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def send_request_outcome_email(email, name, route, status, request_id, perm):
    """Helper to send the final approval/rejection email."""
    try:
        app_name = format_application_name(route)
        content = get_user_confirmation_template(name, route, status, request_id, perm)
        
        send_email(
            to_emails=[email],
            subject=f"Access Request {'Approved' if status == 'approved' else 'Declined'}: {app_name}",
            body=content
        )
    except Exception as e:
        logger.error(f"Outcome Email Error: {e}")
@router.delete("/permissions/revoke", response_model=Dict[str, Any])
async def revoke_permission(req: RevokePermissionRequest, email: str):
    """Revoke a route permission from a user."""
    try:
        def revoke():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return False
            cursor = get_pg_cursor(conn)
            try:
                # 1. Verify Admin
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone():
                    return False
                
                # 2. Revoke Permission (soft delete)
                cursor.execute("""
                    UPDATE rbac.route_permissions 
                    SET is_active = FALSE 
                    WHERE LOWER(email) = LOWER(%s) AND route_path = %s
                """, (req.email.lower(), req.route))
                conn.commit()
                return True
            finally:
                conn.close()
        
        success = await asyncio.get_event_loop().run_in_executor(thread_pool, revoke)
        return {"success": success}
    except Exception as e:
        logger.error(f"Revoke error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Admin Management Endpoints
# ============================================================================

@router.get("/admin/platform-admins", response_model=Dict[str, Any])
async def get_platform_admins(email: str):
    """List all platform admins from rbac.user_roles."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return None
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone(): return None
                cursor.execute("""
                    SELECT email, role, granted_by, granted_at
                    FROM rbac.user_roles
                    ORDER BY granted_at DESC
                """)
                rows = cursor.fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    if d.get('granted_at'): d['granted_at'] = str(d['granted_at'])
                    result.append(d)
                return result
            finally:
                conn.close()
        result = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        if result is None:
            raise HTTPException(status_code=403, detail="Unauthorized")
        return {"admins": result, "total": len(result)}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"get_platform_admins error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/grant-role", response_model=Dict[str, Any])
async def grant_platform_role(req: GrantRoleRequest, email: str):
    """Grant a global platform role (e.g. admin) to a user."""
    try:
        def do_grant():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return False
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone(): return False
                cursor.execute("""
                    INSERT INTO rbac.user_roles (email, role, granted_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (email, role) DO UPDATE
                        SET granted_by = EXCLUDED.granted_by,
                            granted_at = CURRENT_TIMESTAMP
                """, (req.target_email.lower(), req.role, email))
                conn.commit()
                return True
            finally:
                conn.close()
        ok = await asyncio.get_event_loop().run_in_executor(thread_pool, do_grant)
        if ok is False:
            raise HTTPException(status_code=403, detail="Unauthorized or DB error")
        log_audit_event(email, "admin_granted", {"target_email": req.target_email, "role": req.role})
        return {"success": True, "message": f"Role '{req.role}' granted to {req.target_email}"}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"grant_platform_role error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/revoke-role", response_model=Dict[str, Any])
async def revoke_platform_role(req: RevokeRoleRequest, email: str):
    """Revoke a global platform role from a user."""
    try:
        def do_revoke():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return False
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone(): return False
                # Safety: cannot remove the last admin
                cursor.execute("SELECT COUNT(*) FROM rbac.user_roles WHERE role = 'admin'")
                count = cursor.fetchone()[0]
                if count <= 1 and req.target_email.lower() == email.lower(): return False
                cursor.execute("DELETE FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (req.target_email,))
                conn.commit()
                return True
            finally:
                conn.close()
        ok = await asyncio.get_event_loop().run_in_executor(thread_pool, do_revoke)
        if ok is False:
            raise HTTPException(status_code=403, detail="Unauthorized or cannot remove last admin")
        log_audit_event(email, "admin_revoked", {"target_email": req.target_email})
        return {"success": True, "message": f"Admin role revoked for {req.target_email}"}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"revoke_platform_role error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/all-users", response_model=Dict[str, Any])
async def get_all_platform_users(email: str):
    """Return all users across all route permissions (admin view)."""
    try:
        def fetch():
            conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
            if not conn: return None
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT 1 FROM rbac.user_roles WHERE LOWER(email) = LOWER(%s) AND role = 'admin'", (email,))
                if not cursor.fetchone(): return None
                cursor.execute("""
                    SELECT rp.email, rp.route_path, rp.permission_type, rp.assigned_at, rp.assigned_by
                    FROM rbac.route_permissions rp
                    WHERE rp.is_active = TRUE
                    ORDER BY rp.email, rp.assigned_at DESC
                """)
                rows = cursor.fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    if d.get('assigned_at'): d['assigned_at'] = str(d['assigned_at'])
                    result.append(d)
                return result
            finally:
                conn.close()
        result = await asyncio.get_event_loop().run_in_executor(thread_pool, fetch)
        if result is None:
            raise HTTPException(status_code=403, detail="Unauthorized")
        return {"users": result, "total": len(result)}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"get_all_platform_users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
