from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import borrowing
from app.schemas.book import BookCreate, BookResponse, BookDetail
from app.api import deps
from app.schemas.borrowing import BorrowDetail,BorrowCreate

router = APIRouter()


@router.post("/", response_model=BorrowDetail, status_code=status.HTTP_201_CREATED)
def borrow_book(
    *,
    db: Session = Depends(deps.get_db),
    borrow_in: BorrowCreate,
):
    """
    Borrow a book (No authentication required)
    """
    return borrowing.create_borrow(db=db, obj_in=borrow_in)

@router.put("/return/{borrow_id}", response_model=BorrowDetail)
def return_book(
    *,
    db: Session = Depends(deps.get_db),
    borrow_id: int,
):
    """
    Return a book (No authentication required)
    """
    return borrowing.return_book(db=db, borrow_id=borrow_id)
