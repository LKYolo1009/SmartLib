from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct, case, desc
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import logging

# 配置日志
logger = logging.getLogger(__name__)

from ..models.book import Book
from ..models.book_copy import BookCopy
from ..models.borrowing_record import BorrowingRecord
from ..models.category import Category
from ..models.student import Student
from ..models.author import Author
from ..models.publisher import Publisher
from ..schemas.statistics import (
    DailyStats,
    CategoryStats,
    OverdueBooks,
    StudentStats,
    KPIMetrics,
    PopularBooks,
    BorrowingTrend,
    StudentActivity,
    LibraryUtilization
)

def get_daily_stats(
    db: Session,
    start_date: datetime,
    end_date: datetime
) -> List[DailyStats]:
    """Get daily borrowing and return statistics"""
    # Get daily borrow counts
    borrow_stats = db.query(
        func.date(BorrowingRecord.borrow_date).label('date'),
        func.count().label('total_borrows'),
        func.count(distinct(BorrowingRecord.matric_number)).label('active_readers')
    ).filter(
        BorrowingRecord.borrow_date.between(start_date, end_date)
    ).group_by(
        func.date(BorrowingRecord.borrow_date)
    ).all()

    # Get daily return counts
    return_stats = db.query(
        func.date(BorrowingRecord.return_date).label('date'),
        func.count().label('total_returns')
    ).filter(
        BorrowingRecord.return_date.between(start_date, end_date)
    ).group_by(
        func.date(BorrowingRecord.return_date)
    ).all()

    # Convert to dictionaries
    borrow_dict = {str(stat.date): {'total_borrows': stat.total_borrows, 'active_readers': stat.active_readers} for stat in borrow_stats}
    return_dict = {str(stat.date): stat.total_returns for stat in return_stats}

    # Generate complete date range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        borrow_data = borrow_dict.get(date_str, {'total_borrows': 0, 'active_readers': 0})
        return_count = return_dict.get(date_str, 0)
        date_range.append(DailyStats(
            date=current_date,
            total_borrows=borrow_data['total_borrows'],
            total_returns=return_count,
            active_readers=borrow_data['active_readers']
        ))
        current_date += timedelta(days=1)

    return date_range

def get_category_stats(db: Session) -> List[CategoryStats]:
    """Get book category statistics"""
    # 获取每个分类的统计信息
    stats = db.query(
        Category.category_name.label('category'),
        func.count(distinct(Book.book_id)).label('total_books'),
        func.sum(case(
            (BookCopy.status == 'available', 1),
            else_=0
        )).label('available_books'),
        func.sum(case(
            (BookCopy.status == 'borrowed', 1),
            else_=0
        )).label('borrowed_books'),
        func.count(distinct(BorrowingRecord.borrow_id)).label('borrow_count')
    ).outerjoin(
        Book, Book.category_id == Category.category_id
    ).outerjoin(
        BookCopy, Book.book_id == BookCopy.book_id
    ).outerjoin(
        BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
    ).group_by(
        Category.category_name
    ).all()

    # 转换为 CategoryStats 对象列表
    return [
        CategoryStats(
            category=stat.category,
            total_books=stat.total_books or 0,
            available_books=stat.available_books or 0,
            borrowed_books=stat.borrowed_books or 0,
            borrow_count=stat.borrow_count or 0
        )
        for stat in stats
    ]

def get_overdue_books(db: Session) -> List[OverdueBooks]:
    """Get list of overdue books"""
    overdue = db.query(
        Book.book_id,
        Book.title,
        Student.matric_number.label('student_id'),
        Student.full_name.label('student_name'),
        BorrowingRecord.due_date,
        func.extract('epoch', func.now() - BorrowingRecord.due_date).label('days_overdue')
    ).join(
        BookCopy, Book.book_id == BookCopy.book_id
    ).join(
        BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
    ).join(
        Student, BorrowingRecord.matric_number == Student.matric_number
    ).filter(
        and_(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date < datetime.now(timezone.utc),
            BorrowingRecord.status == 'borrowed'
        )
    ).all()

    return [
        OverdueBooks(
            book_id=record.book_id,
            title=record.title,
            student_id=record.student_id,
            student_name=record.student_name,
            due_date=record.due_date,
            days_overdue=int(record.days_overdue / 86400)  # 将秒转换为天
        )
        for record in overdue
    ]

def get_student_stats(db: Session) -> List[StudentStats]:
    """Get student borrowing statistics"""
    # 获取学生借阅统计信息
    stats = db.query(
        Student.matric_number.label('student_id'),
        Student.full_name.label('student_name'),
        func.count(distinct(BorrowingRecord.borrow_id)).label('total_borrows'),
        func.sum(case(
            (and_(
                BorrowingRecord.return_date.is_(None),
                BorrowingRecord.status == 'borrowed'
            ), 1),
            else_=0
        )).label('active_borrows'),
        func.sum(case(
            (and_(
                BorrowingRecord.return_date.is_(None),
                BorrowingRecord.due_date < datetime.now(timezone.utc),
                BorrowingRecord.status == 'borrowed'
            ), 1),
            else_=0
        )).label('overdue_count')
    ).outerjoin(
        BorrowingRecord, BorrowingRecord.matric_number == Student.matric_number
    ).group_by(
        Student.matric_number,
        Student.full_name
    ).all()

    # 转换为 StudentStats 对象列表
    return [
        StudentStats(
            student_id=stat.student_id,
            student_name=stat.student_name,
            total_borrows=stat.total_borrows or 0,
            active_borrows=stat.active_borrows or 0,
            overdue_count=stat.overdue_count or 0
        )
        for stat in stats
    ]

