from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from .. models.borrowing_record import BorrowingRecord as Borrowing 
from ..models.book_copy import BookCopy
from ..models.book import Book
from ..models.student import Student
from ..models.category import Category
from ..schemas.borrowing import BorrowCreate, BorrowUpdate, BorrowStatus
from .base import CRUDBase


class CRUDBorrowing(CRUDBase[Borrowing, BorrowCreate, BorrowUpdate]):
    """Borrowing CRUD operations class"""
    
    def get(self, db: Session, borrow_id: int) -> Optional[Borrowing]:
        """
        Get borrowing by ID
        """
        return db.query(Borrowing).filter(Borrowing.borrow_id == borrow_id).first()
    
    def get_with_details(self, db: Session, borrow_id: int) -> Optional[Borrowing]:
        """
        Get borrowing with all related details
        """
        return db.query(Borrowing).options(
            joinedload(Borrowing.book_copy).joinedload(BookCopy.book),
            joinedload(Borrowing.student)
        ).filter(Borrowing.borrow_id == borrow_id).first()
    
    def get_by_student(
        self, db: Session, *, student_id: int, skip: int = 0, limit: int = 100
    ) -> List[Borrowing]:
        """
        Get all borrowings for a specific student
        """
        return db.query(Borrowing).filter(
            Borrowing.student_id == student_id
        ).order_by(desc(Borrowing.borrow_date)).offset(skip).limit(limit).all()
    
    def get_active_by_student(
        self, db: Session, *, student_id: int, skip: int = 0, limit: int = 100
    ) -> List[Borrowing]:
        """
        Get active borrowings for a specific student
        """
        return db.query(Borrowing).filter(
            Borrowing.student_id == student_id,
            Borrowing.return_date == None
        ).order_by(Borrowing.due_date).offset(skip).limit(limit).all()
    
    def get_current_by_copy(self, db: Session, *, copy_id: int) -> Optional[Borrowing]:
        """
        Get current active borrowing for a book copy
        """
        return db.query(Borrowing).filter(
            Borrowing.copy_id == copy_id,
            Borrowing.return_date == None
        ).first()
    
    def get_history_by_copy(
        self, db: Session, *, copy_id: int, limit: int = 10
    ) -> List[Borrowing]:
        """
        Get borrowing history for a book copy
        """
        return db.query(Borrowing).filter(
            Borrowing.copy_id == copy_id,
            Borrowing.return_date != None
        ).order_by(desc(Borrowing.return_date)).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: BorrowCreate) -> Borrowing:
        """
        Create a new borrowing record
        """
        # Check if copy exists
        copy = db.query(BookCopy).filter(BookCopy.copy_id == obj_in.copy_id).first()
        if not copy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book copy not found"
            )
        
        # Check if copy is available
        if copy.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book copy is not available, current status: {copy.status}"
            )
        
        # Check if student exists
        student = db.query(Student).filter(Student.student_id == obj_in.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check if student has too many books
        active_borrows = self.get_active_by_student(db, student_id=obj_in.student_id)
        if len(active_borrows) >= 3:  # Maximum 3 books per student
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student has reached maximum number of borrowed books"
            )
        
        # Set default borrow_date if not provided
        if not obj_in.borrow_date:
            obj_in.borrow_date = datetime.now()
        
        # Create borrowing record
        obj_data = obj_in.dict()
        db_obj = Borrowing(**obj_data, status=BorrowStatus.BORROWED)
        
        # Update copy status
        copy.status = "borrowed"
        
        db.add(db_obj)
        db.add(copy)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    def return_book(
        self, db: Session, *, borrow_id: int, return_date: Optional[datetime] = None
    ) -> Borrowing:
        """
        Process book return
        """
        borrow = self.get_with_details(db, borrow_id=borrow_id)
        if not borrow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrowing record not found"
            )
        
        if borrow.return_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book has already been returned"
            )
        
        # Set return date
        actual_return_date = return_date or datetime.now()
        
        # Update borrow status
        borrow.return_date = actual_return_date
        borrow.status = BorrowStatus.RETURNED
        
        # Update copy status back to available
        copy = borrow.book_copy
        copy.status = "available"
        
        db.add(borrow)
        db.add(copy)
        db.commit()
        db.refresh(borrow)
        
        return borrow
    
    def extend_borrowing(
        self, db: Session, *, borrow_id: int, days: int, reason: Optional[str] = None
    ) -> Borrowing:
        """
        Extend borrowing due date
        """
        if days <= 0 or days > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Extension days must be between 1 and 30"
            )
        
        borrow = self.get(db, borrow_id=borrow_id)
        if not borrow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrowing record not found"
            )
        
        if borrow.return_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot extend borrowing for already returned book"
            )
        
        # Check if already overdue
        now = datetime.now()
        if borrow.due_date < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot extend overdue borrowing"
            )
        
        # Calculate new due date
        new_due_date = borrow.due_date + timedelta(days=days)
        
        # Update borrowing
        borrow.extension_date = now
        borrow.due_date = new_due_date
        borrow.status = BorrowStatus.EXTENDED
        if reason:
            borrow.notes = reason if not borrow.notes else f"{borrow.notes}\nExtension: {reason}"
        
        db.add(borrow)
        db.commit()
        db.refresh(borrow)
        
        return borrow
    
    def get_student_history(
        self, db: Session, *, student_id: int, limit: int = 50, include_active: bool = True
    ) -> List[Borrowing]:
        """
        Get student's borrowing history with detailed information
        """
        query = db.query(Borrowing).options(
            joinedload(Borrowing.book_copy).joinedload(BookCopy.book),
            joinedload(Borrowing.student)
        ).filter(Borrowing.student_id == student_id)
        
        if not include_active:
            query = query.filter(Borrowing.return_date != None)
        
        return query.order_by(desc(Borrowing.borrow_date)).limit(limit).all()
    
    def get_active_borrowings(
        self, db: Session, *, skip: int = 0, limit: int = 50, 
        overdue_only: bool = False, student_id: Optional[int] = None
    ) -> List[Borrowing]:
        """
        Get active borrowings with optional filtering
        """
        query = db.query(Borrowing).options(
            joinedload(Borrowing.book_copy).joinedload(BookCopy.book),
            joinedload(Borrowing.student)
        ).filter(Borrowing.return_date == None)
        
        # Add filters if specified
        if overdue_only:
            query = query.filter(Borrowing.due_date < datetime.now())
        
        if student_id:
            query = query.filter(Borrowing.student_id == student_id)
        
        return query.order_by(Borrowing.due_date).offset(skip).limit(limit).all()
    
    def count_active_borrowings(
        self, db: Session, *, overdue_only: bool = False, student_id: Optional[int] = None
    ) -> int:
        """
        Count active borrowings with optional filtering
        """
        query = db.query(func.count(Borrowing.borrow_id)).filter(Borrowing.return_date == None)
        
        # Add filters if specified
        if overdue_only:
            query = query.filter(Borrowing.due_date < datetime.now())
        
        if student_id:
            query = query.filter(Borrowing.student_id == student_id)
        
        return query.scalar()
    
    def get_overdue_borrowings(
        self, db: Session, *, due_date_threshold: Optional[datetime] = None, limit: int = 50
    ) -> List[Borrowing]:
        """
        Get overdue borrowings
        """
        now = datetime.now()
        query = db.query(Borrowing).options(
            joinedload(Borrowing.book_copy).joinedload(BookCopy.book),
            joinedload(Borrowing.student)
        ).filter(
            Borrowing.return_date == None,
            Borrowing.due_date < now
        )
        
        if due_date_threshold:
            query = query.filter(Borrowing.due_date > due_date_threshold)
        
        return query.order_by(Borrowing.due_date).limit(limit).all()
    
    def get_statistics(
        self, db: Session, *, start_date: datetime, end_date: datetime, 
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get borrowing statistics for a period
        """
        # Base query for borrowings in the period
        base_query = db.query(Borrowing).filter(
            Borrowing.borrow_date >= start_date,
            Borrowing.borrow_date <= end_date
        )
        
        # Filter by category if specified
        if category_id:
            base_query = base_query.join(
                BookCopy, Borrowing.copy_id == BookCopy.copy_id
            ).join(
                Book, BookCopy.book_id == Book.book_id
            ).filter(
                Book.category_id == category_id
            )
        
        # Total borrowings in period
        total_borrowings = base_query.count()
        
        # Active borrowings (not returned yet)
        active_borrowings = base_query.filter(
            Borrowing.return_date == None
        ).count()
        
        # Overdue borrowings
        overdue_borrowings = base_query.filter(
            Borrowing.return_date == None,
            Borrowing.due_date < datetime.now()
        ).count()
        
        # Average days kept (for returned books)
        avg_days_result = db.query(
            func.avg(func.julianday(Borrowing.return_date) - func.julianday(Borrowing.borrow_date))
        ).filter(
            Borrowing.borrow_date >= start_date,
            Borrowing.borrow_date <= end_date,
            Borrowing.return_date != None
        ).scalar()
        
        average_days_kept = float(avg_days_result) if avg_days_result else 0.0
        
        # Most borrowed books (top 5)
        most_borrowed_books = db.query(
            Book.book_id,
            Book.title,
            func.count(Borrowing.borrow_id).label('borrow_count')
        ).join(
            BookCopy, Book.book_id == BookCopy.book_id
        ).join(
            Borrowing, BookCopy.copy_id == Borrowing.copy_id
        ).filter(
            Borrowing.borrow_date >= start_date,
            Borrowing.borrow_date <= end_date
        ).group_by(
            Book.book_id
        ).order_by(
            desc('borrow_count')
        ).limit(5).all()
        
        # Most active students (top 5)
        most_active_students = db.query(
            Student.student_id,
            Student.name,
            func.count(Borrowing.borrow_id).label('borrow_count')
        ).join(
            Borrowing, Student.student_id == Borrowing.student_id
        ).filter(
            Borrowing.borrow_date >= start_date,
            Borrowing.borrow_date <= end_date
        ).group_by(
            Student.student_id
        ).order_by(
            desc('borrow_count')
        ).limit(5).all()
        
        # Borrowings by category
        borrowings_by_category = db.query(
            Category.category_id,
            Category.name,
            func.count(Borrowing.borrow_id).label('borrow_count')
        ).join(
            Book, Category.category_id == Book.category_id
        ).join(
            BookCopy, Book.book_id == BookCopy.book_id
        ).join(
            Borrowing, BookCopy.copy_id == Borrowing.copy_id
        ).filter(
            Borrowing.borrow_date >= start_date,
            Borrowing.borrow_date <= end_date
        ).group_by(
            Category.category_id
        ).order_by(
            desc('borrow_count')
        ).all()
        
        # Borrowings by month
        borrowings_by_month = db.query(
            func.strftime('%Y-%m', Borrowing.borrow_date).label('month'),
            func.count(Borrowing.borrow_id).label('borrow_count')
        ).filter(
            Borrowing.borrow_date >= start_date,
            Borrowing.borrow_date <= end_date
        ).group_by(
            'month'
        ).order_by(
            'month'
        ).all()
        
        # Prepare results
        return {
            "total_borrowings": total_borrowings,
            "active_borrowings": active_borrowings,
            "overdue_borrowings": overdue_borrowings,
            "average_days_kept": average_days_kept,
            "most_borrowed_books": [
                {
                    "book_id": book.book_id,
                    "title": book.title,
                    "borrow_count": book.borrow_count
                }
                for book in most_borrowed_books
            ],
            "most_active_students": [
                {
                    "student_id": student.student_id,
                    "name": student.name,
                    "borrow_count": student.borrow_count
                }
                for student in most_active_students
            ],
            "borrowings_by_category": [
                {
                    "category_id": category.category_id,
                    "name": category.name,
                    "borrow_count": category.borrow_count
                }
                for category in borrowings_by_category
            ],
            "borrowings_by_month": [
                {
                    "month": month.month,
                    "borrow_count": month.borrow_count
                }
                for month in borrowings_by_month
            ]
        }


# Create borrowing CRUD operations instance
borrowing_crud = CRUDBorrowing(Borrowing)