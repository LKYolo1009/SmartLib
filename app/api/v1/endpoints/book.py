from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import book as book_crud
from app.schemas.book import BookCreate, BookResponse, BookDetail, BookUpdate

router = APIRouter()

@router.get("/", response_model=List[BookResponse])
def get_books(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    title: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[str] = None,
):
    """
    Retrieve a list of books with optional filtering.
    """
    if title:
        return book_crud.search_by_title(db, title=title, skip=skip, limit=limit)
    if author:
        return book_crud.search_by_author(db, author=author, skip=skip, limit=limit)
    if category:
        return book_crud.search_by_category(db, category=category, skip=skip, limit=limit)
    return book_crud.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    *,
    db: Session = Depends(get_db),
    book_in: BookCreate,
):
    """
    Create a new book metadata entry.
    """
    return book_crud.create(db=db, obj_in=book_in)

@router.get("/{book_id}", response_model=BookDetail)
def get_book(
    *,
    db: Session = Depends(get_db),
    book_id: int,
):
    """
    Retrieve detailed information about a book.
    """
    db_book = book_crud.get(db, id=book_id)
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
    """
    db_book = book_crud.get(db, id=book_id)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return book_crud.update(db=db, db_obj=db_book, obj_in=book_in)

@router.get("/isbn/{isbn}", response_model=BookDetail)
def get_book_by_isbn(
    *,
    db: Session = Depends(get_db),
    isbn: str,
):
    """
    Retrieve a book by its ISBN.
    """
    db_book = book_crud.get_by_isbn(db, isbn=isbn)
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    return db_book

@router.get("/search/", response_model=List[BookResponse])
def search_books(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = 0,
    limit: int = 100,
):
    """
    Search for books by title, author, or ISBN.
    """
    return book_crud.search(db, query=q, skip=skip, limit=limit)