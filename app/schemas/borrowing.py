from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class BorrowStatus(str, Enum):
    """Borrowing status options"""
    BORROWED = "borrowed"
    EXTENDED = "extended"
    RETURNED = "returned"
    OVERDUE = "overdue"


class BorrowCreate(BaseModel):
    """Simplified borrowing creation model"""
    copy_id: int = Field(..., description="Book copy ID", example=1)
    matric_number: str = Field(..., description="Student matriculation number")
    loan_days: Optional[int] = Field(None, ge=14, le=30, description="Loan period in days (default: 14)", example=14)


class BorrowResponse(BaseModel):
    """Basic borrowing response model"""
    borrow_id: int
    copy_id: int
    matric_number: str
    borrow_date: datetime
    due_date: datetime
    status: BorrowStatus
    extension_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    is_overdue: bool
    days_remaining: Optional[int] = None

    @field_validator('borrow_date', 'due_date', 'return_date', 'extension_date', mode='before')
    def ensure_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure all dates have timezone information"""
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "borrow_id": 1,
                "copy_id": 1,
                "matric_number": "A0123456Z",
                "borrow_date": "2023-01-01T12:00:00Z",
                "due_date": "2023-01-15T23:59:59Z",
                "extension_date": None,
                "return_date": None,
                "status": "borrowed",
                "is_overdue": False,
                "days_remaining": 14
            }
        }


class BorrowDetail(BorrowResponse):
    """Detailed borrowing response model with book and student info"""
    book_title: Optional[str] = None
    call_number: Optional[str] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "borrow_id": 1,
                "copy_id": 1,
                "matric_number": "A0123456Z",
                "borrow_date": "2023-01-01T12:00:00Z",
                "due_date": "2023-01-15T23:59:59Z",
                "extension_date": None,
                "return_date": None,
                "status": "borrowed",
                "is_overdue": False,
                "days_remaining": 14,
                "book_title": "Dream of the Red Chamber",
                "call_number": "LIT-123-1",
                "student_name": "John Smith",
                "student_email": "john.smith@university.edu"
            }
        }


class BorrowingStats(BaseModel):
    """Statistical information about borrowings"""
    total_borrowings: int
    active_borrowings: int
    overdue_borrowings: int
    average_days_kept: float
    most_borrowed_books: List[Dict[str, Any]]
    most_active_students: List[Dict[str, Any]]
    borrowings_by_month: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "total_borrowings": 250,
                "active_borrowings": 45,
                "overdue_borrowings": 12,
                "average_days_kept": 18.5,
                "most_borrowed_books": [
                    {
                        "book_id": 1,
                        "title": "Dream of the Red Chamber",
                        "borrow_count": 15
                    }
                ],
                "most_active_students": [
                    {
                        "matric_number": "A0123456Z",
                        "name": "John Smith",
                        "borrow_count": 8
                    }
                ],
                "borrowings_by_month": [
                    {
                        "month": "2023-01",
                        "count": 35
                    }
                ]
            }
        }


class ActiveBorrowingsResponse(BaseModel):
    """Response model for active borrowings query"""
    total_count: int
    returned_count: int
    overdue_count: int
    borrowings: List[BorrowDetail]

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 45,
                "returned_count": 0,
                "overdue_count": 12,
                "borrowings": [
                    {
                        "borrow_id": 1,
                        "copy_id": 1,
                        "matric_number": "A0123456Z",
                        "borrow_date": "2023-01-01T12:00:00Z",
                        "due_date": "2023-01-15T23:59:59Z",
                        "status": "borrowed",
                        "is_overdue": False,
                        "days_remaining": 14,
                        "book_title": "Dream of the Red Chamber",
                        "call_number": "LIT-123-1",
                        "student_name": "John Smith",
                        "student_email": "john.smith@university.edu"
                    }
                ]
            }
        }