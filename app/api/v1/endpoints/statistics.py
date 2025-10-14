from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
import logging

# Configure logger
logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.crud import statistics as crud_stats
from app.schemas.statistics import (
    DailyStats,
    CategoryStats,
    OverdueBooks,
    StudentStats,
    KPIMetrics,
    PopularBooks,
    BorrowingTrend,
    StudentActivity,
    LibraryUtilization
)

router = APIRouter()

@router.get("/daily", response_model=List[DailyStats])
def get_daily_stats(
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    db: Session = Depends(get_db)
):
    """Get daily borrowing and return statistics"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=90)
    if not end_date:
        end_date = datetime.now()
    
    return crud_stats.get_daily_stats(db, start_date, end_date)

@router.get("/categories", response_model=List[CategoryStats])
def get_category_stats(db: Session = Depends(get_db)):
    """Get book category statistics"""
    return crud_stats.get_category_stats(db)

@router.get("/overdue", response_model=List[OverdueBooks])
def get_overdue_books(db: Session = Depends(get_db)):
    """Get list of overdue books"""
    return crud_stats.get_overdue_books(db)

@router.get("/students", response_model=List[StudentStats])
def get_student_stats(db: Session = Depends(get_db)):
    """Get student borrowing statistics"""
    return crud_stats.get_student_stats(db)

@router.get("/kpi", response_model=KPIMetrics)
def get_kpi_metrics(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Get KPI metrics (supports optional start_date/end_date for period-aware KPIs)."""
    try:
        if start_date and end_date:
            # Ensure timezone awareness
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")
            if (end_date - start_date).days > 365:
                raise HTTPException(status_code=400, detail="Date range cannot exceed one year")
            # Prevent future query
            now = datetime.now(timezone.utc)
            if start_date > now or end_date > now:
                raise HTTPException(status_code=400, detail="Cannot query future dates")
        else:
            start_date = None
            end_date = None

        return crud_stats.get_kpi_metrics(db, start_date, end_date)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in KPI endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular-books", response_model=List[PopularBooks])
def get_popular_books(
    limit: int = Query(default=10, ge=1, le=100),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Get most popular books based on borrowing frequency"""
    try:
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)  # Default to 30 days
        
        # Ensure dates have timezone information
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )
        
        # Validate date range doesn't exceed one year
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed one year"
            )
        
        result = crud_stats.get_popular_books(db, limit, start_date, end_date)
        if not result:
            return []
        return result
    except Exception as e:
        logger.error(f"Error in get_popular_books endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/borrowing-trends", response_model=BorrowingTrend)
def get_borrowing_trends(
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    interval: str = Query(default="day", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Get borrowing trends over time"""
    try:
        # Set default date range
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=90)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Ensure datetime values are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )
        
        # Validate the date range does not exceed one year
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed one year"
            )
        
        # Ensure dates are not in the future
        now = datetime.now(timezone.utc)
        if start_date > now or end_date > now:
            raise HTTPException(status_code=400, detail="Cannot query future dates")
        
        # Fetch data
        result = crud_stats.get_borrowing_trends(db, start_date, end_date, interval)
        
        # Return empty result when no data is found
        if not result:
            return BorrowingTrend(
                time_period=interval,
                total_borrows=0,
                unique_readers=0,
                average_duration=0.0,
                category_distribution={},
                data=[]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in borrowing-trends endpoint: {str(e)}", exc_info=True)
        # Return different error messages based on error type
        if "timezone" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid timezone information")
        elif "interval" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid interval parameter")
        elif "database" in str(e).lower():
            raise HTTPException(status_code=500, detail="Database error occurred")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/student-activity", response_model=List[StudentActivity])
def get_student_activity(
    limit: int = Query(default=10, ge=1, le=100),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db)
):
    """Get most active students based on borrowing frequency"""
    try:
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        result = crud_stats.get_student_activity(db, limit, start_date, end_date)
        if not result:
            return []
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/library-utilization", response_model=LibraryUtilization)
def get_library_utilization(
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    db: Session = Depends(get_db)
):
    """Get library utilization metrics"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    return crud_stats.get_library_utilization(db, start_date, end_date)


@router.get("/category-trends", response_model=Dict)
def get_category_trends(
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    db: Session = Depends(get_db)
):
    """Get borrowing trends by category"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=90)
    if not end_date:
        end_date = datetime.now()
    
    return crud_stats.get_category_trends(db, start_date, end_date) 