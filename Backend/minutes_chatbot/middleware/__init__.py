"""
SSO Authentication Middleware for Minutes Chatbot

Integrates with Azure AD SSO from main aegis_backend.
Extracts user information from JWT tokens and manages chatbot user sessions.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os
from typing import Optional

from ..database.connection import get_db_session
from ..database.models import User
from ..config.settings import settings

# Security scheme
security = HTTPBearer()


class SSOAuth:
    """SSO Authentication handler"""
    
    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db_session)
    ) -> User:
        """
        Extract and verify user from SSO token.
        
        Args:
            credentials: Bearer token from Authorization header
            db: Database session
            
        Returns:
            User: Chatbot user object
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        token = credentials.credentials
        
        try:
            # Decode JWT token (Azure AD token)
            # Note: In production, you should verify the signature with Azure AD public keys
            payload = jwt.decode(
                token,
                options={"verify_signature": False}  # For development
                # In production, add proper verification:
                # key=settings.AZURE_AD_PUBLIC_KEY,
                # algorithms=["RS256"],
                # audience=settings.AZURE_AD_CLIENT_ID
            )
            
            # Extract user information
            email = payload.get("email") or payload.get("preferred_username")
            name = payload.get("name")
            sso_user_id = payload.get("oid")  # Azure AD Object ID
            
            if not email:
                raise HTTPException(
                    status_code=401,
                    detail="Email not found in token"
                )
            
            # Get or create chatbot user
            user = SSOAuth._get_or_create_user(
                db=db,
                email=email,
                name=name,
                sso_user_id=sso_user_id
            )
            
            return user
            
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid authentication token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Authentication error: {str(e)}"
            )
    
    @staticmethod
    def _get_or_create_user(
        db: Session,
        email: str,
        name: Optional[str],
        sso_user_id: Optional[str]
    ) -> User:
        """
        Get existing user or create new one from SSO login.
        
        Args:
            db: Database session
            email: User email from SSO
            name: User name from SSO
            sso_user_id: Azure AD Object ID
            
        Returns:
            User: Chatbot user object
        """
        from datetime import datetime
        
        # Try to find existing user by email
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update SSO ID if not set
            if not user.sso_user_id and sso_user_id:
                user.sso_user_id = sso_user_id
                db.commit()
            return user
        
        # Create new user
        user = User(
            email=email,
            name=name or email.split("@")[0],
            sso_user_id=sso_user_id,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user


# Dependency for routes
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Usage in routes:
        @router.post("/endpoint")
        async def endpoint(user: User = Depends(get_current_user)):
            # user is automatically extracted from SSO token
            pass
    """
    return SSOAuth.get_current_user(credentials, db)
