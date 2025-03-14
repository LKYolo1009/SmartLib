from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from ..models.book import Book
from ..schemas.book import BookCreate, BookUpdate
from .base import CRUDBase

class CRUDBook(CRUDBase[Book, BookCreate, BookUpdate]):
    """图书CRUD操作类"""

    def get(self, db: Session, book_id: int) -> Optional[Book]:
        """
        根据ID获取图书
        :param db: 数据库会话
        :param book_id: 图书ID
        :return: 图书对象
        """
        return db.query(Book).filter(Book.book_id == book_id).first()
    
    def get_by_isbn(self, db: Session, isbn: str) -> Optional[Book]:
        """
        根据ISBN获取图书
        :param db: 数据库会话
        :param isbn: 图书ISBN
        :return: 图书对象
        """
        return db.query(Book).filter(Book.isbn == isbn).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """
        获取多本图书，支持分页
        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 图书列表
        """
        return db.query(Book).offset(skip).limit(limit).all()
    
    def get_by_category(
        self, db: Session, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """
        根据分类获取图书
        :param db: 数据库会话
        :param category_id: 分类ID
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 图书列表
        """
        return db.query(Book).filter(
            Book.category_id == category_id
        ).offset(skip).limit(limit).all()
    
    def get_by_author(
        self, db: Session, *, author_id: int, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """
        根据作者获取图书
        :param db: 数据库会话
        :param author_id: 作者ID
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 图书列表
        """
        return db.query(Book).filter(
            Book.author_id == author_id
        ).offset(skip).limit(limit).all()
    
    def search(
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """
        搜索图书
        :param db: 数据库会话
        :param query: 搜索关键词
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 图书列表
        """
        search_query = f"%{query}%"
        return db.query(Book).filter(
            Book.title.ilike(search_query) | 
            Book.isbn.ilike(search_query)
        ).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: BookCreate) -> Book:
        """
        创建新图书
        :param db: 数据库会话
        :param obj_in: 包含图书数据的schema
        :return: 创建的图书对象
        """
        # 检查ISBN是否已存在
        if obj_in.isbn:
            existing_book = self.get_by_isbn(db, isbn=obj_in.isbn)
            if existing_book:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ISBN已存在"
                )
        
        db_obj = Book(
            title=obj_in.title,
            isbn=obj_in.isbn,
            author_id=obj_in.author_id,
            publisher_id=obj_in.publisher_id,
            publication_year=obj_in.publication_year,
            language_code=obj_in.language_code,
            category_id=obj_in.category_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_with_details(self, db: Session, book_id: int) -> Optional[Book]:
        """
        获取图书详细信息，包括关联的作者、出版社、分类等
        :param db: 数据库会话
        :param book_id: 图书ID
        :return: 包含详细信息的图书对象
        """
        return db.query(Book).options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.language),
            joinedload(Book.category),
            joinedload(Book.copies)
        ).filter(Book.book_id == book_id).first()

# 创建图书CRUD操作实例
book_crud = CRUDBook(Book)