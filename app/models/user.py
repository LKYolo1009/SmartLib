from sqlalchemy import Column, Integer, String
from .base import Base

class User(Base):
    __tablename__ = 'users'
    
    # 用户ID，主键
    id = Column(Integer, primary_key=True)
    # 用户名，唯一
    username = Column(String(255), nullable=False, unique=True)
    # 加密后的密码
    hashed_password = Column(String(255), nullable=False)