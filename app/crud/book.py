from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from fastapi import HTTPException, status

from ..models.book import Book
from ..models.author import Author
from ..models.publisher import Publisher
from ..models.category import Category
from ..models.language import Language
from ..schemas.book import BookCreate, BookUpdate
from .base import CRUDBase
from app.schemas.borrowing import BorrowResponse, BorrowDetail
from ..models.student import Student
from ..models.book_copy import BookCopy
from ..models.borrowing_record import BorrowingRecord

class CRUDBook(CRUDBase[Book, BookCreate, BookUpdate]):
    """Book CRUD operations class"""

    def get(self, db: Session, book_id: int) -> Optional[Book]:
        """
        Get book by ID
        """
        return db.query(Book).filter(Book.book_id == book_id).first()

    def get_by_isbn(self, db: Session, isbn: str) -> Optional[Book]:
        """
        Get book by ISBN
        """
        return db.query(Book).filter(Book.isbn == isbn).first()

    def get_by_call_number(self, db: Session, call_number: str) -> Optional[Book]:
        """
        Get book by call number
        """
        return db.query(Book).filter(Book.call_number == call_number).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        """
        Get multiple books with pagination
        """
        return db.query(Book).offset(skip).limit(limit).all()

    def get_with_details(self, db: Session, book_id: int) -> Optional[Book]:
        """
        Get book with all related details (author, publisher, etc.)
        """
        book = db.query(Book).options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.language),
            joinedload(Book.category),
            joinedload(Book.copies)
        ).filter(Book.book_id == book_id).first()

        if book:
            # Add calculated fields
            available_copies = sum(1 for copy in book.copies if copy.status == "available")
            setattr(book, "available_copies", available_copies)
            setattr(book, "total_copies", len(book.copies))

            # Add required fields for BookDetail schema
            setattr(book, "author_name", book.author.author_name if book.author else None)
            setattr(book, "publisher_name", book.publisher.publisher_name if book.publisher else None)
            setattr(book, "language_name", book.language.language_name if book.language else None)
            setattr(book, "category_name", book.category.category_name if book.category else None)

        return book

    def search_by_title(self, db: Session, *, title: str, limit: int = 20) -> List[Book]:
        """
        Search books by title (partial match)
        """
        search_query = f"%{title}%"
        return db.query(Book).options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.language),
            joinedload(Book.category),
            joinedload(Book.copies)
        ).filter(
            Book.title.ilike(search_query)
        ).limit(limit).all()

    def search_by_exact_title(self, db: Session, *, title: str, limit: int = 20) -> List[Book]:
        """
        Search books by exact title
        """
        return db.query(Book).options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.language),
            joinedload(Book.category),
            joinedload(Book.copies)
        ).filter(
            func.lower(Book.title) == func.lower(title)
        ).limit(limit).all()

    def search_by_author_name(self, db: Session, *, author_name: str, limit: int = 20) -> List[Book]:
        """
        Search books by author name
        """
        search_query = f"%{author_name}%"
        return db.query(Book).options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.language),
            joinedload(Book.category),
            joinedload(Book.copies)
        ).join(Book.author).filter(
            Author.author_name.ilike(search_query)
        ).limit(limit).all()

    def search_by_publisher_name(self, db: Session, *, publisher_name: str, limit: int = 20) -> List[Book]:
        """
        Search books by publisher name
        """
        search_query = f"%{publisher_name}%"
        return db.query(Book).options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.language),
            joinedload(Book.category),
            joinedload(Book.copies)
        ).join(Book.publisher).filter(
            Publisher.publisher_name.ilike(search_query)
        ).limit(limit).all()

    def search_by_category_name(self, db: Session, *, category_name: str, limit: int = 20) -> List[Book]:
        """
        Search books by category name
        """
        search_query = f"%{category_name}%"
        return db.query(Book).options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.language),
            joinedload(Book.category),
            joinedload(Book.copies)
        ).join(Book.category).filter(
            Category.category_name.ilike(search_query)
        ).limit(limit).all()

    def search_by_names(
        self,
        db: Session,
        *,
        title: Optional[str] = None,
        author_name: Optional[str] = None,
        publisher_name: Optional[str] = None,
        category_name: Optional[str] = None,
        language_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Book]:
        """
        Search books by various name fields
        """
        query = db.query(Book)

        # Build joins for each related entity only if needed
        if author_name:
            query = query.join(Book.author)
        if publisher_name:
            query = query.join(Book.publisher, isouter=True)  # Use outer join for optional relationships
        if category_name:
            query = query.join(Book.category)
        if language_name:
            query = query.join(Book.language, isouter=True)  # Use outer join for optional relationships

        # Build filter conditions
        filters = []
        if title:
            filters.append(Book.title.ilike(f"%{title}%"))
        if author_name:
            filters.append(Author.author_name.ilike(f"%{author_name}%"))
        if publisher_name:
            filters.append(Publisher.publisher_name.ilike(f"%{publisher_name}%"))
        if category_name:
            filters.append(Category.name.ilike(f"%{category_name}%"))
        if language_name:
            filters.append(Language.name.ilike(f"%{language_name}%"))

        # Apply filters if any
        if filters:
            query = query.filter(or_(*filters))

        return query.limit(limit).all()

    def create(self, db: Session, *, obj_in: BookCreate) -> Book:
        """
        Create a new book
        """
        try:
            # Check if ISBN already exists (only if ISBN is provided)
            if obj_in.isbn:
                existing_book = self.get_by_isbn(db, isbn=obj_in.isbn)
                if existing_book:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="this ISBN already exists"
                    )

            # Convert Pydantic model to dict and create DB object
            obj_data = obj_in.model_dump(exclude={"initial_copies"})
            db_obj = Book(**obj_data)

            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except Exception as e:
            db.rollback()  # Rollback the transaction
            raise

    def update(
        self,
        db: Session,
        *,
        db_obj: Book,
        obj_in: Union[BookUpdate, Dict[str, Any]]
    ) -> Book:
        """
        Update book information
        Supports both full BookUpdate object and partial dictionary updates
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Check if ISBN is being updated and if it already exists
        if "isbn" in update_data and update_data["isbn"] != db_obj.isbn:
            existing_book = self.get_by_isbn(db, isbn=update_data["isbn"])
            if existing_book and existing_book.book_id != db_obj.book_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="this book already exists"
                )

        # Update the db object with new values
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def check_availability(self, db: Session, book_id: int) -> Dict[str, Any]:
        """
        Check if a book is available for borrowing
        """
        book = self.get_with_details(db, book_id=book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )

        # Get all available copies
        available_copies = [copy for copy in book.copies if copy.status == "available"]

        return {
            "book_id": book.book_id,
            "title": book.title,
            "isbn": book.isbn,
            "total_copies": len(book.copies),
            "available_copies": len(available_copies),
            "is_available": len(available_copies) > 0,
            "available_copy_ids": [copy.copy_id for copy in available_copies]
        }

    def search_books(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        title: Optional[str] = None,
        author_name: Optional[str] = None,
        publisher_name: Optional[str] = None,
        category_name: Optional[str] = None,
        isbn: Optional[str] = None,
        publication_year: Optional[int] = None,
        language_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        exact_match: bool = False
    ) -> List[Book]:
        """
        Search books
        
        Args:
            db: Database session
            query: General search term
            title: Book title
            author_name: Author name
            publisher_name: Publisher name
            category_name: Category name
            isbn: ISBN
            publication_year: Publication year
            language_name: Language
            status: Status
            limit: Maximum number of records to return
            offset: Number of records to skip
            sort_by: Sort field
            exact_match: Whether to match exactly
            
        Returns:
            List of books
        """
        # Build base query
        db_query = db.query(Book)
        
        # If a general search term is provided
        if query:
            search_term = f"%{query}%" if not exact_match else query
            db_query = db_query.join(
                Author, Book.author_id == Author.author_id
            ).join(
                Publisher, Book.publisher_id == Publisher.publisher_id
            ).join(
                Category, Book.category_id == Category.category_id
            ).join(
                Language, Book.language_id == Language.language_id
            ).filter(
                or_(
                    Book.title.ilike(search_term),
                    Book.isbn.ilike(search_term),
                    Author.name.ilike(search_term),
                    Publisher.name.ilike(search_term),
                    Category.name.ilike(search_term),
                    Language.name.ilike(search_term)
                )
            )
        else:
            # Use specific fields for search
            if title:
                search_term = f"%{title}%" if not exact_match else title
                db_query = db_query.filter(Book.title.ilike(search_term))
                
            if author_name:
                search_term = f"%{author_name}%" if not exact_match else author_name
                db_query = db_query.join(Author).filter(Author.name.ilike(search_term))
                
            if publisher_name:
                search_term = f"%{publisher_name}%" if not exact_match else publisher_name
                db_query = db_query.join(Publisher).filter(Publisher.name.ilike(search_term))
                
            if category_name:
                search_term = f"%{category_name}%" if not exact_match else category_name
                db_query = db_query.join(Category).filter(Category.name.ilike(search_term))
                
            if isbn:
                search_term = f"%{isbn}%" if not exact_match else isbn
                db_query = db_query.filter(Book.isbn.ilike(search_term))
                
            if publication_year:
                db_query = db_query.filter(Book.publication_year == publication_year)
                
            if language_name:
                search_term = f"%{language_name}%" if not exact_match else language_name
                db_query = db_query.join(Language).filter(Language.name.ilike(search_term))
                
            if status:
                if status == "available":
                    db_query = db_query.filter(Book.available_copies > 0)
                elif status == "unavailable":
                    db_query = db_query.filter(Book.available_copies == 0)
        
        # Add sorting
        if sort_by:
            if sort_by == "title":
                db_query = db_query.order_by(Book.title)
            elif sort_by == "author":
                db_query = db_query.join(Author).order_by(Author.name)
            elif sort_by == "publisher":
                db_query = db_query.join(Publisher).order_by(Publisher.name)
            elif sort_by == "category":
                db_query = db_query.join(Category).order_by(Category.name)
            elif sort_by == "publication_year":
                db_query = db_query.order_by(Book.publication_year)
            elif sort_by == "created_at":
                db_query = db_query.order_by(Book.created_at)
            elif sort_by == "updated_at":
                db_query = db_query.order_by(Book.updated_at)
        
        # Add pagination
        db_query = db_query.offset(offset).limit(limit)
        
        return db_query.all()

    def general_search(
        self,
        db: Session,
        *,
        query: str,
        limit: int = 20
    ) -> List[Book]:
        """
        General purpose search that looks across multiple fields
        """
        search_pattern = f"%{query}%"

        db_query = db.query(Book).outerjoin(Book.author).outerjoin(
            Book.publisher
        ).outerjoin(Book.category).filter(
            or_(
                Book.title.ilike(search_pattern),
                Book.isbn.ilike(search_pattern),
                Author.author_name.ilike(search_pattern),
                Publisher.publisher_name.ilike(search_pattern),
                Category.category_name.ilike(search_pattern)
            )
        ).limit(limit)

        return db_query.all()


# Create book CRUD operations instance
book_crud = CRUDBook(Book)