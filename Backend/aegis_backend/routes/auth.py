# Authentication Route Module auth.py
# This module handles Azure AD SSO authentication and authorization using PostgreSQL
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
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
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for authentication endpoints
router = APIRouter()

# Schema for RBAC
PG_SCHEMA = "rbac"

# SSO Toggle
SSO_ENABLED = os.getenv("SSO_ENABLED", "True").lower() in ("true", "1", "yes")

# Configuration from environment variables
CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_AD_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
REDIRECT_URI = os.getenv("AZURE_AD_REDIRECT_URI", "https://aegis.adani.com/api/auth/callback")

def get_user_permissions_from_db(email: str) -> dict:
    """Get route-based permissions from PostgreSQL for a user"""
    if not email:
        return {"routes": [], "has_any_access": False}
    
    conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
    if not conn:
        logger.error("Failed to connect to PG for permissions")
        return {"routes": [], "has_any_access": False}
        
    try:
        cursor = get_pg_cursor(conn)
        # Query all active permissions for this user (case-insensitive)
        cursor.execute("""
            SELECT route_path, permission_type
            FROM route_permissions
            WHERE LOWER(email) = LOWER(%s) AND is_active = TRUE
        """, (email,))
        
        rows = cursor.fetchall()
        if not rows:
            return {"routes": [], "has_any_access": False}
        
        route_perms = {r["route_path"]: r["permission_type"] for r in rows}
        
        return {
            "routes": list(route_perms.keys()),
            "permissions": route_perms,
            "has_any_access": len(route_perms) > 0
        }
    except Exception as e:
        logger.error(f"Error fetching permissions: {e}")
        return {"routes": [], "has_any_access": False}
    finally:
        conn.close()

# Response models
class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

@router.get("/auth/config")
async def get_auth_config():
    return {"sso_enabled": SSO_ENABLED}

@router.get("/auth/login")
async def azure_ad_login():
    if not SSO_ENABLED:
        raise HTTPException(status_code=403, detail="SSO is disabled.")
    if not all([CLIENT_ID, TENANT_ID, REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="Azure AD config incomplete")
    
    state = secrets.token_urlsafe(32)
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
    auth_url += f"client_id={CLIENT_ID}&"
    auth_url += f"response_type=code&"
    auth_url += f"redirect_uri={REDIRECT_URI}&"
    auth_url += f"scope=openid profile email&"
    auth_url += f"state={state}&"
    auth_url += f"response_mode=query"
    
    return {"redirect_url": auth_url, "state": state}

@router.get("/auth/callback")
async def azure_ad_callback(code: str = Query(...), state: str = Query(...)):
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        raise HTTPException(status_code=500, detail="Azure AD config incomplete")
    
    try:
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
            raise HTTPException(status_code=400, detail="Failed to get token from Azure AD")
        
        id_token = token_response.json().get('id_token')
        oidc_config = requests.get(f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration").json()
        jwks_url = oidc_config.get('jwks_uri')
        jwks = requests.get(jwks_url).json()
        
        unverified_header = jose_jwt.get_unverified_header(id_token)
        kid = unverified_header.get('kid')
        
        rsa_key = next((k for k in jwks['keys'] if k['kid'] == kid), None)
        if not rsa_key:
            raise HTTPException(status_code=400, detail="Signing key not found")
        
        payload = jose_jwt.decode(id_token, rsa_key, algorithms=["RS256"], audience=CLIENT_ID, issuer=oidc_config.get('issuer'))
        
        email = payload.get('email', payload.get('preferred_username'))
        name = payload.get('name')
        user_perms = get_user_permissions_from_db(email)
        
        # Log to audit (Postgres)
        conn = get_pg_connection(os.getenv('POSTGRES_DATABASE_RBAC'))
        if conn:
            try:
                cursor = get_pg_cursor(conn)
                cursor.execute(f"INSERT INTO {PG_SCHEMA}.auth_audit_logs (email, event_type, event_details) VALUES (%s, %s, %s)",
                             (email, 'login', json.dumps({"status": "success", "routes": user_perms.get('routes', [])})))
                conn.commit()
            finally:
                conn.close()

        target_url = f"/?token={secrets.token_urlsafe(32)}&email={email}&name={urllib.parse.quote(name or '')}&has_access={user_perms.get('has_any_access', False)}"
        return RedirectResponse(url=target_url)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        return RedirectResponse(url="/?auth_error=true&details=" + urllib.parse.quote(str(e)))

@router.post("/auth/logout")
async def azure_ad_logout():
    logout_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout?post_logout_redirect_uri={urllib.parse.quote('https://aegis.adani.com')}"
    return {"success": True, "redirect_url": logout_url}

@router.get("/auth/me")
async def get_current_user(request: Request):
    raise HTTPException(status_code=401, detail="Not authenticated")
