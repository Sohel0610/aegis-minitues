# User Management Route Module user_management.py
# This module handles user role assignment and management using PostgreSQL
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for user management endpoints
router = APIRouter()

# Request models
class RoleAssignmentRequest(BaseModel):
    user_email: str
    role: str

class RoleRemovalRequest(BaseModel):
    user_email: str
    role: str

# Response models
class UserRoleResponse(BaseModel):
    user_email: str
    roles: List[str]
    message: str

class UsersListResponse(BaseModel):
    users: List[Dict[str, Any]]

def init_rbac_db():
    """Initialize RBAC tables in PostgreSQL."""
    conn = get_pg_connection()
    if conn:
        try:
            cursor = get_pg_cursor(conn)
            
            # Simple user roles table for SSO integration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(email, role)
                )
            """)
            
            # Seed initial admin if empty
            cursor.execute("SELECT COUNT(*) FROM user_roles WHERE email = %s", ("cogn206112@adani.com",))
            if cursor.fetchone()["count"] == 0:
                cursor.execute("INSERT INTO user_roles (email, role) VALUES (%s, %s)", ("cogn206112@adani.com", "admin"))
            
            conn.commit()
            logger.info("RBAC tables initialized in PostgreSQL")
        finally:
            conn.close()

# Endpoint to get all users and their roles
@router.get("/admin/users", response_model=UsersListResponse)
async def get_all_users_with_roles():
    """Get all users and their assigned roles from PostgreSQL"""
    try:
        def fetch():
            conn = get_pg_connection()
            if not conn: raise RuntimeError("DB connection failed")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("SELECT email, role, assigned_at FROM user_roles ORDER BY email")
                rows = cursor.fetchall()
                # Group by email
                users_map = {}
                for r in rows:
                    e = r["email"]
                    if e not in users_map:
                        users_map[e] = {"email": e, "roles": [], "assigned_at": str(r["assigned_at"])}
                    users_map[e]["roles"].append(r["role"])
                return list(users_map.values())
            finally:
                conn.close()
        
        loop = asyncio.get_event_loop()
        users = await loop.run_in_executor(thread_pool, fetch)
        return {"users": users}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to assign a role to a user
@router.post("/admin/assign-role", response_model=UserRoleResponse)
async def assign_role_to_user(request: RoleAssignmentRequest):
    """Assign a role to a user in PostgreSQL"""
    email = request.user_email.lower().strip()
    role = request.role.lower().strip()
    
    try:
        def assign():
            conn = get_pg_connection()
            if not conn: raise RuntimeError("DB Error")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("INSERT INTO user_roles (email, role) VALUES (%s, %s) ON CONFLICT (email, role) DO NOTHING", (email, role))
                conn.commit()
                # Fetch all roles
                cursor.execute("SELECT role FROM user_roles WHERE email = %s", (email,))
                rows = cursor.fetchall()
                return [r["role"] for r in rows]
            finally:
                conn.close()
                
        roles = await asyncio.get_event_loop().run_in_executor(thread_pool, assign)
        return UserRoleResponse(user_email=email, roles=roles, message=f"Role {role} assigned successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to remove a role from a user
@router.post("/admin/remove-role", response_model=UserRoleResponse)
async def remove_role_from_user(request: RoleRemovalRequest):
    """Remove a role from a user in PostgreSQL"""
    email = request.user_email.lower().strip()
    role = request.role.lower().strip()
    
    try:
        def remove():
            conn = get_pg_connection()
            if not conn: raise RuntimeError("DB Error")
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute("DELETE FROM user_roles WHERE email = %s AND role = %s", (email, role))
                conn.commit()
                # Fetch remaining roles
                cursor.execute("SELECT role FROM user_roles WHERE email = %s", (email,))
                rows = cursor.fetchall()
                return [r["role"] for r in rows]
            finally:
                conn.close()
                
        roles = await asyncio.get_event_loop().run_in_executor(thread_pool, remove)
        return UserRoleResponse(user_email=email, roles=roles, message=f"Role {role} removed successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
