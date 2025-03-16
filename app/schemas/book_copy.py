from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from uuid import UUID


class BookCondition(str, Enum):
    """Enumeration of valid book condition values"""
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"


class BookStatus(str, Enum):
    """Enumeration of valid book status values"""
    AVAILABLE = "available"
    BORROWED = "borrowed"
    PROCESSING = "processing"
    MISSING = "missing"
    UNPUBLISHED = "unpublished"
    DISPOSED = "disposed"
    DAMAGED = "damaged"


class AcquisitionType(str, Enum):
    """Enumeration of valid acquisition types"""
    PURCHASED = "purchased"
    DONATED = "donated"


class BookCopyBase(BaseModel):
    """Book Copy Basic Information"""
    book_id: int = Field(..., description="Book ID", example=1)
    call_number: str = Field(..., description="Call Number", example="F12.345")
    acquisition_type: str = Field(..., description="Acquisition Type", example="purchased")
    acquisition_date: date = Field(..., description="Acquisition Date", example="2023-01-15")
    price: Optional[float] = Field(None, description="Price", example=48.00)
    condition: str = Field("good", description="Book Condition", example="good")
    status: str = Field("available", description="Book Status", example="available")
    notes: Optional[str] = Field(None, description="Notes")
    
    @field_validator('acquisition_type')
    def validate_acquisition_type(cls, v):
        """Validate Acquisition Type for valid values"""
        valid_types = [e.value for e in AcquisitionType]
        if v not in valid_types:
            raise ValueError(f'Acquisition Type must be one of the following: {", ".join(valid_types)}')
        return v
    
    @field_validator('condition')
    def validate_condition(cls, v):
        """Validate Book Condition for valid values"""
        valid_conditions = [e.value for e in BookCondition]
        if v not in valid_conditions:
            raise ValueError(f'Book Condition must be one of the following: {", ".join(valid_conditions)}')
        return v
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate Book Status for valid values"""
        valid_statuses = [e.value for e in BookStatus]
        if v not in valid_statuses:
            raise ValueError(f'Book Status must be one of the following: {", ".join(valid_statuses)}')
        return v
    
    @field_validator('call_number')
    def validate_call_number(cls, v):
        """Validate call number format"""
        if not all(c.isupper() or c.isdigit() or c in '.-' for c in v):
            raise ValueError('Call number can only contain uppercase letters, numbers, dots and hyphens')
        return v


class BookCopyCreate(BookCopyBase):
    """Model used when creating a book copy"""
    qr_code: Optional[str] = Field(None, description="QR Code for the book copy")


class BookCopyUpdate(BaseModel):
    """Model used when updating a book copy - all fields optional"""
    book_id: Optional[int] = Field(None, description="Book ID", example=1)
    call_number: Optional[str] = Field(None, description="Call Number", example="F12.345")
    acquisition_type: Optional[str] = Field(None, description="Acquisition Type", example="purchased")
    acquisition_date: Optional[date] = Field(None, description="Acquisition Date", example="2023-01-15")
    price: Optional[float] = Field(None, description="Price", example=48.00)
    condition: Optional[str] = Field(None, description="Book Condition", example="good")
    status: Optional[str] = Field(None, description="Book Status", example="available")
    notes: Optional[str] = Field(None, description="Notes")
    
    @field_validator('acquisition_type')
    def validate_acquisition_type(cls, v):
        """Validate Acquisition Type for valid values"""
        if v is not None:
            valid_types = [e.value for e in AcquisitionType]
            if v not in valid_types:
                raise ValueError(f'Acquisition Type must be one of the following: {", ".join(valid_types)}')
        return v
    
    @field_validator('condition')
    def validate_condition(cls, v):
        """Validate Book Condition for valid values"""
        if v is not None:
            valid_conditions = [e.value for e in BookCondition]
            if v not in valid_conditions:
                raise ValueError(f'Book Condition must be one of the following: {", ".join(valid_conditions)}')
        return v
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate Book Status for valid values"""
        if v is not None:
            valid_statuses = [e.value for e in BookStatus]
            if v not in valid_statuses:
                raise ValueError(f'Book Status must be one of the following: {", ".join(valid_statuses)}')
        return v
    
    @field_validator('call_number')
    def validate_call_number(cls, v):
        """Validate call number format"""
        if v is not None:
            if not all(c.isupper() or c.isdigit() or c in '.-' for c in v):
                raise ValueError('Call number can only contain uppercase letters, numbers, dots and hyphens')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "condition": "fair",
                "status": "borrowed",
                "notes": "Pages 10-15 have highlighting"
            }
        }


