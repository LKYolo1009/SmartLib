from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError  # 使用 python-jose 库
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import SessionLocal
from app.crud.user import CRUDUser
from app.models.user import User

# OAuth2密码流程的依赖项
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

def get_db() -> Generator:
    """
    获取数据库会话依赖项
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

