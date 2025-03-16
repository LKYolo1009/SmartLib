from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.crud import book as book_crud
from app.schemas.book import (
    BookCreate, 
    BookResponse, 
    BookDetail, 
    BookUpdate,
    BookAvailabilityResponse
)

router = APIRouter()

@router.get("/", response_model=List[BookResponse])
def get_books(
    db: Session = Depends(get_db),
    limit: int = 20,
    title: Optional[str] = None,
    author_name: Optional[str] = None,
    publisher_name: Optional[str] = None,
    category_name: Optional[str] = None,
    language_name: Optional[str] = None,
):
    """
    
    - **limit**: Maximum number of records to return
    - **title**: Filter by book title (partial match)
    - **author_name**: Filter by author name
    - **publisher_name**: Filter by publisher name
    - **category_name**: Filter by category name
    - **language_name**: Filter by language name
    """
    return book_crud.search_by_names(
        db, 
        title=title,
        author_name=author_name,
        publisher_name=publisher_name,
        category_name=category_name,
        language_name=language_name,
        limit=limit
    )

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    *,
    db: Session = Depends(get_db),
    book_in: BookCreate,
):
    """
    Create a new book and optionally create initial copies.
    
    - **book_in**: Book creation data, including optional initial copy count
    """
    # Create book record
    new_book = book_crud.create(db=db, obj_in=book_in)
    
    # If initial copy count is specified, create the corresponding number of copies
    if book_in.initial_copies > 0:
        from app.crud import book_copy as book_copy_crud
        from app.schemas.book_copy import BookCopyCreate
        
        for i in range(book_in.initial_copies):
            # Generate call number for each copy
            call_number = f"{new_book.category.code if hasattr(new_book, 'category') else 'GEN'}-{new_book.book_id}-{i+1}"
            
            # Create copy
            book_copy_crud.create(
                db=db,
                obj_in=BookCopyCreate(
                    book_id=new_book.book_id,
                    call_number=call_number,
                    acquisition_type="purchased",
                    acquisition_date=datetime.now().date(),
                    status="available",
                    condition="new"
                )
            )
    
    return new_book

@router.get("/{book_id}", response_model=BookDetail)
def get_book(
    *,
    db: Session = Depends(get_db),
    book_id: int,
):
    """
    Get book details.
    
    - **book_id**: Book ID
    """
    db_book = book_crud.get_with_details(db, book_id=book_id)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return db_book

@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    *,
    db: Session = Depends(get_db),
    book_id: int,
    book_in: BookUpdate,
):
    """
    Update book information.
    
    - **book_id**: Book ID
    - **book_in**: Updated book data
    """
    db_book = book_crud.get(db, book_id=book_id)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book_crud.update(db=db, db_obj=db_book, obj_in=book_in)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    *,
    db: Session = Depends(get_db),
    book_id: int,
):
    """
    Delete a book (only if it has no copies).
    
    - **book_id**: Book ID
    """
    db_book = book_crud.get_with_details(db, book_id=book_id)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Check if there are any copies
    if db_book.copies and len(db_book.copies) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a book with copies. Please delete all copies first."
        )
    
    book_crud.remove(db=db, id=book_id)
    return None

@router.get("/isbn/{isbn}", response_model=BookDetail)
def get_book_by_isbn(
    *,
    db: Session = Depends(get_db),
    isbn: str,
):
    """
    Get a book by ISBN.
    
    - **isbn**: ISBN number
    """
    db_book = book_crud.get_by_isbn(db, isbn=isbn)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book_crud.get_with_details(db, book_id=db_book.book_id)

@router.get("/search/title/{title}", response_model=List[BookResponse])
def search_books_by_title(
    *,
    db: Session = Depends(get_db),
    title: str,
    exact_match: bool = False,
    limit: int = 20,
):
    """
    Search books by title.
    Supports exact match or fuzzy search.
    
    - **title**: Book title
    - **exact_match**: Whether to match exactly
    - **limit**: Maximum number of records to return
    """
    if exact_match:
        return book_crud.search_by_exact_title(db, title=title, limit=limit)
    else:
        return book_crud.search_by_title(db, title=title, limit=limit)

@router.get("/search/author/{author_name}", response_model=List[BookResponse])
def search_books_by_author(
    *,
    db: Session = Depends(get_db),
    author_name: str,
    limit: int = 20,
):
    """
    Search books by author name.
    
    - **author_name**: Author name
    - **limit**: Maximum number of records to return
    """
    return book_crud.search_by_author_name(db, author_name=author_name, limit=limit)

@router.get("/search/publisher/{publisher_name}", response_model=List[BookResponse])
def search_books_by_publisher(
    *,
    db: Session = Depends(get_db),
    publisher_name: str,
    limit: int = 20,
):
    """
    Search books by publisher name.
    
    - **publisher_name**: Publisher name
    - **limit**: Maximum number of records to return
    """
    return book_crud.search_by_publisher_name(db, publisher_name=publisher_name, limit=limit)

@router.get("/search/category/{category_name}", response_model=List[BookResponse])
def search_books_by_category(
    *,
    db: Session = Depends(get_db),
    category_name: str,
    limit: int = 20,
):
    """
    Search books by category name.
    
    - **category_name**: Category name
    - **limit**: Maximum number of records to return
    """
    return book_crud.search_by_category_name(db, category_name=category_name, limit=limit)

@router.get("/title/{title}/availability", response_model=List[BookAvailabilityResponse])
def check_book_availability_by_title(
    *,
    db: Session = Depends(get_db),
    title: str,
    exact_match: bool = False,
    limit: int = 5,
):
    """
    Check book availability by title.
    Returns the availability status of books that match the criteria.
    
    - **title**: Book title
    - **exact_match**: Whether to match exactly
    - **limit**: Maximum number of records to return
    """
    books = []
    if exact_match:
        books = book_crud.search_by_exact_title(db, title=title, limit=limit)
    else:
        books = book_crud.search_by_title(db, title=title, limit=limit)
    
    results = []
    for book in books:
        availability = book_crud.check_availability(db, book_id=book.book_id)
        results.append(availability)
    
    return results