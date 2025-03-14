from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID

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
        valid_types = ["purchased", "donated"]
        if v not in valid_types:
            raise ValueError(f'Acquisition Type must be one of the following: {", ".join(valid_types)}')
        return v
    
    @field_validator('condition')
    def validate_condition(cls, v):
        """Validate Book Condition for valid values"""
        valid_conditions = ["new", "good", "fair", "poor", "damaged"]
        if v not in valid_conditions:
            raise ValueError(f'Book Condition must be one of the following: {", ".join(valid_conditions)}')
        return v
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate Book Status for valid values"""
        valid_statuses = ["available", "borrowed", "missing", "unpublished", "disposed"]
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
    # Default implementation inherited from BookCopyBase
    class Config:
        schema_extra = {
            "example": {
                "book_id": 1,
                "call_number": "F12.345",
                "acquisition_type": "purchased",
                "acquisition_date": "2023-01-15",
                "price": 48.00,
                "condition": "new",
                "status": "available",
                "notes": "First edition"
            }
        }

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
            valid_types = ["purchased", "donated"]
            if v not in valid_types:
                raise ValueError(f'Acquisition Type must be one of the following: {", ".join(valid_types)}')
        return v
    
    @field_validator('condition')
    def validate_condition(cls, v):
        """Validate Book Condition for valid values"""
        if v is not None:
            valid_conditions = ["new", "good", "fair", "poor", "damaged"]
            if v not in valid_conditions:
                raise ValueError(f'Book Condition must be one of the following: {", ".join(valid_conditions)}')
        return v
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate Book Status for valid values"""
        if v is not None:
            valid_statuses = ["available", "borrowed", "missing", "unpublished", "disposed"]
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

class BookCopyResponse(BookCopyBase):
    """Model used when returning book copy information"""
    copy_id: int
    qr_code: UUID
    book_title: str  # Changed from Optional to required
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