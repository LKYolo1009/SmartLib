from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.language import Language
from ..schemas.language import LanguageCreate, LanguageUpdate
from .base import CRUDBase

class CRUDLanguage(CRUDBase[Language, LanguageCreate, LanguageUpdate]):
    """Language CRUD operations class"""

    def get(self, db: Session, language_code: str) -> Optional[Language]:
        """
        根据语言代码获取语言
        :param db: 数据库会话
        :param language_code: 语言代码
        :return: 语言对象
        """
        return db.query(Language).filter(Language.language_code == language_code).first()
    
    def get_by_name(self, db: Session, language_name: str) -> Optional[Language]:
        """
        根据名称获取语言
        :param db: 数据库会话
        :param language_name: 语言名称
        :return: 语言对象
        """
        return db.query(Language).filter(Language.language_name == language_name).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Language]:
        """
        获取多种语言，支持分页
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 语言列表
        """
        return db.query(Language).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: LanguageCreate) -> Language:
        """
        创建新语言
        :param db: 数据库会话
        :param obj_in: 包含语言数据的schema
        :return: 创建的语言对象
        """
        # Check if language code already exists
        existing_language = self.get(db, language_code=obj_in.language_code)
        if existing_language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language code already exists"
            )
        
        # Check if language name already exists
        existing_name = self.get_by_name(db, language_name=obj_in.language_name)
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language name already exists"
            )
        
        db_obj = Language(
            language_code=obj_in.language_code,
            language_name=obj_in.language_name
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Create language CRUD instance
language_crud = CRUDLanguage(Language)