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
    query: Optional[str] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    publisher: Optional[str] = None,
    category: Optional[str] = None,
    isbn: Optional[str] = None,
    year: Optional[int] = None,
    language: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = None,
    exact_match: bool = False
):
    """
    Unified search endpoint for books
    
    If 'query' is provided, performs a general search across multiple fields.
    Otherwise, uses the specific field parameters for more targeted searching.
    
    Parameters:
    - query: General search term to match across multiple fields
    - title: Filter by book title
    - author: Filter by author name
    - publisher: Filter by publisher name
    - category: Filter by category name
    - isbn: Filter by ISBN
    - year: Filter by publication year
    - language: Filter by language
    - status: Filter by availability status
    - limit: Maximum number of results to return
    - offset: Number of results to skip (for pagination)
    - sort_by: Field to sort results by (e.g. 'title', 'year', 'author')
    - exact_match: If True, requires exact matches for string fields
    """
    if query:
        return book_crud.general_search(
            db, 
            query=query, 
            limit=limit,
            offset=offset,
            sort_by=sort_by
        )
    
    return book_crud.search_books(
        db,
        title=title,
        author_name=author,
        publisher_name=publisher,
        category_name=category,
        isbn=isbn,
        publication_year=year,
        language_name=language,
        status=status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        exact_match=exact_match
    )