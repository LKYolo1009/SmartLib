from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import book as book_crud
from app.schemas.book import BookResponse, BookDetail

router = APIRouter()
@router.get("/search", response_model=List[BookResponse])
def search_books(
    db: Session = Depends(get_db),
    title: Optional[str] = None,
    author: Optional[str] = None,
    publisher: Optional[str] = None,
    category: Optional[str] = None,
    isbn: Optional[str] = None,
    year: Optional[int] = None,
    language: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    exact_match: bool = False
):
    """
    Unified search endpoint for books
    """
    return book_crud.search_books(
        db,
        title=title,
        author_name=author,
        publisher_name=publisher,
        category_name=category,
        isbn=isbn,
        publication_year=year,
        language_name=language,
        limit=limit,
        exact_match=exact_match
    )

@router.get("/search/{query}", response_model=List[BookResponse])
def general_search(
    query: str,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """
    General purpose search with a single query parameter
    """
    return book_crud.general_search(db, query=query, limit=limit)