class BookCopyStatusUpdate(BaseModel):
    """Model used when updating only the status of a book copy"""
    status: str = Field(..., description="New status for the book copy")
    condition: Optional[str] = Field(None, description="New condition for the book copy")
    notes: Optional[str] = Field(None, description="Notes about the status change")
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate Book Status for valid values"""
        valid_statuses = [e.value for e in BookStatus]
        if v not in valid_statuses:
            raise ValueError(f'Book Status must be one of the following: {", ".join(valid_statuses)}')
        return v
    
    @field_validator('condition')
    def validate_condition(cls, v):
        """Validate Book Condition for valid values"""
        if v is not None:
            valid_conditions = [e.value for e in BookCondition]
            if v not in valid_conditions:
                raise ValueError(f'Book Condition must be one of the following: {", ".join(valid_conditions)}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "status": "borrowed",
                "condition": "good",
                "notes": "Loaned to student ID 10234"
            }
        }


class BookCopyResponse(BookCopyBase):
    """Model used when returning book copy information"""
    copy_id: int
    qr_code: str
    book_title: str
    date_added: datetime = Field(..., description="Date when the copy was added to system")
    last_updated: datetime = Field(..., description="Date when the copy was last updated")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "copy_id": 1,
                "book_id": 1,
                "book_title": "Dream of the Red Chamber",
                "call_number": "F12.345",
                "qr_code": "123e4567-e89b-12d3-a456-426614174000",
                "acquisition_type": "purchased",
                "acquisition_date": "2023-01-15",
                "price": 48.00,
                "condition": "good",
                "status": "available",
                "notes": "First edition",
                "date_added": "2023-01-15T10:00:00",
                "last_updated": "2023-01-15T10:00:00"
            }
        }


class BookCopyDetailResponse(BookCopyResponse):
    """Model used when returning detailed book copy information with borrowing history"""
    current_borrowing: Optional[Dict[str, Any]] = Field(None, description="Current borrowing information if borrowed")
    borrowing_history: List[Dict[str, Any]] = Field([], description="Borrowing history for this copy")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "copy_id": 1,
                "book_id": 1,
                "book_title": "Dream of the Red Chamber",
                "call_number": "F12.345",
                "qr_code": "123e4567-e89b-12d3-a456-426614174000",
                "acquisition_type": "purchased",
                "acquisition_date": "2023-01-15",
                "price": 48.00,
                "condition": "good",
                "status": "borrowed",
                "notes": "First edition",
                "date_added": "2023-01-15T10:00:00",
                "last_updated": "2023-01-15T10:00:00",
                "current_borrowing": {
                    "borrow_id": 5,
                    "student_id": 101,
                    "student_name": "John Doe",
                    "borrow_date": "2023-03-15T14:30:00",
                    "due_date": "2023-04-15T23:59:59",
                    "is_overdue": False
                },
                "borrowing_history": [
                    {
                        "borrow_id": 3,
                        "student_id": 102,
                        "student_name": "Jane Smith",
                        "borrow_date": "2023-01-20T09:15:00",
                        "return_date": "2023-02-18T11:30:00",
                        "was_overdue": False
                    }
                ]
            }
        }


class BorrowInfoResponse(BaseModel):
    """Model for borrowing information response"""
    borrow_id: int
    student_id: int
    due_date: datetime
    is_overdue: bool


class CopyStatusInfo(BaseModel):
    """Model for individual copy status information"""
    copy_id: int
    call_number: str
    status: str
    condition: str
    borrow_info: Optional[BorrowInfoResponse] = None


class BookBorrowStatusResponse(BaseModel):
    """Model for book borrowing status response"""
    book_id: int
    total_copies: int
    available_copies: int
    copies_info: List[CopyStatusInfo]
    
    class Config:
        schema_extra = {
            "example": {
                "book_id": 1,
                "total_copies": 3,
                "available_copies": 1,
                "copies_info": [
                    {
                        "copy_id": 1,
                        "call_number": "F12.345",
                        "status": "available",
                        "condition": "good",
                        "borrow_info": None
                    },
                    {
                        "copy_id": 2,
                        "call_number": "F12.346",
                        "status": "borrowed",
                        "condition": "good",
                        "borrow_info": {
                            "borrow_id": 5,
                            "student_id": 101,
                            "due_date": "2023-04-15T23:59:59",
                            "is_overdue": False
                        }
                    }
                ]
            }
        }


class BookCopyBatchStatusUpdate(BaseModel):
    """Model for batch updating book copy statuses"""
    copy_ids: List[int] = Field(..., description="List of copy IDs to update")
    status: str = Field(..., description="New status for the book copies")
    condition: Optional[str] = Field(None, description="New condition for the book copies") 
    notes: Optional[str] = Field(None, description="Optional notes about the status change")
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate Book Status for valid values"""
        valid_statuses = [e.value for e in BookStatus]
        if v not in valid_statuses:
            raise ValueError(f'Book Status must be one of the following: {", ".join(valid_statuses)}')
        return v
    
    @field_validator('condition')
    def validate_condition(cls, v):
        """Validate Book Condition for valid values"""
        if v is not None:
            valid_conditions = [e.value for e in BookCondition]
            if v not in valid_conditions:
                raise ValueError(f'Book Condition must be one of the following: {", ".join(valid_conditions)}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "copy_ids": [1, 2, 3],
                "status": "missing",
                "condition": "poor",
                "notes": "Not found during inventory check"
            }
        }