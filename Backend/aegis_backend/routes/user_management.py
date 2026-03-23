# User Management Route Module user_management.py
# This module handles user role assignment and management for Azure AD SSO integration
# Using local in-memory storage instead of PostgreSQL for now

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
tread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for user management endpoints
router = APIRouter()

# In-memory local user role storage (temporary solution)
LOCAL_USER_ROLES = {
    "cogn206112@adani.com": ["admin"]
}

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


# Endpoint to get all users and their roles
@router.get("/admin/users", response_model=UsersListResponse)
async def get_all_users_with_roles():
    """Get all users and their assigned roles from local mapping"""
    users = []
    for email, roles in LOCAL_USER_ROLES.items():
        users.append({
            "email": email,
            "name": "",  # Would come from user profile
            "roles": roles,
            "assigned_at": datetime.now().isoformat()  # Mock timestamp
        })
    
    return {"users": users}

# Endpoint to assign a role to a user
@router.post("/admin/users/assign-role", response_model=UserRoleResponse)
async def assign_role_to_user(role_assignment: RoleAssignmentRequest):
    """Assign a role to a user in the local in-memory mapping"""
    # Check if user already exists in mapping
    if role_assignment.user_email in LOCAL_USER_ROLES:
        # Update existing roles
        current_roles = LOCAL_USER_ROLES[role_assignment.user_email]
        if role_assignment.role not in current_roles:
            current_roles.append(role_assignment.role)
            LOCAL_USER_ROLES[role_assignment.user_email] = current_roles
        else:
            return {
                "user_email": role_assignment.user_email,
                "roles": current_roles,
                "message": f"Role {role_assignment.role} already assigned to {role_assignment.user_email}"
            }
    else:
        # Create new user mapping
        LOCAL_USER_ROLES[role_assignment.user_email] = [role_assignment.role]
    
    return {
        "user_email": role_assignment.user_email,
        "roles": LOCAL_USER_ROLES[role_assignment.user_email],
        "message": f"Role {role_assignment.role} assigned to {role_assignment.user_email}"
    }

# Endpoint to remove a role from a user
@router.delete("/admin/users/remove-role", response_model=UserRoleResponse)
async def remove_role_from_user(role_removal: RoleRemovalRequest):
    """Remove a role from a user in the local in-memory mapping"""
    if role_removal.user_email in LOCAL_USER_ROLES:
        current_roles = LOCAL_USER_ROLES[role_removal.user_email]
        if role_removal.role in current_roles:
            current_roles.remove(role_removal.role)
            LOCAL_USER_ROLES[role_removal.user_email] = current_roles
            
            return {
                "user_email": role_removal.user_email,
                "roles": current_roles,
                "message": f"Role {role_removal.role} removed from {role_removal.user_email}"
            }
        else:
            raise HTTPException(status_code=404, detail="Role not found for user")
    else:
        raise HTTPException(status_code=404, detail="User not found in role mapping")

# Endpoint to initialize the user role mapping (for local storage)
@router.post("/admin/init-role-mapping")
async def init_role_mapping_table():
    """Initialize the local user role mapping (placeholder for local storage)"""
    # Since we're using in-memory storage, this is just a placeholder
    # In a real implementation with persistence, you might load from a file or DB
    return {"message": "Local user role mapping initialized successfully"}
