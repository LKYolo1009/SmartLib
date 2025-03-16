from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import get_db
from app.crud import borrowing as borrowing_crud
from app.schemas.borrowing import (
BorrowResponse, BorrowDetail,BorrowingStats,ActiveBorrowingsResponse
)

router = APIRouter()

@router.get("/history/{student_id}", response_model=List[BorrowDetail])
def get_student_borrowing_history(
    student_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    include_active: bool = True
):
    """
    Get borrowing history for a student
    """
    return borrowing_crud.get_student_history(
        db, 
        student_id=student_id, 
        limit=limit,
        include_active=include_active
    )

@router.get("/stats", response_model=BorrowingStats)
def get_borrowing_stats(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    category_id: Optional[int] = None
):
    """
    Get borrowing statistics
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return borrowing_crud.get_statistics(
        db,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id
    )

@router.get("/active", response_model=ActiveBorrowingsResponse)
def get_active_borrowings(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    overdue_only: bool = False,
    student_id: Optional[int] = None
):
    """
    Get active borrowings with optional filtering
    """
    active_borrowings = borrowing_crud.get_active_borrowings(
        db,
        skip=skip,
        limit=limit,
        overdue_only=overdue_only,
        student_id=student_id
    )
    
    total_count = borrowing_crud.count_active_borrowings(
        db,
        overdue_only=overdue_only,
        student_id=student_id
    )
    
    # Calculate statistics
    now = datetime.now()
    overdue_count = sum(1 for b in active_borrowings if b.due_date < now)
    
    return {
        "total_count": total_count,
        "returned_count": total_count - len(active_borrowings),
        "overdue_count": overdue_count,
        "borrowings": active_borrowings
    }

@router.get("/overdue", response_model=List[BorrowDetail])
def get_overdue_borrowings(
    db: Session = Depends(get_db),
    days_overdue: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get overdue borrowings
    """
    now = datetime.now()
    due_date_threshold = None
    if days_overdue is not None:
        due_date_threshold = now - timedelta(days=days_overdue)
    
    return borrowing_crud.get_overdue_borrowings(
        db,
        due_date_threshold=due_date_threshold,
        limit=limit
    )