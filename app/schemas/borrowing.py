from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum


class BorrowStatus(str, Enum):
    """Enumeration of possible borrow statuses"""
    BORROWED = "borrowed"
    EXTENDED = "extended"
    RETURNED = "returned"
    OVERDUE = "overdue"


class BorrowBase(BaseModel):
    """Basic information of borrowing"""
    copy_id: int = Field(..., description="Book copy ID", example=1)
    student_id: int = Field(..., description="Student ID", example=1)
    due_date: datetime = Field(..., description="Due date", example="2023-02-01T23:59:59")
    
    @field_validator('due_date')
    def validate_due_date(cls, v):
        """Validate that the due date is after the current date"""
        if v < datetime.now():
            raise ValueError('The due date must be after the current date')
        return v


class BorrowCreate(BorrowBase):
    """Model used when creating a borrowing record"""
    borrow_date: Optional[datetime] = Field(
        None,
        description="Borrow date (defaults to current time if not provided)",
        example="2023-01-01T12:00:00"
    )

    @field_validator('borrow_date')
    def set_borrow_date(cls, v):
        """Set borrow date to current time if not provided"""
        return v or datetime.now()


class BorrowUpdate(BaseModel):
    """Model used when updating a borrowing record"""
    extension_date: Optional[datetime] = Field(
        None,
        description="New due date after extension",
        example="2023-02-15T23:59:59"
    )
    return_date: Optional[datetime] = Field(
        None,
        description="Date when book was returned",
        example="2023-01-25T14:30:00"
    )
    status: Optional[BorrowStatus] = Field(
        None,
        description="Borrow status",
        example="returned"
    )
    
    @field_validator('extension_date')
    def validate_extension_date(cls, v):
        """Validate that the extension date is after the current date"""
        if v is not None and v < datetime.now():
            raise ValueError('The extension date must be after the current date')
        return v
    
    @field_validator('return_date')
    def validate_return_date(cls, v):
        """Validate that the return date is not in the future"""
        if v is not None and v > datetime.now():
            raise ValueError('The return date cannot be in the future')
        return v


class BorrowResponse(BorrowBase):
    """Model used when returning borrowing basic information"""
    borrow_id: int
    borrow_date: datetime
    status: BorrowStatus
    extension_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    is_overdue: bool = Field(
        ...,
        description="Indicates if the loan is currently overdue",
        example=False
    )
    days_remaining: Optional[int] = Field(
        None,
        description="Days remaining until due (negative if overdue)",
        example=15
    )

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "borrow_id": 1,
                "copy_id": 1,
                "student_id": 1,
                "borrow_date": "2023-01-01T12:00:00",
                "due_date": "2023-02-01T23:59:59",
                "extension_date": None,
                "return_date": None,
                "status": "borrowed",
                "is_overdue": False,
                "days_remaining": 31
            }
        }


class BorrowDetail(BorrowResponse):
    """Model used when returning detailed borrowing information including associated data"""
    book_title: str
    isbn: Optional[str] = None
    call_number: str
    student_name: str
    student_matric_number: str
    student_email: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "borrow_id": 1,
                "copy_id": 1,
                "student_id": 1,
                "borrow_date": "2023-01-01T12:00:00",
                "due_date": "2023-02-01T23:59:59",
                "extension_date": None,
                "return_date": None,
                "status": "borrowed",
                "is_overdue": False,
                "days_remaining": 31,
                "book_title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
                "call_number": "F12.345",
                "student_name": "John Smith",
                "student_matric_number": "S12345678Z",
                "student_email": "john.smith@university.edu"
            }
        }


class BorrowSummary(BaseModel):
    """Summary of a student's borrowing history"""
    student_id: int
    student_name: str
    student_email: str
    current_borrows: int
    total_borrows: int
    overdue_borrows: int
    borrowing_history: List[BorrowResponse]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "student_id": 1,
                "student_name": "John Smith",
                "student_email": "john.smith@university.edu",
                "current_borrows": 2,
                "total_borrows": 15,
                "overdue_borrows": 0,
                "borrowing_history": [
                    {
                        "borrow_id": 1,
                        "copy_id": 1,
                        "student_id": 1,
                        "borrow_date": "2023-01-01T12:00:00",
                        "due_date": "2023-02-01T23:59:59",
                        "extension_date": None,
                        "return_date": None,
                        "status": "borrowed",
                        "is_overdue": False,
                        "days_remaining": 31
                    }
                ]
            }
        }