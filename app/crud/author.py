from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.author import Author
from schemas.author import AuthorCreate, AuthorUpdate
from crud.base import CRUDBase

class CRUDAuthor(CRUDBase[Author, AuthorCreate, AuthorUpdate]):
    """作者CRUD操作类"""

    def get(self, db: Session, author_id: int) -> Optional[Author]:
        """
        根据ID获取作者
        :param db: 数据库会话
        :param author_id: 作者ID
        :return: 作者对象
        """
        return db.query(Author).filter(Author.author_id == author_id).first()
    
    def get_by_name(self, db: Session, author_name: str) -> Optional[Author]:
        """
        根据名称获取作者
        :param db: 数据库会话
        :param author_name: 作者名称
        :return: 作者对象
        """
        return db.query(Author).filter(Author.author_name == author_name).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Author]:
        """
        获取多个作者，支持分页
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 作者列表
        """
        return db.query(Author).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: AuthorCreate) -> Author:
        """
        创建新作者
        :param db: 数据库会话
        :param obj_in: 包含作者数据的schema
        :return: 创建的作者对象
        """
        # 检查作者名称是否已存在
        existing_author = self.get_by_name(db, author_name=obj_in.author_name)
        if existing_author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="作者名称已存在"
            )
        
        db_obj = Author(
            author_name=obj_in.author_name
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# 创建作者CRUD操作实例
author_crud = CRUDAuthor(Author)