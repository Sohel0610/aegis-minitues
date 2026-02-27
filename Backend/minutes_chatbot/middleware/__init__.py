"""
Middleware package for minutes_chatbot.
Authentication has been replaced with a static local guest user.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..database.connection import get_db_session
from ..database.models import User

def get_current_user(db: Session = Depends(get_db_session)) -> User:
    """
    Returns a static local guest user.
    Authentication is disabled, so we always return or create a default guest user.
    """
    guest_email = "guest@adani.com"
    guest_name = "Guest User"
    
    # Try to find existing guest user
    user = db.query(User).filter(User.email == guest_email).first()
    
    if not user:
        # Create new guest user if not exists
        user = User(
            email=guest_email,
            name=guest_name,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user

class MockAuth:
    """Mock auth class for backward compatibility if needed"""
    @staticmethod
    def get_current_user(db: Session = Depends(get_db_session)) -> User:
        return get_current_user(db)
