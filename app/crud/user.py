from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.base import CRUDBase
from app.core.security import get_password_hash, verify_password

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户CRUD操作类"""

    def get(self, db: Session, id: int) -> Optional[User]:
        """
        根据ID获取用户
        :param db: 数据库会话
        :param id: 用户ID
        :return: 用户对象
        """
        return db.query(User).filter(User.id == id).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        :param db: 数据库会话
        :param username: 用户名
        :return: 用户对象
        """
        return db.query(User).filter(User.username == username).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        创建新用户
        :param db: 数据库会话
        :param obj_in: 包含用户数据的schema
        :return: 创建的用户对象
        """
        # 检查用户名是否已存在
        existing_user = self.get_by_username(db, username=obj_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 创建新用户，密码哈希处理
        db_obj = User(
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def authenticate(
        self, db: Session, *, username: str, password: str
    ) -> Optional[User]:
        """
        验证用户
        :param db: 数据库会话
        :param username: 用户名
        :param password: 密码
        :return: 验证成功则返回用户对象，否则返回None
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
        修改用户密码
        :param db: 数据库会话
        :param user_id: 用户ID
        :param new_password: 新密码
        :return: 更新后的用户对象
        """
        user = self.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

# 创建用户CRUD操作实例
user_crud = CRUDUser(User)