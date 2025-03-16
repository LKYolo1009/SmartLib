from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import borrowing
from app.schemas.borrowing import BorrowCreate, BorrowResponse, BorrowDetail

router = APIRouter()

@router.post("/", response_model=BorrowDetail, status_code=status.HTTP_201_CREATED)
def borrow_book(
    *,
    db: Session = Depends(get_db),
    borrow_in: BorrowCreate,
):
    """
    Borrow a book.
    """
    return borrowing.create_borrow(db=db, obj_in=borrow_in)

@router.put("/return/{borrow_id}", response_model=BorrowDetail)
def return_book(
    *,
    db: Session = Depends(get_db),
    borrow_id: int,
):
    """
    Return a book.
    """
    return borrowing.return_book(db=db, borrow_id=borrow_id)

@router.put("/extend/{borrow_id}", response_model=BorrowDetail)
def extend_borrowing(
    *,
    db: Session = Depends(get_db),
    borrow_id: int,
    days: int = Query(14, ge=1, le=30, description="Number of days to extend"),
):
    """
    Extend the borrowing period.
    """
    return borrowing.extend_due_date(db=db, borrow_id=borrow_id, days=days)

@router.get("/student/{student_id}", response_model=List[BorrowDetail])
def get_student_borrowings(
    *,
    db: Session = Depends(get_db),
    student_id: int,
    active_only: bool = Query(False, description="Return only active borrowings"),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a student's borrowing records.
    """
    if active_only:
        records = borrowing.get_active_by_student(db, student_id=student_id)
    else:
        records = borrowing.get_by_student(db, student_id=student_id, skip=skip, limit=limit)
    
    # Load detailed information
    detailed_records = []
    for record in records:
        detailed_record = borrowing.get_with_details(db, borrow_id=record.borrow_id)
        detailed_records.append(detailed_record)
    
    return detailed_records

@router.get("/overdue", response_model=List[BorrowDetail])
def get_overdue_borrowings(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all overdue borrowing records.
    """
    records = borrowing.get_overdue(db, skip=skip, limit=limit)
    
    # Load detailed information
    detailed_records = []
    for record in records:
        detailed_record = borrowing.get_with_details(db, borrow_id=record.borrow_id)
        detailed_records.append(detailed_record)
    
    return detailed_records