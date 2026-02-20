"""
Authentication Service

Handles user authentication (email-based).
"""

from sqlalchemy.orm import Session
from minutes_chatbot.database.models import User
from minutes_chatbot.config import logger
from datetime import datetime


class AuthService:
    """Service for user authentication"""
    
    @staticmethod
    def login_or_create_user(db: Session, email: str, name: str = None) -> User:
        """
        Login user or create new user if doesn't exist.
        
        Args:
            db: Database session
            email: User's email
            name: User's name (optional)
        
        Returns:
            User object
        """
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update last_active timestamp
            user.last_active = datetime.now()
            db.commit()
            db.refresh(user)
            logger.info(f"User logged in: {email}")
            return user
        else:
            # Create new user
            new_user = User(email=email, name=name)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            logger.info(f"New user created: {email}")
            return new_user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
