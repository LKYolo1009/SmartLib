from typing import List, Optional, Dict, Any, Union, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid

from ..models.book_copy import BookCopy
from ..models.book import Book
from ..schemas.book_copy import BookCopyCreate, BookCopyUpdate, BookCopyStatusUpdate
from .base import CRUDBase


class CRUDBookCopy(CRUDBase[BookCopy, BookCopyCreate, BookCopyUpdate]):
    """Book copy CRUD operations class"""

    def get(self, db: Session, copy_id: int) -> Optional[BookCopy]:
        """
        Get book copy by ID
        """
        return db.query(BookCopy).filter(BookCopy.copy_id == copy_id).first()

    def get_with_book(self, db: Session, copy_id: int) -> Optional[BookCopy]:
        """
        Get book copy with associated book information
        """
        copy = db.query(BookCopy).options(
            joinedload(BookCopy.book)
        ).filter(BookCopy.copy_id == copy_id).first()

        if copy:
            # Add book title for easier access
            if copy.book:
                setattr(copy, "book_title", copy.book.title)

            # Ensure qr_code is a string
            if copy.qr_code is not None:
                copy.qr_code = str(copy.qr_code)

        return copy

    def get_by_identifier(self, db: Session, identifier_type: str, value: str) -> Optional[BookCopy]:
        """
        Get book copy by various identifiers (call number, QR code, etc.)
        """
        if not hasattr(BookCopy, identifier_type):
            raise ValueError(f"Invalid identifier type: {identifier_type}")

        return db.query(BookCopy).filter(
            getattr(BookCopy, identifier_type) == value
        ).first()

    # get_by_call_number method removed as call_number is now a field in the Book model

    def get_by_qr_code(self, db: Session, qr_code: str) -> Optional[BookCopy]:
        """
        Get book copy by QR code
        """
        try:
            # Try to convert qr_code to UUID before querying
            uuid_obj = uuid.UUID(qr_code)
            copy = db.query(BookCopy).filter(BookCopy.qr_code == uuid_obj).first()

            # Ensure qr_code is converted to string for response
            if copy and copy.qr_code is not None:
                copy.qr_code = str(copy.qr_code)

                # Add book title if available
                if copy.book:
                    setattr(copy, "book_title", copy.book.title)

            return copy
        except ValueError:
            # If not a valid UUID format, return None
            return None

    def get_by_book(
        self, db: Session, *, book_id: int, skip: int = 0, limit: int = 100
    ) -> List[BookCopy]:
        """
        Get all copies of a specific book
        """
        return db.query(BookCopy).filter(
            BookCopy.book_id == book_id
        ).offset(skip).limit(limit).all()

    def get_copies_by_title_and_status(
        self,
        db: Session,
        *,
        book_title: Optional[str] = None,
        status: Optional[str] = None,
        condition: Optional[str] = None,
        limit: int = 20
    ) -> List[BookCopy]:
        """
        Get book copies filtered by book title and status
        """
        query = db.query(BookCopy).options(joinedload(BookCopy.book))

        # Apply filters
        if book_title:
            query = query.join(Book).filter(Book.title.ilike(f"%{book_title}%"))

        filters = []
        if status:
            filters.append(BookCopy.status == status)
        if condition:
            filters.append(BookCopy.condition == condition)

        if filters:
            query = query.filter(and_(*filters))

        copies = query.limit(limit).all()

        # Add book title for easier access and convert UUID to string
        for copy in copies:
            if copy.book:
                setattr(copy, "book_title", copy.book.title)

            # Ensure qr_code is a string
            if copy.qr_code is not None:
                copy.qr_code = str(copy.qr_code)

        return copies

    def get_available_by_book(
        self, db: Session, *, book_id: int, skip: int = 0, limit: int = 100
    ) -> List[BookCopy]:
        """
        Get all available copies of a specific book
        """
        return db.query(BookCopy).filter(
            BookCopy.book_id == book_id,
            BookCopy.status == "available"
        ).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: BookCopyCreate) -> BookCopy:
        obj_data = obj_in.model_dump(exclude={"qr_code"})
        db_obj = BookCopy(**obj_data)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        if hasattr(db_obj, 'book') and db_obj.book:
            setattr(db_obj, "book_title", db_obj.book.title)

        return db_obj
    def update_status(
        self, db: Session, *, copy_id: int, status_update: BookCopyStatusUpdate
    ) -> BookCopy:
        """
        Update book copy status with additional information
        """
        db_obj = self.get(db, copy_id=copy_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book copy not found"
            )

        update_data = {"status": status_update.status}

        # Add notes if provided
        if status_update.notes:
            update_data["notes"] = status_update.notes if not db_obj.notes else f"{db_obj.notes}\n[{datetime.now().strftime('%Y-%m-%d')}] {status_update.status}: {status_update.notes}"

        # Update condition if provided
        if status_update.condition:
            update_data["condition"] = status_update.condition

        updated_copy = super().update(db, db_obj=db_obj, obj_in=update_data)

        # Add book title if available
        if hasattr(updated_copy, 'book') and updated_copy.book:
            setattr(updated_copy, "book_title", updated_copy.book.title)

        return updated_copy

    def get_status_counts_by_book(
        self, db: Session, book_id: int
    ) -> Dict[str, int]:
        """
        Get counts of copies by status for a specific book
        """
        query = db.query(
            BookCopy.status,
            func.count(BookCopy.copy_id).label('count')
        ).filter(
            BookCopy.book_id == book_id
        ).group_by(BookCopy.status)

        result = {row.status: row.count for row in query.all()}

        # Ensure all statuses have a count
        for status in ["available", "borrowed", "processing", "missing", "damaged", "unpublished"]:
            if status not in result:
                result[status] = 0

        return result

    def bulk_update_status(
        self, db: Session, *, copy_ids: List[int], status: str, notes: Optional[str] = None
    ) -> Tuple[int, List[int]]:
        """
        Update status for multiple book copies at once
        """
        successful_updates = 0
        failed_updates = []

        for copy_id in copy_ids:
            try:
                self.update_status(
                    db,
                    copy_id=copy_id,
                    status_update=BookCopyStatusUpdate(
                        status=status,
                        notes=notes
                    )
                )
                successful_updates += 1
            except HTTPException:
                failed_updates.append(copy_id)

        return successful_updates, failed_updates

    def get_copies_with_book_details(
        self, db: Session, *, filters: Dict[str, Any] = None, skip: int = 0, limit: int = 100
    ) -> List[BookCopy]:
        """
        Get book copies with their associated book details, with optional filtering
        """
        query = db.query(BookCopy).options(joinedload(BookCopy.book))

        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(BookCopy, key):
                    filter_conditions.append(getattr(BookCopy, key) == value)

            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        copies = query.offset(skip).limit(limit).all()

        # Add book title for easier access and convert UUID to string
        for copy in copies:
            if copy.book:
                setattr(copy, "book_title", copy.book.title)

            # Ensure qr_code is a string
            if copy.qr_code is not None:
                copy.qr_code = str(copy.qr_code)

        return copies


# Create book copy CRUD operations instance
book_copy_crud = CRUDBookCopy(BookCopy)