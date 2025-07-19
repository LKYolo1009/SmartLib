from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, text, or_
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone

from ..models.borrowing_record import BorrowingRecord
from ..models.book_copy import BookCopy
from ..models.book import Book
from ..models.student import Student
from ..schemas.borrowing import BorrowCreate, BorrowStatus
from .base import CRUDBase


class CRUDBorrowing(CRUDBase[BorrowingRecord, BorrowCreate, Dict]):
    def get(self, db: Session, borrow_id: int) -> Optional[BorrowingRecord]:
        """Get borrowing record by ID"""
        return db.query(BorrowingRecord).filter(BorrowingRecord.borrow_id == borrow_id).first()

    def get_with_details(self, db: Session, borrow_id: int) -> Optional[BorrowingRecord]:
        """Get borrowing record with all related details"""
        record = db.query(BorrowingRecord).options(
            joinedload(BorrowingRecord.student),
            joinedload(BorrowingRecord.copy).joinedload(BookCopy.book)
        ).filter(
            BorrowingRecord.borrow_id == borrow_id
        ).first()

        if not record:
            return None

        # Add computed fields
        self._add_computed_fields(record)
        return record

    def _add_computed_fields(self, record):
        """Add computed fields to borrowing record"""
        # Add student information
        if record.student:
            record.student_name = record.student.full_name
            record.student_email = record.student.email
            record.student_telegram_id = record.student.telegram_id

        # Add book information
        if record.copy and record.copy.book:
            record.book_title = record.copy.book.title
            record.call_number = record.copy.book.call_number

        # Calculate remaining days and overdue status
        if record.return_date:
            record.days_remaining = 0
            record.is_overdue = False
        else:
            # Convert all dates to UTC for consistent comparison
            now = datetime.now(timezone.utc)
            due_date_utc = record.due_date.astimezone(timezone.utc)
            days_remaining = (due_date_utc - now).days
            record.days_remaining = days_remaining
            record.is_overdue = days_remaining < 0

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "borrow_date",
        order: str = "desc"
    ) -> List[BorrowingRecord]:
        """Get multiple borrowing records with pagination and sorting"""
        query = db.query(BorrowingRecord).options(
            joinedload(BorrowingRecord.student),
            joinedload(BorrowingRecord.copy).joinedload(BookCopy.book)
        )

        if sort_by in ["borrow_date", "due_date", "return_date"]:
            sort_column = getattr(BorrowingRecord, sort_by)
            if order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        records = query.offset(skip).limit(limit).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_active(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "due_date",
        order: str = "asc"
    ) -> List[BorrowingRecord]:
        """Get active (not returned) borrowing records"""
        query = db.query(BorrowingRecord).filter(BorrowingRecord.return_date.is_(None))

        if sort_by in ["borrow_date", "due_date"]:
            sort_column = getattr(BorrowingRecord, sort_by)
            if order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        records = query.offset(skip).limit(limit).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_returned(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "return_date",
        order: str = "desc"
    ) -> List[BorrowingRecord]:
        """Get returned borrowing records"""
        query = db.query(BorrowingRecord).filter(BorrowingRecord.return_date.isnot(None))

        if sort_by in ["borrow_date", "due_date", "return_date"]:
            sort_column = getattr(BorrowingRecord, sort_by)
            if order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        records = query.offset(skip).limit(limit).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_overdue(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "due_date",
        order: str = "asc",
        due_date_threshold: Optional[datetime] = None
    ) -> List[BorrowingRecord]:
        """Get overdue borrowing records"""
        now = datetime.now(timezone.utc)
        threshold = due_date_threshold or now

        query = db.query(BorrowingRecord).filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date < threshold
        )

        if sort_by in ["borrow_date", "due_date"]:
            sort_column = getattr(BorrowingRecord, sort_by)
            if order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        records = query.offset(skip).limit(limit).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def create_borrow(self, db: Session, obj_in: BorrowCreate) -> BorrowingRecord:
        """Create a new borrowing record"""
        print(f"Searching for student with matric_number: '{obj_in.matric_number}'")
        student = db.query(Student).filter(Student.matric_number == obj_in.matric_number).first()
        print(f"Query result: {student}")
        # find student by matric number
        student = db.query(Student).filter(Student.matric_number == obj_in.matric_number).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with matriculation number {obj_in.matric_number} not found"
            )

        # check student status
        if student.status == 'suspended':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Student {student.full_name} is suspended and cannot borrow books"
            )

        # check active borrowings
        active_borrowings = db.query(BorrowingRecord).filter(
            BorrowingRecord.matric_number == obj_in.matric_number,
            BorrowingRecord.return_date.is_(None)
        ).count()

        if active_borrowings >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student {student.full_name} has reached maximum borrowing limit (3)"
            )

        # find book copy
        book_copy = db.query(BookCopy).filter(BookCopy.copy_id == obj_in.copy_id).first()
        if not book_copy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book copy with ID {obj_in.copy_id} not found"
            )

        # check if book copy is available
        if book_copy.status != 'available':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book copy {book_copy.copy_id} is not available (current status: {book_copy.status})"
            )

        # calculate dates
        borrow_date = datetime.now(timezone.utc)
        loan_days = obj_in.loan_days or 14  # if not specified, default 14 days
        due_date = borrow_date + timedelta(days=loan_days)

        try:
            # update book copy status
            book_copy.status = 'borrowed'
            db.add(book_copy)
            db.flush()  # do not commit

            # create borrowing record - do not use BorrowStatus enum, but use string directly
            # this can avoid triggering the check in the validator for the student
            borrow_record = BorrowingRecord(
                copy_id=obj_in.copy_id,
                matric_number=obj_in.matric_number,
                borrow_date=borrow_date,
                due_date=due_date,
                status='borrowed'  # Use string directly instead of BorrowStatus.BORROWED
            )

            db.add(borrow_record)
            db.commit()
            db.refresh(borrow_record)

            # add computed fields
            self._add_computed_fields(borrow_record)

            return borrow_record
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    def return_book(self, db: Session, *, borrow_id: int) -> BorrowingRecord:
        """Return a book"""
        borrow = self.get(db, borrow_id=borrow_id)
        if not borrow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Borrowing record with ID {borrow_id} not found"
            )

        if borrow.return_date is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book has already been returned on {borrow.return_date}"
            )

        try:
            # Update borrowing record
            now = datetime.now(timezone.utc)
            borrow.return_date = now
            borrow.status = BorrowStatus.RETURNED

            # Update book copy status
            book_copy = db.query(BookCopy).filter(BookCopy.copy_id == borrow.copy_id).first()
            if book_copy:
                book_copy.status = 'available'
                db.add(book_copy)

            db.add(borrow)
            db.commit()
            db.refresh(borrow)

            # Add computed fields
            self._add_computed_fields(borrow)

            return borrow
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    def extend_due_date(self, db: Session, *, borrow_id: int, days: int) -> BorrowingRecord:
        """Extend the due date of a borrowing record"""
        borrow = self.get(db, borrow_id=borrow_id)
        if not borrow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Borrowing record with ID {borrow_id} not found"
            )

        if borrow.return_date is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot extend a returned book (returned on {borrow.return_date})"
            )

        if borrow.extension_date is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book has already been extended once"
            )

        try:
            # Calculate new due date
            new_due_date = borrow.due_date + timedelta(days=days)

            # Update borrowing record
            # Set extension_date to the current due_date (before extension)
            # Ensure both dates are in the same timezone
            current_due_date = borrow.due_date
            if current_due_date.tzinfo is None:
                current_due_date = current_due_date.replace(tzinfo=timezone.utc)
            
            borrow.extension_date = current_due_date
            borrow.due_date = new_due_date

            db.add(borrow)
            db.commit()
            db.refresh(borrow)

            # Add computed fields
            self._add_computed_fields(borrow)

            return borrow
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    def get_by_matric_number(
        self,
        db: Session,
        *,
        matric_number: str,
        active_only: bool = False
    ) -> List[BorrowingRecord]:
        """Get borrowing records for a student by matriculation number"""
        query = db.query(BorrowingRecord).filter(
            BorrowingRecord.matric_number == matric_number
        )

        if active_only:
            query = query.filter(BorrowingRecord.return_date.is_(None))

        records = query.order_by(desc(BorrowingRecord.borrow_date)).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_by_book(
        self,
        db: Session,
        *,
        book_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[BorrowingRecord]:
        """Get borrowing records for a book across all its copies"""
        records = db.query(BorrowingRecord).join(
            BookCopy, BorrowingRecord.copy_id == BookCopy.copy_id
        ).filter(
            BookCopy.book_id == book_id
        ).order_by(desc(BorrowingRecord.borrow_date)).offset(skip).limit(limit).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_due_soon(
        self,
        db: Session,
        *,
        days: int = 3,
        limit: int = 100
    ) -> List[BorrowingRecord]:
        """Get borrowing records due soon (for reminders)"""
        now = datetime.now(timezone.utc)
        soon = now + timedelta(days=days)

        records = db.query(BorrowingRecord).filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date > now,
            BorrowingRecord.due_date <= soon
        ).order_by(BorrowingRecord.due_date).limit(limit).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_popular_books(
        self,
        db: Session,
        *,
        days: int = 90,
        limit: int = 10
    ) -> List[Dict]:
        """Get most popular books in a time period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        popular_books = db.query(
            Book.book_id,
            Book.title,
            func.count(BorrowingRecord.borrow_id).label('borrow_count')
        ).join(
            BookCopy, Book.book_id == BookCopy.book_id
        ).join(
            BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
        ).filter(
            BorrowingRecord.borrow_date >= cutoff_date
        ).group_by(
            Book.book_id
        ).order_by(
            desc('borrow_count')
        ).limit(limit).all()

        # Convert SQLAlchemy Row objects to dictionaries
        return [
            {
                "book_id": book.book_id,
                "title": book.title,
                "borrow_count": book.borrow_count
            }
            for book in popular_books
        ]


    def get_student_borrowing_stats(
        self,
        db: Session,
        *,
        matric_number: str
    ) -> Dict[str, Any]:
        """Get borrowing statistics for a specific student"""
        now = datetime.now(timezone.utc)

        # Total borrowings
        total_count = db.query(func.count(BorrowingRecord.borrow_id)).filter(
            BorrowingRecord.matric_number == matric_number
        ).scalar() or 0

        # Active borrowings
        active_count = db.query(func.count(BorrowingRecord.borrow_id)).filter(
            BorrowingRecord.matric_number == matric_number,
            BorrowingRecord.return_date.is_(None)
        ).scalar() or 0

        # Overdue borrowings
        overdue_count = db.query(func.count(BorrowingRecord.borrow_id)).filter(
            BorrowingRecord.matric_number == matric_number,
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date < now
        ).scalar() or 0

        # Average days kept
        avg_days_query = db.query(
            func.avg(
                func.julianday(BorrowingRecord.return_date) -
                func.julianday(BorrowingRecord.borrow_date)
            )
        ).filter(
            BorrowingRecord.matric_number == matric_number,
            BorrowingRecord.return_date.isnot(None)
        )
        avg_days_kept = avg_days_query.scalar() or 0

        # Recent borrowing history
        recent_history = self.get_by_matric_number(
            db,
            matric_number=matric_number,
            active_only=False
        )[:5]  # Limit to 5 most recent

        # Student information
        student = db.query(Student).filter(Student.matric_number == matric_number).first()

        return {
            "student_info": {
                "matric_number": matric_number,
                "name": student.full_name if student else "Unknown",
                "email": student.email if student else None
            },
            "total_borrowings": total_count,
            "active_borrowings": active_count,
            "overdue_borrowings": overdue_count,
            "average_days_kept": round(float(avg_days_kept), 1),
            "recent_history": recent_history
        }

    def get_active_borrowings(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        overdue_only: bool = False,
        matric_number: Optional[str] = None
    ) -> List[BorrowingRecord]:
        """Get active borrowings with filters"""
        query = db.query(BorrowingRecord).filter(
            BorrowingRecord.return_date.is_(None)
        )

        if overdue_only:
            now = datetime.now(timezone.utc)
            query = query.filter(BorrowingRecord.due_date < now)

        if matric_number:
            query = query.filter(BorrowingRecord.matric_number == matric_number)

        records = query.order_by(BorrowingRecord.due_date).offset(skip).limit(limit).all()

        # Add computed fields
        for record in records:
            self._add_computed_fields(record)

        return records

    def count_active_borrowings(
        self,
        db: Session,
        *,
        overdue_only: bool = False,
        matric_number: Optional[str] = None
    ) -> int:
        """Count active borrowings with filters"""
        query = db.query(func.count(BorrowingRecord.borrow_id)).filter(
            BorrowingRecord.return_date.is_(None)
        )

        if overdue_only:
            now = datetime.now(timezone.utc)
            query = query.filter(BorrowingRecord.due_date < now)

        if matric_number:
            query = query.filter(BorrowingRecord.matric_number == matric_number)

        return query.scalar() or 0

    def search_borrowings(
        self,
        db: Session,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[BorrowingRecord]:
        """Search borrowings by various fields"""
        search_pattern = f"%{query}%"

        records = db.query(BorrowingRecord).join(
            Student, BorrowingRecord.matric_number == Student.matric_number
        ).join(
            BookCopy, BorrowingRecord.copy_id == BookCopy.copy_id
        ).join(
            Book, BookCopy.book_id == Book.book_id
        ).filter(
            or_(
                Student.full_name.ilike(search_pattern),
                Student.matric_number.ilike(search_pattern),
                Book.title.ilike(search_pattern),
                Book.isbn.ilike(search_pattern),
                BookCopy.call_number.ilike(search_pattern)
            )
        ).order_by(desc(BorrowingRecord.borrow_date)).offset(skip).limit(limit).all()

        # Add computed fields
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_by_telegram_id(
        self,
        db: Session,
        *,
        telegram_id: str,
        active_only: bool = False
    ) -> List[BorrowingRecord]:
        """Get borrowing records for a student by telegram ID"""
        query = db.query(BorrowingRecord).join(
            Student, BorrowingRecord.matric_number == Student.matric_number
        ).filter(
            Student.telegram_id == telegram_id
        )

        if active_only:
            query = query.filter(BorrowingRecord.return_date.is_(None))

        records = query.order_by(desc(BorrowingRecord.borrow_date)).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_student_borrowing_stats(
        self,
        db: Session,
        *,
        telegram_id: str
    ) -> Dict[str, Any]:
        """Get borrowing statistics for a student by telegram ID"""
        student = db.query(Student).filter(Student.telegram_id == telegram_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with telegram ID {telegram_id} not found"
            )
        
        return self.get_student_borrowing_stats(db, matric_number=student.matric_number)

    def get_due_soon_by_telegram_id(
        self,
        db: Session,
        *,
        telegram_id: str,
        days: int = 3,
        limit: int = 100
    ) -> List[BorrowingRecord]:
        """Get borrowing records due soon for a student by telegram ID"""
        now = datetime.now(timezone.utc)
        soon = now + timedelta(days=days)

        records = db.query(BorrowingRecord).join(
            Student, BorrowingRecord.matric_number == Student.matric_number
        ).filter(
            Student.telegram_id == telegram_id,
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date > now,
            BorrowingRecord.due_date <= soon
        ).order_by(BorrowingRecord.due_date).limit(limit).all()

        # Add computed fields
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_overdue_by_telegram_id(
        self,
        db: Session,
        *,
        telegram_id: str,
        skip: int = 0,
        limit: int = 100,
        due_date_threshold: Optional[datetime] = None
    ) -> List[BorrowingRecord]:
        """Get overdue borrowing records for a student by telegram ID"""
        now = datetime.now(timezone.utc)
        threshold = due_date_threshold or now

        records = db.query(BorrowingRecord).join(
            Student, BorrowingRecord.matric_number == Student.matric_number
        ).filter(
            Student.telegram_id == telegram_id,
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date < threshold
        ).order_by(BorrowingRecord.due_date).offset(skip).limit(limit).all()

        # Add computed fields
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_by_student_identifier(
        self,
        db: Session,
        *,
        identifier: str,
        active_only: bool = False
    ) -> List[BorrowingRecord]:
        """
        Get borrowing records for a student by matric number or telegram ID
        
        Args:
            db: Database session
            identifier: Matric number or telegram ID
            active_only: If True, only return active borrowings
            
        Returns:
            List of borrowing records
        """
        # 首先尝试通过 telegram_id 查找学生
        student = db.query(Student).filter(Student.telegram_id == identifier).first()
        if student:
            matric_number = student.matric_number
        else:
            # 如果不是 telegram_id，则假设是 matric_number
            matric_number = identifier
        
        query = db.query(BorrowingRecord).filter(
            BorrowingRecord.matric_number == matric_number
        )

        if active_only:
            query = query.filter(BorrowingRecord.return_date.is_(None))

        records = query.order_by(desc(BorrowingRecord.borrow_date)).all()

        # Add computed fields to each record
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_due_soon_by_student_identifier(
        self,
        db: Session,
        *,
        identifier: str,
        days: int = 3,
        limit: int = 100
    ) -> List[BorrowingRecord]:
        """Get borrowing records due soon for a student by matric number or telegram ID"""
        # 首先尝试通过 telegram_id 查找学生
        student = db.query(Student).filter(Student.telegram_id == identifier).first()
        if student:
            matric_number = student.matric_number
        else:
            # 如果不是 telegram_id，则假设是 matric_number
            matric_number = identifier

        now = datetime.now(timezone.utc)
        soon = now + timedelta(days=days)

        records = db.query(BorrowingRecord).filter(
            BorrowingRecord.matric_number == matric_number,
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date > now,
            BorrowingRecord.due_date <= soon
        ).order_by(BorrowingRecord.due_date).limit(limit).all()

        # Add computed fields
        for record in records:
            self._add_computed_fields(record)

        return records

    def get_overdue_by_student_identifier(
        self,
        db: Session,
        *,
        identifier: str,
        skip: int = 0,
        limit: int = 100,
        due_date_threshold: Optional[datetime] = None
    ) -> List[BorrowingRecord]:
        """Get overdue borrowing records for a student by matric number or telegram ID"""
        # 首先尝试通过 telegram_id 查找学生
        student = db.query(Student).filter(Student.telegram_id == identifier).first()
        if student:
            matric_number = student.matric_number
        else:
            # 如果不是 telegram_id，则假设是 matric_number
            matric_number = identifier

        now = datetime.now(timezone.utc)
        threshold = due_date_threshold or now

        records = db.query(BorrowingRecord).filter(
            BorrowingRecord.matric_number == matric_number,
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date < threshold
        ).order_by(BorrowingRecord.due_date).offset(skip).limit(limit).all()

        # Add computed fields
        for record in records:
            self._add_computed_fields(record)

        return records

    def search(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        borrow_date_start: Optional[str] = None,
        borrow_date_end: Optional[str] = None,
        due_date_start: Optional[str] = None,
        due_date_end: Optional[str] = None,
        return_date_start: Optional[str] = None,
        return_date_end: Optional[str] = None,
        is_overdue: Optional[bool] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None
    ) -> List[BorrowingRecord]:
        """
        搜索借阅记录
        
        Args:
            db: 数据库会话
            query: 通用搜索词
            borrow_date_start: 借阅开始日期
            borrow_date_end: 借阅结束日期
            due_date_start: 应还开始日期
            due_date_end: 应还结束日期
            return_date_start: 归还开始日期
            return_date_end: 归还结束日期
            is_overdue: 是否逾期
            is_active: 是否当前借阅
            limit: 返回结果的最大数量
            offset: 跳过的结果数量
            sort_by: 排序字段
            
        Returns:
            借阅记录列表
        """
        # 构建基础查询
        db_query = db.query(BorrowingRecord)
        
        # 如果提供了通用搜索词
        if query:
            db_query = db_query.join(
                Student, BorrowingRecord.matric_number == Student.matric_number
            ).join(
                BookCopy, BorrowingRecord.copy_id == BookCopy.copy_id
            ).join(
                Book, BookCopy.book_id == Book.book_id
            ).filter(
                or_(
                    Student.name.ilike(f"%{query}%"),
                    Student.matric_number.ilike(f"%{query}%"),
                    Student.email.ilike(f"%{query}%"),
                    Student.telegram_id.ilike(f"%{query}%"),
                    Book.title.ilike(f"%{query}%"),
                    Book.isbn.ilike(f"%{query}%")
                )
            )
        else:
            # 使用特定字段搜索
            if borrow_date_start:
                db_query = db_query.filter(BorrowingRecord.borrow_date >= borrow_date_start)
            if borrow_date_end:
                db_query = db_query.filter(BorrowingRecord.borrow_date <= borrow_date_end)
                
            if due_date_start:
                db_query = db_query.filter(BorrowingRecord.due_date >= due_date_start)
            if due_date_end:
                db_query = db_query.filter(BorrowingRecord.due_date <= due_date_end)
                
            if return_date_start:
                db_query = db_query.filter(BorrowingRecord.return_date >= return_date_start)
            if return_date_end:
                db_query = db_query.filter(BorrowingRecord.return_date <= return_date_end)
                
            if is_overdue is not None:
                now = datetime.now(timezone.utc)
                if is_overdue:
                    db_query = db_query.filter(
                        BorrowingRecord.return_date.is_(None),
                        BorrowingRecord.due_date < now
                    )
                else:
                    db_query = db_query.filter(
                        or_(
                            BorrowingRecord.return_date.isnot(None),
                            BorrowingRecord.due_date >= now
                        )
                    )
                    
            if is_active is not None:
                if is_active:
                    db_query = db_query.filter(BorrowingRecord.return_date.is_(None))
                else:
                    db_query = db_query.filter(BorrowingRecord.return_date.isnot(None))
        
        # 添加排序
        if sort_by:
            if sort_by == "borrow_date":
                db_query = db_query.order_by(BorrowingRecord.borrow_date)
            elif sort_by == "due_date":
                db_query = db_query.order_by(BorrowingRecord.due_date)
            elif sort_by == "return_date":
                db_query = db_query.order_by(BorrowingRecord.return_date)
            elif sort_by == "created_at":
                db_query = db_query.order_by(BorrowingRecord.created_at)
            elif sort_by == "updated_at":
                db_query = db_query.order_by(BorrowingRecord.updated_at)
        
        # 添加分页
        db_query = db_query.offset(offset).limit(limit)
        
        # 获取结果并添加计算字段
        records = db_query.all()
        for record in records:
            self._add_computed_fields(record)
        
        return records


# Instance of CRUD operations
borrowing_crud = CRUDBorrowing(BorrowingRecord)