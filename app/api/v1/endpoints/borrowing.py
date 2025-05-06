from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.crud.borrowing import borrowing_crud
from app.schemas.borrowing import (
    BorrowCreate, BorrowResponse, BorrowDetail, BorrowStatus, 
    BorrowingStats, ActiveBorrowingsResponse
)

router = APIRouter()


@router.get("/", response_model=List[BorrowDetail])
def get_all_borrowings(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Skip the first N records"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: str = Query(None, description="Filter status: active, returned, overdue, all"),
    sort_by: str = Query("borrow_date", description="Sort by field: borrow_date, due_date, return_date"),
    order: str = Query("desc", description="Sort direction: asc or desc")
):
    """Get all borrowing records with optional filtering"""
    if status == "active":
        records = borrowing_crud.get_active(db, skip=skip, limit=limit, sort_by=sort_by, order=order)
    elif status == "returned":
        records = borrowing_crud.get_returned(db, skip=skip, limit=limit, sort_by=sort_by, order=order)
    elif status == "overdue":
        records = borrowing_crud.get_overdue(db, skip=skip, limit=limit, sort_by=sort_by, order=order)
    else:
        records = borrowing_crud.get_multi(db, skip=skip, limit=limit, sort_by=sort_by, order=order)
    
    return records


@router.post("/", response_model=BorrowDetail, status_code=status.HTTP_201_CREATED)
def borrow_book(
    *,
    db: Session = Depends(get_db),
    borrow_in: BorrowCreate,
):
    """
    Create a new borrowing record
    
    Only need to provide:
    - copy_id: Book copy ID
    - matric_number: Student matriculation number
    - loan_days: (optional) Borrowing days, default 14 days
    
    The system will automatically set the borrowing date to the current date and calculate the due date
    """
    return borrowing_crud.create_borrow(db=db, obj_in=borrow_in)

@router.put("/return/{borrow_id}", response_model=BorrowDetail)
def return_book(
    borrow_id: int,
    db: Session = Depends(get_db),
):
    """Return the book"""
    return borrowing_crud.return_book(db=db, borrow_id=borrow_id)


@router.put("/extend/{borrow_id}", response_model=BorrowDetail)
def extend_borrowing(
    borrow_id: int,
    days: int = Query(14, ge=1, le=30, description="Extension days"),
    db: Session = Depends(get_db),
):
    """Extend the borrowing period"""
    return borrowing_crud.extend_due_date(db=db, borrow_id=borrow_id, days=days)


@router.get("/student/{matric_number}", response_model=List[BorrowDetail])
def get_student_borrowings(
    matric_number: str,
    active_only: bool = Query(False, description="Only return current borrowings"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get borrowing records for a specific student"""
    records = borrowing_crud.get_by_matric_number(
        db, 
        matric_number=matric_number,
        active_only=active_only
    )
    
    # Limit the records after retrieving
    records = records[skip:skip+limit]
    
    detailed_records = []
    for record in records:
        detailed_record = borrowing_crud.get_with_details(db, borrow_id=record.borrow_id)
        if detailed_record:
            detailed_records.append(detailed_record)
    
    return detailed_records


@router.get("/student/{matric_number}/history", response_model=List[BorrowDetail])
def get_student_borrowing_history(
    matric_number: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    include_active: bool = Query(True, description="Include current borrowings")
):
    """Get full borrowing history for a student"""
    records = borrowing_crud.get_by_matric_number(
        db, 
        matric_number=matric_number,
        active_only=not include_active
    )
    
    # Limit the number of records
    records = records[:limit]
    
    detailed_records = []
    for record in records:
        detailed_record = borrowing_crud.get_with_details(db, borrow_id=record.borrow_id)
        if detailed_record:
            detailed_records.append(detailed_record)
    
    return detailed_records

#done
@router.get("/overdue", response_model=List[BorrowDetail])
def get_overdue_borrowings(
    days_overdue: Optional[int] = Query(None, description="Overdue days threshold"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get overdue borrowing records"""
    now = datetime.now(timezone.utc)
    due_date_threshold = None
    if days_overdue is not None:
        due_date_threshold = now - timedelta(days=days_overdue)
    
    records = borrowing_crud.get_overdue(
        db,
        skip=skip,
        limit=limit,
        due_date_threshold=due_date_threshold
    )
    
    detailed_records = []
    for record in records:
        detailed_record = borrowing_crud.get_with_details(db, borrow_id=record.borrow_id)
        if detailed_record:
            detailed_records.append(detailed_record)
    
    return detailed_records


@router.get("/due-soon", response_model=List[BorrowDetail])
def get_due_soon_borrowings(
    days: int = Query(3, ge=1, le=7, description="Days threshold for due soon"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get borrowing records due soon (for reminder)"""
    records = borrowing_crud.get_due_soon(db, days=days, limit=limit)
    
    detailed_records = []
    for record in records:
        detailed_record = borrowing_crud.get_with_details(db, borrow_id=record.borrow_id)
        if detailed_record:
            detailed_records.append(detailed_record)
    
    return detailed_records


@router.get("/book/{book_id}", response_model=List[BorrowDetail])
def get_book_borrowing_history(
    book_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get borrowing history for a specific book"""
    records = borrowing_crud.get_by_book(db, book_id=book_id, skip=skip, limit=limit)
    
    detailed_records = []
    for record in records:
        detailed_record = borrowing_crud.get_with_details(db, borrow_id=record.borrow_id)
        if detailed_record:
            detailed_records.append(detailed_record)
    
    return detailed_records

# done
@router.get("/popular", response_model=List[Dict])
def get_popular_books(
    days: int = Query(90, ge=1, le=365, description="Days range for statistics"),
    limit: int = Query(10, ge=1, le=50, description="Number of popular books to return"),
    db: Session = Depends(get_db),
):
    """Get the most popular books in a period of time"""
    return borrowing_crud.get_popular_books(db, days=days, limit=limit)


@router.get("/stats", response_model=BorrowingStats)
def get_borrowing_stats(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Days range for statistics"),
    category_id: Optional[int] = None
):
    """Get borrowing statistics"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    return borrowing_crud.get_borrowing_stats(
        db,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id
    )


# @router.get("/student-stats/{matric_number}", response_model=Dict[str, Any])
# def get_student_borrowing_stats(
#     matric_number: str,
#     db: Session = Depends(get_db),
# ):
#     """Get borrowing statistics for a specific student"""
#     return borrowing_crud.get_student_borrowing_stats(db, matric_number=matric_number)


@router.get("/active", response_model=ActiveBorrowingsResponse)
def get_active_borrowings(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    overdue_only: bool = Query(False, description="Only show overdue borrowings"),
    matric_number: Optional[str] = Query(None, description="Filter by student matriculation number")
):
    """
    Get current active borrowings with filtering options and statistical data
    """
    active_borrowings = borrowing_crud.get_active_borrowings(
        db,
        skip=skip,
        limit=limit,
        overdue_only=overdue_only,
        matric_number=matric_number
    )
    
    total_count = borrowing_crud.count_active_borrowings(
        db,
        overdue_only=overdue_only,
        matric_number=matric_number
    )
    
    # Calculate statistical data
    now = datetime.now(timezone.utc)
    overdue_count = sum(1 for b in active_borrowings if b.due_date < now)
    
    return {
        "total_count": total_count,
        "returned_count": total_count - len(active_borrowings),
        "overdue_count": overdue_count,
        "borrowings": active_borrowings
    }


