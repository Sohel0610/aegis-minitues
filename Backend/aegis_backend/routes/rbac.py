"""
RBAC (Role-Based Access Control) Route Module
This module handles route-based permission management and access requests
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
from datetime import datetime
import json
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
    permission_type: str  # 'view', 'admin', 'edit'
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
    permission_type: str  # 'view', 'admin', 'edit'
    notes: Optional[str] = None

class RevokePermissionRequest(BaseModel):
    email: EmailStr
    route: str

class AccessRequestSubmit(BaseModel):
    email: EmailStr
    name: str
    requested_route: str
    requested_permission: str  # 'view', 'admin', 'edit'
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

def get_db_path():
    """Get the path to the database"""
    return os.path.join(os.path.dirname(__file__), "..", "public", "email_data.db")

def log_audit_event(email: str, event_type: str, event_details: Dict[str, Any], 
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None):
    """Log an audit event"""
    def _log():
        conn = sqlite3.connect(get_db_path(), timeout=30)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auth_audit_logs (email, event_type, event_details, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        """, (email, event_type, json.dumps(event_details), ip_address, user_agent))
        conn.commit()
        conn.close()
    
    try:
        _log()
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")

def get_user_permissions_from_db(email: str) -> List[Dict[str, Any]]:
    """Get all permissions for a user from database"""
    conn = sqlite3.connect(get_db_path(), timeout=30)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT rp.route_path, rp.permission_type, rd.route_name, rd.description
        FROM route_permissions rp
        LEFT JOIN route_definitions rd ON rp.route_path = rd.route_path
        WHERE LOWER(rp.email) = LOWER(?) AND rp.is_active = 1
        ORDER BY rp.route_path
    """, (email,))
    
    permissions = []
    for row in cursor.fetchall():
        route_path, perm_type, route_name, description = row
        permissions.append({
            "route": route_path,
            "permission_type": perm_type,
            "route_name": route_name or route_path,
            "description": description,
            "can_view": perm_type in ['view', 'edit', 'admin'],
            "can_edit": perm_type in ['edit', 'admin'],
            "can_admin": perm_type == 'admin'
        })
    
    conn.close()
    return permissions

def check_route_permission(email: str, route_path: str) -> Optional[str]:
    """Check if user has permission for a specific route. Returns permission type or None"""
    conn = sqlite3.connect(get_db_path(), timeout=30)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT permission_type FROM route_permissions
        WHERE LOWER(email) = LOWER(?) AND route_path = ? AND is_active = 1
        LIMIT 1
    """, (email, route_path))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

# ============================================================================
# Permission Check Endpoints
# ============================================================================

@router.get("/api/users/me/permissions", response_model=UserPermissionsResponse)
async def get_current_user_permissions(request: Request):
    """Get all permissions for the current authenticated user"""
    # Extract email from request (should be set by auth middleware)
    # For now, we'll get it from query param or header
    email = request.query_params.get("email") or request.headers.get("X-User-Email")
    
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        def fetch_permissions():
            return get_user_permissions_from_db(email)
        
        loop = asyncio.get_event_loop()
        permissions = await loop.run_in_executor(thread_pool, fetch_permissions)
        
        accessible_routes = [p["route"] for p in permissions]
        
        return UserPermissionsResponse(
            email=email,
            permissions=permissions,
            accessible_routes=accessible_routes
        )
    except Exception as e:
        logger.error(f"Error fetching permissions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch permissions: {str(e)}")

@router.get("/api/permissions/check", response_model=PermissionCheckResponse)
async def check_permission(route: str, request: Request):
    """Check if current user has access to a specific route"""
    email = request.query_params.get("email") or request.headers.get("X-User-Email")
    
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        def check_perm():
            return check_route_permission(email, route)
        
        loop = asyncio.get_event_loop()
        permission_type = await loop.run_in_executor(thread_pool, check_perm)
        
        if permission_type:
            return PermissionCheckResponse(
                has_access=True,
                permission_type=permission_type,
                can_view=permission_type in ['view', 'edit', 'admin'],
                can_edit=permission_type in ['edit', 'admin'],
                can_admin=permission_type == 'admin'
            )
        else:
            return PermissionCheckResponse(
                has_access=False,
                message="You do not have permission to access this application",
                can_request_access=True
            )
    except Exception as e:
        logger.error(f"Error checking permission: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check permission: {str(e)}")

