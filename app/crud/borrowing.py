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
            now = datetime.now(timezone.utc)
            new_due_date = borrow.due_date + timedelta(days=days)

            # Update borrowing record
            borrow.extension_date = now
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

    def get_borrowing_stats(
        self,
        db: Session,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get borrowing statistics"""
        now = datetime.now(timezone.utc)

        # Default to last 30 days if dates not provided
        if not start_date:
            start_date = now - timedelta(days=30)
        if not end_date:
            end_date = now

        # Base query with optional category filter
        base_query = db.query(BorrowingRecord)
        if category_id:
            base_query = base_query.join(
                BookCopy, BorrowingRecord.copy_id == BookCopy.copy_id
            ).join(
                Book, BookCopy.book_id == Book.book_id
            ).filter(
                Book.category_id == category_id
            )

        # Total borrowings in period
        total_borrowings = base_query.filter(
            BorrowingRecord.borrow_date >= start_date,
            BorrowingRecord.borrow_date <= end_date
        ).count()

        # Active borrowings
        active_borrowings = base_query.filter(
            BorrowingRecord.return_date.is_(None)
        ).count()

        # Overdue borrowings
        overdue_borrowings = base_query.filter(
            BorrowingRecord.return_date.is_(None),
            BorrowingRecord.due_date < now
        ).count()

        # Average days kept (for returned books)
        avg_days_query = db.query(
            func.avg(
                func.julianday(BorrowingRecord.return_date) -
                func.julianday(BorrowingRecord.borrow_date)
            )
        ).select_from(
            base_query.subquery()
        ).filter(
            BorrowingRecord.return_date.isnot(None),
            BorrowingRecord.borrow_date >= start_date,
            BorrowingRecord.borrow_date <= end_date
        )
        avg_days_kept = avg_days_query.scalar() or 0

        # Most borrowed books
        most_borrowed_query = db.query(
            Book.book_id,
            Book.title,
            func.count(BorrowingRecord.borrow_id).label('borrow_count')
        ).join(
            BookCopy, Book.book_id == BookCopy.book_id
        ).join(
            BorrowingRecord, BookCopy.copy_id == BorrowingRecord.copy_id
        ).filter(
            BorrowingRecord.borrow_date >= start_date,
            BorrowingRecord.borrow_date <= end_date
        )

        if category_id:
            most_borrowed_query = most_borrowed_query.filter(Book.category_id == category_id)

        most_borrowed_books = most_borrowed_query.group_by(
            Book.book_id
        ).order_by(
            desc('borrow_count')
        ).limit(10).all()

        # Most active students
        most_active_students = db.query(
            Student.matric_number,
            Student.full_name,
            func.count(BorrowingRecord.borrow_id).label('borrow_count')
        ).join(
            BorrowingRecord, Student.matric_number == BorrowingRecord.matric_number
        ).filter(
            BorrowingRecord.borrow_date >= start_date,
            BorrowingRecord.borrow_date <= end_date
        ).group_by(
            Student.matric_number
        ).order_by(
            desc('borrow_count')
        ).limit(10).all()

        # Borrowings by month
        borrowings_by_month = db.query(
            func.strftime('%Y-%m', BorrowingRecord.borrow_date).label('month'),
            func.count().label('count')
        ).filter(
            BorrowingRecord.borrow_date >= start_date,
            BorrowingRecord.borrow_date <= end_date
        ).group_by('month').order_by('month').all()

        return {
            "total_borrowings": total_borrowings,
            "active_borrowings": active_borrowings,
            "overdue_borrowings": overdue_borrowings,
            "average_days_kept": round(float(avg_days_kept), 1),
            "most_borrowed_books": [
                {
                    "book_id": book.book_id,
                    "title": book.title,
                    "borrow_count": book.borrow_count
                } for book in most_borrowed_books
            ],
            "most_active_students": [
                {
                    "matric_number": student.matric_number,
                    "name": student.full_name,
                    "borrow_count": student.borrow_count
                } for student in most_active_students
            ],
            "borrowings_by_month": [
                {
                    "month": month.month,
                    "count": month.count
                } for month in borrowings_by_month
            ]
        }

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


# Instance of CRUD operations
borrowing_crud = CRUDBorrowing(BorrowingRecord)