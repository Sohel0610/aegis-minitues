# Authentication Route Module auth.py
# This module handles Azure AD SSO authentication and authorization

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
import requests
import jwt
from jose import jwt as jose_jwt
from datetime import datetime, timedelta
import secrets
import hashlib
import urllib.parse

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
tread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for authentication endpoints
router = APIRouter()

# Configuration from environment variables
CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_AD_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
REDIRECT_URI = os.getenv("AZURE_AD_REDIRECT_URI", "https://aegis.adani.com/api/auth/callback")

if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
    logger.warning("Azure AD configuration not fully set. Authentication endpoints may not work properly.")

# In-memory local user role storage (temporary solution)
LOCAL_USER_ROLES = {
    "admin@example.com": ["admin"],
    "viewer@example.com": ["viewer"],
    "bse_manager@example.com": ["bse_manager"],
    "cogn206112@adani.com": ["admin"]
}

def get_user_roles_with_default(email: str) -> List[str]:
    """Get roles from mapping, providing a default 'viewer' role for corporate accounts"""
    if not email:
        return []
        
    # Check if user is in our explicit mapping
    roles = LOCAL_USER_ROLES.get(email.lower())
    if roles:
        return roles
        
    # Default behavior: any @adani.com email gets 'viewer' access
    if email.lower().endswith("@adani.com"):
        return ["viewer"]
        
    return []

# Response models
class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

# Endpoint to initiate Azure AD login
@router.get("/api/auth/login")
async def azure_ad_login():
    """Redirect user to Azure AD for authentication"""
    if not all([CLIENT_ID, TENANT_ID, REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="Azure AD configuration is incomplete")
    
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    # Store state in session (in a real implementation, you'd use proper session management)
    # For now, we'll just pass it as a parameter
    
    # Construct Azure AD authorization URL
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
    auth_url += f"client_id={CLIENT_ID}&"
    auth_url += f"response_type=code&"
    auth_url += f"redirect_uri={REDIRECT_URI}&"
    auth_url += f"scope=openid profile email&"
    auth_url += f"state={state}&"
    auth_url += f"response_mode=query"
    
    # In a real implementation, you'd store the state in session
    # Here we're just returning the URL to redirect to
    return {"redirect_url": auth_url, "state": state}

# Endpoint to handle Azure AD callback
@router.get("/api/auth/callback")
async def azure_ad_callback(code: str = Query(...), state: str = Query(...)):
    """Handle Azure AD callback and exchange code for tokens"""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        raise HTTPException(status_code=500, detail="Azure AD configuration is incomplete")
    
    try:
        # Verify state parameter for security
        # Note: In a real implementation, you'd verify this against a stored session value
        # For now, we'll just log it
        logger.info(f"Received callback with state: {state}")
        
        # Exchange authorization code for tokens
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            logger.error(f"Failed to get token from Azure AD: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to authenticate with Azure AD")
        
        token_json = token_response.json()
        id_token = token_json.get('id_token')
        
        if not id_token:
            raise HTTPException(status_code=400, detail="No ID token received from Azure AD")
        
        # Validate ID token
        jwks_url = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
        jwks_response = requests.get(jwks_url)
        jwks = jwks_response.json()
        
        # Decode the token without verification first to get header info
        unverified_header = jose_jwt.get_unverified_header(id_token)
        kid = unverified_header['kid']
        
        # Find the correct key in the JWKS
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == kid:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
                break
        
        if not rsa_key:
            raise HTTPException(status_code=400, detail="Unable to find appropriate signing key")
        
        # Verify the token
        try:
            payload = jose_jwt.decode(
                id_token,
                rsa_key,
                algorithms=["RS256"],
                audience=CLIENT_ID,
                issuer=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
            )
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid token from Azure AD")
        
        # Extract user information
        user_id = payload.get('oid')
        email = payload.get('email', payload.get('preferred_username'))
        name = payload.get('name')
        
        # Get user roles from local in-memory storage with corporate default
        user_roles = get_user_roles_with_default(email)
        
        user_info = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'roles': user_roles
        }
        
        # Create a session token (in a real implementation, you'd use proper session management)
        session_token = secrets.token_urlsafe(32)
        
        # Log successful login
        logger.info(f"User {email} authenticated successfully. Roles: {user_roles}")
        
        # Redirect back to the frontend with the token and user info
        # Note: In production, you'd use a more secure way to pass the token (like a secure cookie)
        # For now, we'll use query parameters for simplicity
        target_url = f"/dashboard?token={session_token}&email={email}&name={urllib.parse.quote(name or '')}&roles={','.join(user_roles)}"
        return RedirectResponse(url=target_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Azure AD callback: {str(e)}", exc_info=True)
        # Redirect to an error page or show a friendly message
        return RedirectResponse(url="/?auth_error=true&details=" + urllib.parse.quote(str(e)))

# Endpoint to handle logout
@router.post("/api/auth/logout")
async def azure_ad_logout():
    """Handle user logout and session cleanup"""
    # In a real implementation, you'd clear the local session
    # For Azure AD logout, you'd redirect to Azure AD's logout endpoint
    
    # Azure AD logout URL
    logout_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout?post_logout_redirect_uri=https://aegis.com"
    
    # In a real implementation, you'd clear server-side session
    # For now, just return success
    return {
        "success": True,
        "message": "Logged out successfully",
        "redirect_url": logout_url  # URL to redirect to after clearing local session
    }

# Endpoint to get current user info
@router.get("/api/auth/me")
async def get_current_user(request: Request):
    """Get current user information (requires valid session)"""
    # In a real implementation, you'd validate the session token from headers/cookies
    # For now, return a mock response
    
    # This would validate the user session and return user details
    # along with their assigned roles from the local in-memory storage
    # For demo purposes, we'll return a default user
    return {
        "user_id": "mock-user-id",
        "email": "mock@example.com",
        "name": "Mock User",
        "roles": ["read_only"]  # Would come from local role mapping
    }

# Endpoint to get user roles from local mapping
@router.get("/api/auth/user/roles/{user_id}")
async def get_user_roles(user_id: str):
    """Get roles for a specific user from local mapping"""
    # This would query the local in-memory storage to get roles for a user
    # For now, return mock data
    return {
        "user_id": user_id,
        "roles": ["read_only"],
        "assigned_at": "2023-01-01T00:00:00Z"
    }

# Endpoint to add a user to local role mapping (temporary admin function)
@router.post("/api/auth/user/add")
async def add_user_to_local_roles(email: str, roles: List[str]):
    """Add a user to the local role mapping (temporary solution)"""
    LOCAL_USER_ROLES[email] = roles
    return {
        "email": email,
        "roles": roles,
        "message": f"User {email} added with roles {roles}"
    }

# Endpoint to get all users from local mapping
@router.get("/api/auth/users")
async def get_all_local_users():
    """Get all users from the local role mapping (temporary solution)"""
    users = []
    for email, roles in LOCAL_USER_ROLES.items():
        users.append({
            "email": email,
            "roles": roles
        })
    return {"users": users}
