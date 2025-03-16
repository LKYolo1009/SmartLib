from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError  
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import SessionLocal
from app.crud.user import CRUDUser
from app.models.user import User


# potential module for authentication
