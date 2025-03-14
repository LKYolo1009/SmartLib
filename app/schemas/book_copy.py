from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
from uuid import UUID

class BookCopyBase(BaseModel):
    """Book Copy Basic Information"""
    book_id: int = Field(..., description="Book ID", example=1)
    call_number: str = Field(..., description="Call Number", example="F12.345")
    acquisition_type: str = Field(..., description="Acquisition Type", example="purchased")
    acquisition_date: date = Field(..., description="Acquisition Date", example="2023-01-15")
    price: Optional[float] = Field(None, description="Price", example=48.00)
    condition: Optional[str] = Field("good", description="Book Condition", example="good")
    status: Optional[str] = Field("available", description="Book Status", example="available")
    notes: Optional[str] = Field(None, description="Notes")
    
    @validator('acquisition_type')
    def validate_acquisition_type(cls, v):
        """Validate Acquisition Type for valid values"""
        valid_types = ["purchased", "donated"]
        if v not in valid_types:
            raise ValueError(f'Acquisition Type must be one of the following: {", ".join(valid_types)}')
        return v
    
    @validator('condition')
    def validate_condition(cls, v):
        """Validate Book Condition for valid values"""
        valid_conditions = ["new", "good", "fair", "poor", "damaged"]
        if v not in valid_conditions:
            raise ValueError(f'Book Condition must be one of the following: {", ".join(valid_conditions)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate Book Status for valid values"""
        valid_statuses = ["available", "borrowed", "missing", "unpublished", "disposed"]
        if v not in valid_statuses:
            raise ValueError(f'Book Status must be one of the following: {", ".join(valid_statuses)}')
        return v
    
    @validator('call_number')
    def validate_call_number(cls, v):
        """Validate call number format"""
        if not all(c.isupper() or c.isdigit() or c in '.-' for c in v):
            raise ValueError('Call number can only contain uppercase letters, numbers, dots and hyphens')
        return v

class BookCopyCreate(BookCopyBase):
    """Model used when creating a book copy"""
    pass
class BookCopyUpdate(BookCopyBase):
    pass
class BookCopyResponse(BookCopyBase):
    """Model used when returning book copy information"""
    copy_id: int
    qr_code: UUID
    book_title: Optional[str] = None  # Can include associated book title

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "copy_id": 1,
                "book_id": 1,
                "book_title": "红楼梦",
                "call_number": "F12.345",
                "qr_code": "123e4567-e89b-12d3-a456-426614174000",
                "acquisition_type": "purchased",
                "acquisition_date": "2023-01-15",
                "price": 48.00,
                "condition": "good",
                "status": "available",
                "notes": "First edition"
            }
        }