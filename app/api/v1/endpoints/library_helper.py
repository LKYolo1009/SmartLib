from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import random
import string

from . import book, book_copy, schemas, models
from .database import get_db

router = APIRouter(prefix="/library", tags=["Library Helper"])

@router.post("/add-new-book", response_model=schemas.CompleteBookResponse)
def add_new_book(
    book_data: schemas.BookCreate,
    initial_copies: int = 1,
    db: Session = Depends(get_db)
):
    """
    一站式添加新书，同时创建书籍元数据和指定数量的副本。
    适合聊天机器人调用的简化流程。
    """
    # 1. 创建书籍元数据
    db_book = book.create_book(db=db, book=book_data)
    
    # 2. 创建指定数量的副本
    copies = []
    for i in range(initial_copies):
        copy_data = schemas.BookCopyCreate(
            book_id=db_book.id,
            call_number=book_data.call_number or generate_call_number(db_book.category),
            status="available"
        )
        db_copy = book_copy.create_book_copy(db=db, book_copy=copy_data)
        copies.append(db_copy)
    
    # 3. 构建完整响应
    return {
        "book": db_book,
        "copies": copies
    }

@router.post("/add-book-copy", response_model=schemas.BookCopyResponse)
def add_book_copy(
    copy_data: schemas.BookCopyCreate,
    db: Session = Depends(get_db)
):
    """
    为现有书籍添加新副本。
    如果没有提供call_number，将自动生成一个。
    """
    # 检查书籍是否存在
    db_book = book.get_book(db, book_id=copy_data.book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # 如果没有提供call_number，生成一个
    if not copy_data.call_number:
        copy_data.call_number = generate_call_number(db_book.category)
    
    # 创建副本
    return book_copy.create_book_copy(db=db, book_copy=copy_data)

@router.get("/book-info/{identifier}", response_model=schemas.BookDetailResponse)
def get_book_info(
    identifier: str,
    search_by: str = Query("auto", description="搜索方式: isbn, title, call_number 或 auto"),
    db: Session = Depends(get_db)
):
    """
    综合查询书籍信息，支持通过ISBN、标题或索书号查询。
    auto模式会自动尝试多种查询方式。
    返回书籍信息和所有副本信息。
    """
    db_book = None
    
    # 自动检测查询类型或使用指定类型
    if search_by == "auto" or search_by == "isbn":
        # 尝试按ISBN查询
        db_book = book.get_book_by_isbn(db, isbn=identifier)
        if db_book and search_by != "auto":
            return build_book_detail_response(db, db_book)
    
    if (search_by == "auto" or search_by == "title") and not db_book:
        # 尝试按标题查询
        books = book.search_books_by_title(db, title=identifier)
        if books and len(books) == 1:
            db_book = books[0]
            if search_by != "auto":
                return build_book_detail_response(db, db_book)
    
    if (search_by == "auto" or search_by == "call_number") and not db_book:
        # 尝试按索书号查询
        db_copy = book_copy.get_book_copy_by_call_number(db, call_number=identifier)
        if db_copy:
            db_book = book.get_book(db, book_id=db_copy.book_id)
    
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return build_book_detail_response(db, db_book)

@router.get("/availability/{book_id}", response_model=schemas.BookAvailabilityResponse)
def get_book_availability(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    获取特定书籍的可用性信息，包括总副本数和当前可借阅数量。
    """
    # 检查书籍是否存在
    db_book = book.get_book(db, book_id=book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # 获取所有副本
    copies = book_copy.get_book_copies_by_book_id(db, book_id=book_id)
    
    # 统计可用副本
    total_copies = len(copies)
    available_copies = sum(1 for copy in copies if copy.status == "available")
    
    return {
        "book_id": book_id,
        "title": db_book.title,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "is_available": available_copies > 0
    }

# 辅助函数

def generate_call_number(category: str) -> str:
    """生成唯一的索书号"""
    # 根据类别生成前缀
    prefix = category[:2].upper() if category else "LB"
    
    # 生成随机数字部分
    numbers = ''.join(random.choices(string.digits, k=4))
    
    # 生成小数部分
    decimal = ''.join(random.choices(string.digits, k=2))
    
    return f"{prefix}{numbers}.{decimal}"

def build_book_detail_response(db: Session, db_book: models.Book) -> dict:
    """构建详细的书籍信息响应，包括所有副本"""
    copies = book_copy.get_book_copies_by_book_id(db, book_id=db_book.id)
    
    # 统计可用副本
    total_copies = len(copies)
    available_copies = sum(1 for copy in copies if copy.status == "available")
    
    return {
        "book": db_book,
        "copies": copies,
        "availability": {
            "total_copies": total_copies,
            "available_copies": available_copies,
            "is_available": available_copies > 0
        }
    }