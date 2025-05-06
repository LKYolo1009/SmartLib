from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.base import CRUDBase
from app.core.security import get_password_hash, verify_password

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """User CRUD operations class"""

    def get(self, db: Session, id: int) -> Optional[User]:
        """
        Get user by ID
        :param db: Database session
        :param id: User ID
        :return: User object
        """
        return db.query(User).filter(User.id == id).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get user by username
        :param db: Database session
        :param username: Username
        :return: User object
        """
        return db.query(User).filter(User.username == username).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user"""
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == obj_in.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Create new user with hashed password
        db_obj = User(
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            email=obj_in.email,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def authenticate(
        self, db: Session, *, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user
        :param db: Database session
        :param username: Username
        :param password: Password
        :return: Authenticated user object, or None if authentication fails
        """
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def change_password(
        self, db: Session, *, user_id: int, new_password: str
    ) -> User:
        """
        Change user password
        :param db: Database session
        :param user_id: User ID
        :param new_password: New password
        :return: Updated user object
        """
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User does not exist"
            )
        
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

# Create user CRUD instance
user_crud = CRUDUser(User)