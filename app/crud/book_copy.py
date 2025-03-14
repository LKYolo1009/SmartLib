from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from ..models.book_copy import BookCopy
from ..schemas.book_copy import BookCopyCreate, BookCopyUpdate
from .base import CRUDBase

class CRUDBookCopy(CRUDBase[BookCopy, BookCopyCreate, BookCopyUpdate]):
    """图书副本CRUD操作类"""

    def get(self, db: Session, copy_id: int) -> Optional[BookCopy]:
        """
        根据ID获取图书副本
        :param db: 数据库会话
        :param copy_id: 副本ID
        :return: 图书副本对象
        """
        return db.query(BookCopy).filter(BookCopy.copy_id == copy_id).first()
    
    def get_with_book(self, db: Session, copy_id: int) -> Optional[BookCopy]:
        """
        获取图书副本及其关联的图书信息
        :param db: 数据库会话
        :param copy_id: 副本ID
        :return: 图书副本对象
        """
        return db.query(BookCopy).options(
            joinedload(BookCopy.book)
        ).filter(BookCopy.copy_id == copy_id).first()
    
    def get_by_call_number(self, db: Session, call_number: str) -> Optional[BookCopy]:
        """
        根据索书号获取图书副本
        :param db: 数据库会话
        :param call_number: 索书号
        :return: 图书副本对象
        """
        return db.query(BookCopy).filter(BookCopy.call_number == call_number).first()
    
    def get_by_qr_code(self, db: Session, qr_code: str) -> Optional[BookCopy]:
        """
        根据QR码获取图书副本
        :param db: 数据库会话
        :param qr_code: QR码
        :return: 图书副本对象
        """
        return db.query(BookCopy).filter(BookCopy.qr_code == qr_code).first()
    
    def get_by_book(
        self, db: Session, *, book_id: int, skip: int = 0, limit: int = 100
    ) -> List[BookCopy]:
        """
        获取指定图书的所有副本
        :param db: 数据库会话
        :param book_id: 图书ID
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 图书副本列表
        """
        return db.query(BookCopy).filter(
            BookCopy.book_id == book_id
        ).offset(skip).limit(limit).all()
    
    def get_available_by_book(
        self, db: Session, *, book_id: int, skip: int = 0, limit: int = 100
    ) -> List[BookCopy]:
        """
        获取指定图书的所有可借阅副本
        :param db: 数据库会话
        :param book_id: 图书ID
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 可借阅的图书副本列表
        """
        return db.query(BookCopy).filter(
            BookCopy.book_id == book_id,
            BookCopy.status == "available"
        ).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: BookCopyCreate) -> BookCopy:
        """
        创建新的图书副本
        :param db: 数据库会话
        :param obj_in: 包含图书副本数据的schema
        :return: 创建的图书副本对象
        """
        # 检查索书号是否已存在
        existing_copy = self.get_by_call_number(db, call_number=obj_in.call_number)
        if existing_copy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="索书号已存在"
            )
        
        db_obj = BookCopy(
            book_id=obj_in.book_id,
            call_number=obj_in.call_number,
            acquisition_type=obj_in.acquisition_type,
            acquisition_date=obj_in.acquisition_date,
            price=obj_in.price,
            condition=obj_in.condition,
            status=obj_in.status,
            notes=obj_in.notes
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_status(
        self, db: Session, *, copy_id: int, status: str
    ) -> BookCopy:
        """
        更新图书副本状态
        :param db: 数据库会话
        :param copy_id: 副本ID
        :param status: 新状态
        :return: 更新后的图书副本对象
        """
        db_obj = self.get(db, copy_id=copy_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="图书副本不存在"
            )
        
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# 创建图书副本CRUD操作实例
book_copy_crud = CRUDBookCopy(BookCopy)