def get_kpi_metrics(db: Session) -> KPIMetrics:
    """Get KPI metrics"""
    total_books = db.query(func.count(Book.book_id)).scalar()
    total_students = db.query(func.count(Student.matric_number)).scalar()
    
    active_borrows = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        and_(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.status == 'borrowed'
        )
    ).scalar()
    
    overdue_books = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        and_(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date < datetime.now(timezone.utc),
            BorrowingRecord.status == 'borrowed'
        )
    ).scalar()

    # Calculate average borrow duration
    avg_duration = db.query(
        func.avg(
            func.extract('epoch', BorrowingRecord.return_date - BorrowingRecord.borrow_date) / 86400
        )
    ).filter(
        BorrowingRecord.return_date.isnot(None)
    ).scalar() or 0

    # Calculate return rate
    total_borrows = db.query(func.count(BorrowingRecord.borrow_id)).scalar()
    total_returns = db.query(func.count(BorrowingRecord.borrow_id)).filter(
        BorrowingRecord.return_date.isnot(None)
    ).scalar()
    return_rate = (total_returns / total_borrows * 100) if total_borrows > 0 else 0

    return KPIMetrics(
        total_books=total_books,
        total_students=total_students,
        active_borrows=active_borrows,
        overdue_books=overdue_books,
        average_borrow_duration=float(avg_duration),
        return_rate=float(return_rate)
    )

def get_borrowing_trends(
    db: Session,
    start_date: datetime,
    end_date: datetime,
    interval: str = "day"
) -> BorrowingTrend:
    """Get borrowing trends over time"""
    try:
        # Set date format based on interval
        if interval == "day":
            date_format = "%Y-%m-%d"
            group_by = func.date(BorrowingRecord.borrow_date)
        elif interval == "week":
            date_format = "%Y-%W"
            group_by = func.date_trunc('week', BorrowingRecord.borrow_date)
        else:  # month
            date_format = "%Y-%m"
            group_by = func.date_trunc('month', BorrowingRecord.borrow_date)

        # Get borrowing trends
        borrowings = db.query(
            group_by.label('date'),
            func.count().label('borrowings')
        ).filter(
            BorrowingRecord.borrow_date.between(start_date, end_date)
        ).group_by(
            group_by
        ).all()

        # Get return trends
        returns = db.query(
            group_by.label('date'),
            func.count().label('returns')
        ).filter(
            BorrowingRecord.return_date.between(start_date, end_date)
        ).group_by(
            group_by
        ).all()

        # Convert to dictionary format
        borrow_dict = {str(stat.date): stat.borrowings for stat in borrowings}
        return_dict = {str(stat.date): stat.returns for stat in returns}

        # Generate complete time series data
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            if interval == "day":
                date_str = current_date.strftime(date_format)
                next_date = current_date + timedelta(days=1)
            elif interval == "week":
                date_str = current_date.strftime(date_format)
                next_date = current_date + timedelta(weeks=1)
            else:  # month
                date_str = current_date.strftime(date_format)
                # Move to first day of next month
                if current_date.month == 12:
                    next_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    next_date = current_date.replace(month=current_date.month + 1, day=1)

            trend_data.append({
                "date": date_str,
                "borrowings": borrow_dict.get(date_str, 0),
                "returns": return_dict.get(date_str, 0)
            })
            current_date = next_date

        # Calculate total borrows
        total_borrows = sum(stat.borrowings for stat in borrowings)

        # Calculate unique readers
        unique_readers = db.query(
            func.count(distinct(BorrowingRecord.matric_number))
        ).filter(
            BorrowingRecord.borrow_date.between(start_date, end_date)
        ).scalar() or 0

        # Calculate average borrow duration
        avg_duration = db.query(
            func.avg(
                func.extract('epoch', BorrowingRecord.return_date - BorrowingRecord.borrow_date) / 86400
            )
        ).filter(
            BorrowingRecord.return_date.isnot(None),
            BorrowingRecord.borrow_date.between(start_date, end_date)
        ).scalar() or 0.0

        # Calculate category distribution
        category_dist = db.query(
            Category.category_name,
            func.count(BorrowingRecord.borrow_id).label('count')
        ).join(
            BookCopy, BookCopy.copy_id == BorrowingRecord.copy_id
        ).join(
            Book, Book.book_id == BookCopy.book_id
        ).join(
            Category, Category.category_id == Book.category_id
        ).filter(
            BorrowingRecord.borrow_date.between(start_date, end_date)
        ).group_by(
            Category.category_name
        ).all()

        # Convert category distribution to dictionary with integer values
        category_distribution = {
            cat.category_name: int(cat.count) if cat.count is not None else 0
            for cat in category_dist
        }

        return BorrowingTrend(
            time_period=interval,
            total_borrows=total_borrows,
            unique_readers=unique_readers,
            average_duration=float(avg_duration),
            category_distribution=category_distribution,
            data=trend_data
        )
    except Exception as e:
        logger.error(f"Error in get_borrowing_trends: {str(e)}", exc_info=True)
        raise