# ============================================================================
# Email Action Endpoint (GET for email buttons)
# ============================================================================

@router.get("/api/access-requests/email-action")
async def email_access_action(id: int, action: str, email: str, request: Request):
    # Simple security check: admin must match our configured admins
    admin_emails_lower = [e.lower() for e in ADMIN_EMAILS]
    if email.lower() not in admin_emails_lower:
        return {"success": False, "message": "Unauthorized action source."}
    
    try:
        if action == "approve":
            # Call the internal logic for approval
            review = ReviewAccessRequestRequest(review_notes="Approved via Email Action")
            # We mock a request object or just use the logic
            result = await approve_access_request(id, review, request)
            return {"success": True, "message": f"Request {id} has been approved successfully."}
        elif action == "reject":
            # Call the internal logic for rejection
            review = ReviewAccessRequestRequest(review_notes="Rejected via Email Action")
            result = await reject_access_request(id, review, request)
            return {"success": True, "message": f"Request {id} has been rejected successfully."}
        else:
            return {"success": False, "message": "Invalid action."}
    except Exception as e:
        logger.error(f"Error processing email action: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


# ============================================================================
# Permission Management Endpoints (Admin Only)
# ============================================================================

@router.post("/api/permissions/assign")
async def assign_permission(req: AssignPermissionRequest, request: Request):
    """Assign a route permission to a user (Admin only)"""
    admin_email = request.query_params.get("email") or request.headers.get("X-User-Email")
    
    if not admin_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify admin has permission to assign
    # For now, we'll check if they have admin permission on any route
    # In production, you'd have a super-admin role
    
    try:
        def assign():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                # Check if permission already exists (to support upsert/update)
                cursor.execute("""
                    SELECT id FROM route_permissions 
                    WHERE LOWER(email) = LOWER(?) AND route_path = ?
                """, (req.email, req.route))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing permission
                    cursor.execute("""
                        UPDATE route_permissions 
                        SET permission_type = ?, assigned_by = ?, notes = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (req.permission_type, admin_email, req.notes, existing[0]))
                    event_type = "permission_updated"
                else:
                    # Insert new permission
                    cursor.execute("""
                        INSERT INTO route_permissions (email, route_path, permission_type, assigned_by, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (req.email, req.route, req.permission_type, admin_email, req.notes))
                    event_type = "permission_assigned"
                
                conn.commit()
                
                # Log audit event
                log_audit_event(
                    admin_email,
                    event_type,
                    {
                        "target_email": req.email,
                        "route": req.route,
                        "permission_type": req.permission_type,
                        "notes": req.notes
                    }
                )
                
                return True
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, assign)
        
        return {
            "success": True,
            "message": "Permission assigned successfully",
            "email": req.email,
            "route": req.route,
            "permission_type": req.permission_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning permission: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign permission: {str(e)}")

@router.delete("/api/permissions/revoke")
async def revoke_permission(req: RevokePermissionRequest, request: Request):
    """Revoke a route permission from a user (Admin only)"""
    admin_email = request.query_params.get("email") or request.headers.get("X-User-Email")
    
    if not admin_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        def revoke():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                # Soft delete by setting is_active = 0
                cursor.execute("""
                    UPDATE route_permissions
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE LOWER(email) = LOWER(?) AND route_path = ?
                """, (req.email, req.route))
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Permission not found")
                
                conn.commit()
                
                # Log audit event
                log_audit_event(
                    admin_email,
                    "permission_revoked",
                    {
                        "target_email": req.email,
                        "route": req.route
                    }
                )
                
                return True
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, revoke)
        
        return {
            "success": True,
            "message": "Permission revoked successfully",
            "email": req.email,
            "route": req.route
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking permission: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke permission: {str(e)}")

@router.get("/api/permissions/all")
async def list_all_permissions(route: Optional[str] = None, request: Request = None):
    """List all permissions, optionally filtered by route (Admin only)"""
    try:
        def fetch_all():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                if route:
                    cursor.execute("""
                        SELECT rp.email, rp.permission_type, rp.assigned_at, rp.assigned_by, rp.notes
                        FROM route_permissions rp
                        WHERE rp.route_path = ? AND rp.is_active = 1
                        ORDER BY rp.permission_type DESC, rp.email
                    """, (route,))
                else:
                    cursor.execute("""
                        SELECT rp.route_path, rp.email, rp.permission_type, rp.assigned_at, rp.assigned_by
                        FROM route_permissions rp
                        WHERE rp.is_active = 1
                        ORDER BY rp.route_path, rp.permission_type DESC, rp.email
                    """)
                
                permissions = []
                for row in cursor.fetchall():
                    if route:
                        permissions.append({
                            "email": row[0],
                            "permission_type": row[1],
                            "assigned_at": row[2],
                            "assigned_by": row[3],
                            "notes": row[4]
                        })
                    else:
                        permissions.append({
                            "route": row[0],
                            "email": row[1],
                            "permission_type": row[2],
                            "assigned_at": row[3],
                            "assigned_by": row[4]
                        })
                
                return permissions
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        permissions = await loop.run_in_executor(thread_pool, fetch_all)
        
        if route:
            # Get route name
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT route_name FROM route_definitions WHERE route_path = ?", (route,))
                result = cursor.fetchone()
                route_name = result[0] if result else route
            finally:
                conn.close()
            
            return {
                "route": route,
                "route_name": route_name,
                "permissions": permissions,
                "total_users": len(permissions)
            }
        else:
            return {
                "permissions": permissions,
                "total": len(permissions)
            }
    except Exception as e:
        logger.error(f"Error listing permissions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list permissions: {str(e)}")

@router.get("/api/route-definitions")
async def list_route_definitions():
    """List all available routes and their friendly names"""
    try:
        def fetch_routes():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT route_path, route_name, description, application FROM route_definitions WHERE is_active = 1")
                routes = []
                for row in cursor.fetchall():
                    routes.append({
                        "route_path": row[0],
                        "route_name": row[1],
                        "description": row[2],
                        "application": row[3]
                    })
                return routes
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(thread_pool, fetch_routes)
    except Exception as e:
        logger.error(f"Error listing route definitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/audit-logs")
async def list_audit_logs(limit: int = 50, offset: int = 0, event_type: Optional[str] = None):
    """List audit logs (Admin only)"""
    try:
        def fetch_logs():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                query = "SELECT * FROM auth_audit_logs "
                params = []
                if event_type:
                    query += "WHERE event_type = ? "
                    params.append(event_type)
                
                query += "ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Get total count for pagination
                count_query = "SELECT COUNT(*) FROM auth_audit_logs"
                if event_type:
                    count_query += " WHERE event_type = ?"
                    cursor.execute(count_query, (event_type,))
                else:
                    cursor.execute(count_query)
                
                total = cursor.fetchone()[0]
                return logs, total
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        logs, total = await loop.run_in_executor(thread_pool, fetch_logs)
        return {"logs": logs, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Access Request Endpoints
# ============================================================================

@router.post("/api/access-requests", response_model=Dict[str, Any])
async def submit_access_request(req: AccessRequestSubmit, request: Request):
    """Submit an access request for a route"""
    try:
        def create_request():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                # Check if user already has this permission
                cursor.execute("""
                    SELECT id FROM route_permissions
                    WHERE LOWER(email) = LOWER(?) AND route_path = ? AND is_active = 1
                """, (req.email, req.requested_route))
                
                if cursor.fetchone():
                    raise HTTPException(status_code=409, detail="You already have access to this application")
                
                # Check if there's already a pending request
                cursor.execute("""
                    SELECT id FROM access_requests
                    WHERE LOWER(email) = LOWER(?) AND requested_route = ? AND status = 'pending'
                """, (req.email, req.requested_route))
                
                if cursor.fetchone():
                    raise HTTPException(status_code=409, detail="You already have a pending request for this application")
                
                # Create new request
                cursor.execute("""
                    INSERT INTO access_requests (email, name, requested_route, requested_permission, justification)
                    VALUES (?, ?, ?, ?, ?)
                """, (req.email, req.name, req.requested_route, req.requested_permission, req.justification))
                
                request_id = cursor.lastrowid
                conn.commit()
                
                # Log audit event
                log_audit_event(
                    req.email,
                    "access_requested",
                    {
                        "route": req.requested_route,
                        "permission": req.requested_permission,
                        "justification": req.justification
                    }
                )
                
                return request_id
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        request_id = await loop.run_in_executor(thread_pool, create_request)
        
        # Send Email Notification to All Administrators
        try:
            app_name = format_application_name(req.requested_route)
            for admin_email in ADMIN_EMAILS:
                admin_body = get_admin_request_template(
                    request_id, req.name, req.email, req.requested_route, req.justification, req.requested_permission,
                    target_admin_email=admin_email
                )
                # Send asynchronously in executor to avoid blocking
                loop.run_in_executor(thread_pool, send_email, f"AEGIS | Access Request: {app_name} from {req.name}", admin_body, admin_email)
        except Exception as email_err:
            logger.error(f"Failed to trigger admin notification email: {email_err}")

        return {
            "id": request_id,
            "status": "pending",
            "message": "Access request submitted successfully. It will be reviewed by the administrator.",
            "route": req.requested_route,
            "permission": req.requested_permission,
            "estimated_review_time": "24-48 hours"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting access request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit access request: {str(e)}")

@router.get("/api/access-requests", response_model=Dict[str, Any])
async def list_access_requests(
    status: Optional[str] = None,
    route: Optional[str] = None,
    request: Request = None
):
    """List access requests (Admin only)"""
    try:
        def fetch_requests():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                query = "SELECT * FROM access_requests WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                if route:
                    query += " AND requested_route = ?"
                    params.append(route)
                
                query += " ORDER BY requested_at DESC"
                
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                requests = []
                for row in cursor.fetchall():
                    requests.append(dict(zip(columns, row)))
                
                return requests
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        requests = await loop.run_in_executor(thread_pool, fetch_requests)
        
        return {
            "requests": requests,
            "total": len(requests)
        }
    except Exception as e:
        logger.error(f"Error listing access requests: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list access requests: {str(e)}")

@router.put("/api/access-requests/{request_id}/approve")
async def approve_access_request(request_id: int, review: ReviewAccessRequestRequest, request: Request):
    """Approve an access request (Admin only)"""
    admin_email = request.query_params.get("email") or request.headers.get("X-User-Email")
    
    if not admin_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        def approve():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                # Get request details
                cursor.execute("SELECT * FROM access_requests WHERE id = ?", (request_id,))
                req_row = cursor.fetchone()
                
                if not req_row:
                    raise HTTPException(status_code=404, detail="Access request not found")
                
                columns = [desc[0] for desc in cursor.description]
                req_data = dict(zip(columns, req_row))
                
                if req_data['status'] != 'pending':
                    raise HTTPException(status_code=400, detail="Request already processed")
                
                # Update request status
                cursor.execute("""
                    UPDATE access_requests
                    SET status = 'approved', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, review_notes = ?
                    WHERE id = ?
                """, (admin_email, review.review_notes, request_id))
                
                # Assign permission (UPSERT logic)
                # Check if permission already exists
                cursor.execute("""
                    SELECT id FROM route_permissions 
                    WHERE LOWER(email) = LOWER(?) AND route_path = ?
                """, (req_data['email'], req_data['requested_route']))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing permission
                    cursor.execute("""
                        UPDATE route_permissions 
                        SET permission_type = ?, assigned_by = ?, notes = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        req_data['requested_permission'], 
                        admin_email, 
                        f"Updated via access request #{request_id}", 
                        existing[0]
                    ))
                else:
                    # Insert new permission
                    cursor.execute("""
                        INSERT INTO route_permissions (email, route_path, permission_type, assigned_by, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        req_data['email'],
                        req_data['requested_route'],
                        req_data['requested_permission'],
                        admin_email,
                        f"Approved via access request #{request_id}"
                    ))
                
                # Log audit event within the same transaction if possible, or right after
                cursor.execute("""
                    INSERT INTO auth_audit_logs (email, event_type, event_details, application)
                    VALUES (?, ?, ?, ?)
                """, (
                    admin_email,
                    "access_approved",
                    json.dumps({
                        "request_id": request_id,
                        "user_email": req_data['email'],
                        "route": req_data['requested_route'],
                        "permission": req_data['requested_permission']
                    }),
                    "aegis"
                ))
                
                conn.commit()
                return req_data
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        req_data = await loop.run_in_executor(thread_pool, approve)
        
        # Send Confirmation Email to User
        try:
            # Pass request_id and assigned_permission to the template
            user_body = get_user_confirmation_template(
                req_data['name'], 
                req_data['requested_route'], 
                'approved', 
                request_id=request_id, 
                access_level=req_data['requested_permission']
            )
            app_name = format_application_name(req_data['requested_route'])
            loop.run_in_executor(thread_pool, send_email, f"AEGIS | Access Granted: {app_name}", user_body, req_data['email'])
        except Exception as email_err:
            logger.error(f"Failed to trigger user confirmation email: {email_err}")

        return {
            "success": True,
            "message": "Access request approved",
            "user_email": req_data['email'],
            "route": req_data['requested_route'],
            "assigned_permission": req_data['requested_permission']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving access request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve access request: {str(e)}")

@router.put("/api/access-requests/{request_id}/reject")
async def reject_access_request(request_id: int, review: ReviewAccessRequestRequest, request: Request):
    """Reject an access request (Admin only)"""
    admin_email = request.query_params.get("email") or request.headers.get("X-User-Email")
    
    if not admin_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        def reject():
            conn = sqlite3.connect(get_db_path(), timeout=30)
            try:
                cursor = conn.cursor()
                
                # Get request details
                cursor.execute("SELECT * FROM access_requests WHERE id = ?", (request_id,))
                req_row = cursor.fetchone()
                
                if not req_row:
                    raise HTTPException(status_code=404, detail="Access request not found")
                
                columns = [desc[0] for desc in cursor.description]
                req_data = dict(zip(columns, req_row))
                
                if req_data['status'] != 'pending':
                    raise HTTPException(status_code=400, detail="Request already processed")
                
                # Update request status
                cursor.execute("""
                    UPDATE access_requests
                    SET status = 'rejected', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP, review_notes = ?
                    WHERE id = ?
                """, (admin_email, review.review_notes, request_id))
                
                conn.commit()
                
                # Log audit event
                log_audit_event(
                    admin_email,
                    "access_rejected",
                    {
                        "request_id": request_id,
                        "user_email": req_data['email'],
                        "route": req_data['requested_route'],
                        "reason": review.review_notes
                    }
                )
                
                return req_data
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        req_data = await loop.run_in_executor(thread_pool, reject)
        
        # Send Notification Email to User
        try:
            # Pass request_id and requested_permission to the template
            user_body = get_user_confirmation_template(
                req_data['name'], 
                req_data['requested_route'], 
                'rejected', 
                request_id=request_id, 
                access_level=req_data['requested_permission']
            )
            app_name = format_application_name(req_data['requested_route'])
            loop.run_in_executor(thread_pool, send_email, f"AEGIS | Access Update: {app_name}", user_body, req_data['email'])
        except Exception as email_err:
            logger.error(f"Failed to trigger user rejection email: {email_err}")

        return {
            "success": True,
            "message": "Access request rejected",
            "user_email": req_data['email'],
            "route": req_data['requested_route']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting access request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject access request: {str(e)}")
