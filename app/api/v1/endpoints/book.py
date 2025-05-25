from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func, or_
import logging
from app.db.session import get_db
from app.crud.book import book_crud
from app.models.book import Book
from app.schemas.book import (
    BookCreate,
    BookResponse,
    BookDetail,
    BookUpdate,
    BookAvailabilityResponse
)
from fastapi import Path

router = APIRouter()

#Done
@router.get("/", response_model=List[BookResponse])
def get_books(
    limit: Optional[int] = Query(20, gt=0, description="Maximum number of books to return"),
    title: Optional[str] = Query(None, description="Filter by book title"),
    author_name: Optional[str] = Query(None, description="Filter by author name"),
    publisher_name: Optional[str] = Query(None, description="Filter by publisher name"),
    category_name: Optional[str] = Query(None, description="Filter by category name"),
    language_name: Optional[str] = Query(None, description="Filter by language"),
    db: Session = Depends(get_db)
):
    """
    Retrieve books with optional filters.
    """
    try:
        books = book_crud.search_books(
            db=db,
            title=title,
            author_name=author_name,
            publisher_name=publisher_name,
            category_name=category_name,
            language_name=language_name,
            limit=limit,
            exact_match=False
        )
        logging.info("Books retrieved successfully")
        return books
    except Exception as e:
        error_message = f"Error retrieving books: {str(e)}"
        logging.error(error_message, exc_info=True)

        # Return detailed error in development environment
        import traceback
        error_details = traceback.format_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to retrieve books",
                "error": str(e),
                "traceback": error_details.split('\n')  # Split stack trace into lines
            }
        )
# done
@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    *,
    db: Session = Depends(get_db),
    book_in: BookCreate,
):
    # Create book record
    new_book = book_crud.create(db=db, obj_in=book_in)

    # If initial copy count is specified, create the corresponding number of copies
    if book_in.initial_copies > 0:
        from app.crud import book_copy as book_copy_crud
        from app.schemas.book_copy import BookCopyCreate

        for i in range(book_in.initial_copies):
            # Create copy
            book_copy_crud.create(
                db=db,
                obj_in=BookCopyCreate(
                    book_id=new_book.book_id,
                    acquisition_type="purchased",
                    acquisition_date=datetime.now().date(),
                    status="available",
                    condition="new"
                )
            )

    return new_book
# done
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
# done
@router.get("/search/isbn/{isbn}", response_model=BookDetail)
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
    # Make sure we get a fully populated BookDetail object
    return book_crud.get_with_details(db, book_id=db_book.book_id)

@router.get("/search/call-number/{call_number}", response_model=BookDetail)
def get_book_by_call_number(
    *,
    db: Session = Depends(get_db),
    call_number: str,
):
    """
    Get a book by call number.

    - **call_number**: Call number
    """
    db_book = book_crud.get_by_call_number(db, call_number=call_number)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    # Make sure we get a fully populated BookDetail object
    return book_crud.get_with_details(db, book_id=db_book.book_id)
#done
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
#done
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

@router.patch("/{book_id}", response_model=BookResponse)
def partial_update_book(
    *,
    db: Session = Depends(get_db),
    book_id: int = Path(..., title="Book ID", description="ID of the book to update"),
    book_in: BookUpdate,
):
    """
    Partially update a book's information.

    - **book_id**: Book ID
    - **book_in**: Updated book data (only include fields that need to be updated)
    """
    db_book = book_crud.get(db, book_id=book_id)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    # Filter out None values to only update provided fields
    update_data = {k: v for k, v in book_in.model_dump(exclude_unset=True).items() if v is not None}

    updated_book = book_crud.update(db=db, db_obj=db_book, obj_in=update_data)
    return updated_book