def get_student_activity(
    db: Session,
    limit: int,
    start_date: datetime,
    end_date: datetime
) -> List[StudentActivity]:
    """Get most active students based on borrowing frequency"""
    try:
        # 统计每个学生的借阅次数
        result = (
            db.query(
                Student.matric_number.label("student_id"),
                Student.full_name.label("student_name"),
                func.count(BorrowingRecord.borrow_id).label("borrow_count"),
                func.max(Category.category_name).label("favorite_category"),
                func.avg(func.extract('epoch', BorrowingRecord.return_date - BorrowingRecord.borrow_date) / 86400).label("average_borrow_duration"),
                (func.count(BorrowingRecord.return_date) / func.count(BorrowingRecord.borrow_id) * 100).label("return_rate")
            )
            .join(BorrowingRecord, BorrowingRecord.matric_number == Student.matric_number)
            .join(BookCopy, BookCopy.copy_id == BorrowingRecord.copy_id)
            .join(Book, Book.book_id == BookCopy.book_id)
            .join(Category, Book.category_id == Category.category_id)
            .filter(
                BorrowingRecord.borrow_date.between(start_date, end_date)
            )
            .group_by(Student.matric_number, Student.full_name)
            .order_by(func.count(BorrowingRecord.borrow_id).desc())
            .limit(limit)
            .all()
        )

        return [
            StudentActivity(
                student_id=row.student_id,
                student_name=row.student_name,
                borrow_count=row.borrow_count,
                favorite_category=row.favorite_category or "",
                average_borrow_duration=float(row.average_borrow_duration) if row.average_borrow_duration is not None else 0.0,
                return_rate=float(row.return_rate) if row.return_rate is not None else 0.0
            )
            for row in result
        ]
    except Exception as e:
        logger.error(f"Error in get_student_activity: {str(e)}", exc_info=True)
        raise

def get_popular_books(
    db: Session,
    limit: int = 10,
    start_date: datetime = None,
    end_date: datetime = None
) -> List[Dict]:
    """Get most popular books based on borrowing frequency"""
    try:
        # Build base query
        query = db.query(
            Book.book_id.label('book_id'),
            Book.title,
            Author.author_name.label('author'),
            Category.category_name.label('category'),
            func.count(BorrowingRecord.borrow_id).label('borrow_count'),
            func.sum(case((BookCopy.status == 'available', 1), else_=0)).label('availability')
        ).join(
            BookCopy, Book.book_id == BookCopy.book_id
        ).join(
            BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
        ).join(
            Category, Book.category_id == Category.category_id
        ).join(
            Author, Book.author_id == Author.author_id
        )

        # Add time filters
        if start_date:
            query = query.filter(BorrowingRecord.borrow_date >= start_date)
        if end_date:
            query = query.filter(BorrowingRecord.borrow_date <= end_date)

        # Group and sort
        query = query.group_by(
            Book.book_id,
            Book.title,
            Author.author_name,
            Category.category_name
        ).order_by(
            desc('borrow_count')
        ).limit(limit)

        # Execute query
        results = query.all()

        # Convert to list of dictionaries
        return [
            {
                'book_id': r.book_id,
                'title': r.title,
                'author': r.author,
                'category': r.category,
                'availability': r.availability or 0,
                'borrow_count': r.borrow_count
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Error in get_popular_books: {str(e)}", exc_info=True)
        raise

def get_library_utilization(
    db: Session,
    start_date: datetime,
    end_date: datetime
) -> LibraryUtilization:
    """Get library utilization metrics"""
    # 计算总藏书量
    total_books = db.query(func.count(BookCopy.copy_id)).scalar()
    
    # 计算当前借出数量
    borrowed_books = db.query(func.count(BookCopy.copy_id)).filter(
        BookCopy.status == 'borrowed'
    ).scalar()
    
    # 计算可用数量
    available_books = total_books - borrowed_books
    
    # 计算利用率
    utilization_rate = (borrowed_books / total_books * 100) if total_books > 0 else 0
    
    # 计算每日借阅量
    daily_borrows = db.query(
        func.date(BorrowingRecord.borrow_date).label('date'),
        func.count().label('count')
    ).filter(
        BorrowingRecord.borrow_date.between(start_date, end_date)
    ).group_by(
        func.date(BorrowingRecord.borrow_date)
    ).all()
    
    # 转换为字典格式
    daily_utilization = {
        str(stat.date): stat.count
        for stat in daily_borrows
    }
    
    return LibraryUtilization(
        total_books=total_books,
        borrowed_books=borrowed_books,
        available_books=available_books,
        utilization_rate=utilization_rate,
        daily_utilization=daily_utilization
    )