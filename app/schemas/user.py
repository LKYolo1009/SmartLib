from pydantic import BaseModel, Field, validator
from typing import Optional

class UserBase(BaseModel):
    """User's Basic Information"""
    username: str = Field(..., description="Username", example="admin")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username length"""
        if len(v) < 3:
            raise ValueError('Username length cannot be less than 3 characters')
        return v

class UserCreate(UserBase):
    """Model used when creating a user"""
    password: str = Field(..., description="Password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password length cannot be less than 8 characters')
        return v
class UserUpdate(UserBase):
    pass
class UserResponse(UserBase):
    """Model used when returning user information"""
    id: int

    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin"
            }
        }

class UserLogin(BaseModel):
    """Model used when user logs in"""
    username: str = Field(..., description="Username", example="admin")
    password: str = Field(..., description="Password")