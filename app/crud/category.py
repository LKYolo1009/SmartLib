from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate
from crud.base import CRUDBase

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    """分类CRUD操作类"""

    def get(self, db: Session, category_id: int) -> Optional[Category]:
        """
        根据ID获取分类
        :param db: 数据库会话
        :param category_id: 分类ID
        :return: 分类对象
        """
        return db.query(Category).filter(Category.category_id == category_id).first()
    
    def get_by_code(self, db: Session, category_code: str) -> Optional[Category]:
        """
        根据分类代码获取分类
        :param db: 数据库会话
        :param category_code: 分类代码
        :return: 分类对象
        """
        return db.query(Category).filter(Category.category_code == category_code).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """
        获取多个分类，支持分页
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 分类列表
        """
        return db.query(Category).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CategoryCreate) -> Category:
        """
        创建新分类
        :param db: 数据库会话
        :param obj_in: 包含分类数据的schema
        :return: 创建的分类对象
        """
        # 检查分类代码是否已存在
        existing_category = self.get_by_code(db, category_code=obj_in.category_code)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分类代码已存在"
            )
        
        db_obj = Category(
            category_name=obj_in.category_name,
            category_code=obj_in.category_code
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# 创建分类CRUD操作实例
category_crud = CRUDCategory(Category)