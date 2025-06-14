from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from app.models.book import Book
from app.models.book_copy import BookCopy
from app.models.student import Student
from app.models.borrowing_record import BorrowingRecord
from app.models.author import Author
from app.models.category import Category
from app.schemas.stats import StudentStats, SystemStats

def get_student_stats(
    db: Session,
    *,
    telegram_id: str
) -> Optional[StudentStats]:
    """
    Get statistics for a student by telegram ID
    
    Args:
        db: Database session
        telegram_id: Student's telegram ID
        
    Returns:
        Student statistics
    """
    # 首先通过 telegram_id 查找学生
    student = db.query(Student).filter(Student.telegram_id == telegram_id).first()
    if not student:
        return None
        
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=3)
    
    # 获取总借阅数
    total_borrowed = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.matric_number == student.matric_number
    ).scalar()
    
    # 获取当前借阅数
    current_borrowed = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.matric_number == student.matric_number,
        BorrowingRecord.return_date.is_(None)
    ).scalar()
    
    # 获取逾期数
    overdue_count = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.matric_number == student.matric_number,
        BorrowingRecord.return_date.is_(None),
        BorrowingRecord.due_date < now
    ).scalar()
    
    # 获取即将到期数
    due_soon_count = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.matric_number == student.matric_number,
        BorrowingRecord.return_date.is_(None),
        BorrowingRecord.due_date > now,
        BorrowingRecord.due_date <= soon
    ).scalar()
    
    # 获取最常借阅的类别
    favorite_categories = db.query(
        Category.name, func.count(BorrowingRecord.borrow_id)
    ).join(
        Book, Category.category_id == Book.category_id
    ).join(
        BookCopy, Book.book_id == BookCopy.book_id
    ).join(
        BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
    ).filter(
        BorrowingRecord.matric_number == student.matric_number
    ).group_by(
        Category.name
    ).order_by(
        desc(func.count(BorrowingRecord.borrow_id))
    ).limit(5).all()
    
    # 获取最常借阅的作者
    favorite_authors = db.query(
        Author.name, func.count(BorrowingRecord.borrow_id)
    ).join(
        Book, Author.author_id == Book.author_id
    ).join(
        BookCopy, Book.book_id == BookCopy.book_id
    ).join(
        BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
    ).filter(
        BorrowingRecord.matric_number == student.matric_number
    ).group_by(
        Author.name
    ).order_by(
        desc(func.count(BorrowingRecord.borrow_id))
    ).limit(5).all()
    
    # 获取最后借阅日期
    last_borrowed = db.query(BorrowingRecord.borrow_date).filter(
        BorrowingRecord.matric_number == student.matric_number
    ).order_by(
        desc(BorrowingRecord.borrow_date)
    ).first()
    
    return StudentStats(
        total_borrowed=total_borrowed,
        current_borrowed=current_borrowed,
        overdue_count=overdue_count,
        due_soon_count=due_soon_count,
        favorite_categories=[c[0] for c in favorite_categories],
        favorite_authors=[a[0] for a in favorite_authors],
        last_borrowed_date=last_borrowed[0] if last_borrowed else None
    )

def get_system_stats(
    db: Session
) -> SystemStats:
    """
    Get system-wide statistics
    
    Args:
        db: Database session
        
    Returns:
        System statistics
    """
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    
    # 获取总图书数
    total_books = db.query(func.count(Book.book_id)).scalar()
    
    # 获取总副本数
    total_copies = db.query(func.count(BookCopy.copy_id)).scalar()
    
    # 获取总学生数
    total_students = db.query(func.count(Student.matric_number)).scalar()
    
    # 获取总借阅数
    total_borrowings = db.query(func.count(BorrowingRecord.borrow_id)).scalar()
    
    # 获取当前借阅数
    active_borrowings = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.return_date.is_(None)
    ).scalar()
    
    # 获取逾期借阅数
    overdue_borrowings = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.return_date.is_(None),
        BorrowingRecord.due_date < now
    ).scalar()
    
    # 获取热门类别
    popular_categories = db.query(
        Category.name, func.count(BorrowingRecord.borrow_id)
    ).join(
        Book, Category.category_id == Book.category_id
    ).join(
        BookCopy, Book.book_id == BookCopy.book_id
    ).join(
        BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
    ).group_by(
        Category.name
    ).order_by(
        desc(func.count(BorrowingRecord.borrow_id))
    ).limit(5).all()
    
    # 获取热门作者
    popular_authors = db.query(
        Author.name, func.count(BorrowingRecord.borrow_id)
    ).join(
        Book, Author.author_id == Book.author_id
    ).join(
        BookCopy, Book.book_id == BookCopy.book_id
    ).join(
        BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
    ).group_by(
        Author.name
    ).order_by(
        desc(func.count(BorrowingRecord.borrow_id))
    ).limit(5).all()
    
    # 获取最近30天的借阅数
    recent_borrowings = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.borrow_date >= thirty_days_ago
    ).scalar()
    
    return SystemStats(
        total_books=total_books,
        total_copies=total_copies,
        total_students=total_students,
        total_borrowings=total_borrowings,
        active_borrowings=active_borrowings,
        overdue_borrowings=overdue_borrowings,
        popular_categories=[c[0] for c in popular_categories],
        popular_authors=[a[0] for a in popular_authors],
        recent_borrowings=recent_borrowings
    ) 