from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import book_copy
from app.schemas.book_copy import BookCopyCreate, BookCopyResponse

router = APIRouter()

# retrieves a list of book copies, with optional filtering by book ID and status.
@router.get("/", response_model=List[BookCopyResponse])
def get_book_copies(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    book_id: int = None,
    status: str = None,
):
    """
    Retrieve a list of book copies, with optional filtering by book ID and status.
    """
    if book_id:
        if status == "available":
            return book_copy.get_available_by_book(db, book_id=book_id, skip=skip, limit=limit)
        return book_copy.get_by_book(db, book_id=book_id, skip=skip, limit=limit)
    # TODO: Implement filtering by status for all book copies
    return book_copy.get_multi(db, skip=skip, limit=limit)

#creates a new book copy.
@router.post("/", response_model=BookCopyResponse, status_code=status.HTTP_201_CREATED)
def create_book_copy(
    *,
    db: Session = Depends(deps.get_db),
    book_copy_in: BookCopyCreate,
):
    """
    Create a new book copy.
    """
    return book_copy.create(db=db, obj_in=book_copy_in)

# This endpoint retrieves detailed information about a specific book copy by its ID.
@router.get("/{copy_id}", response_model=BookCopyResponse)
def get_book_copy(
    *,
    db: Session = Depends(deps.get_db),
    copy_id: int,
):
    """
    Retrieve detailed information about a book copy.
    """
    book_copy = book_copy.get_with_book(db, copy_id=copy_id)
    if not book_copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found"
        )
    return book_copy

# This endpoint updates the status of a specific book copy by its ID.
@router.put("/{copy_id}/status", response_model=BookCopyResponse)
def update_book_copy_status(
    *,
    db: Session = Depends(deps.get_db),
    copy_id: int,
    status: str,
):
    """
    Update the status of a book copy.
    """
    return book_copy.update_status(db=db, copy_id=copy_id, status=status)

# This endpoint retrieves a book copy by its call number.
@router.get("/call-number/{call_number}", response_model=BookCopyResponse)
def get_book_copy_by_call_number(
    *,
    db: Session = Depends(deps.get_db),
    call_number: str,
):
    """
    Retrieve a book copy by its call number.
    """
    book_copy = book_copy.get_by_call_number(db, call_number=call_number)
    if not book_copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found"
        )
    return book_copy