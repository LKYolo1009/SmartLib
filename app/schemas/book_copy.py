from pydantic import BaseModel, field_validator, Field
from datetime import date
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from uuid import UUID

class BookStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    PROCESSING = "processing"
    MISSING = "missing"
    DAMAGED = "damaged"
    UNPUBLISHED = "unpublished"

class BookCondition(str, Enum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class AcquisitionType(str, Enum):
    PURCHASED = "purchased"
    DONATED = "donated"

class BookCopyBase(BaseModel):
    book_id: int
    acquisition_type: str
    acquisition_date: date = Field(default_factory=date.today)
    price: Optional[float] = None
    condition: str = "good"
    status: str = "available"
    notes: Optional[str] = None

class BookCopyCreate(BookCopyBase):
    pass

class BookCopyUpdate(BaseModel):
    book_id: Optional[int] = None
    acquisition_type: Optional[str] = None
    acquisition_date: Optional[date] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class BookCopyResponse(BookCopyBase):
    copy_id: int

    qr_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    book_title: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('qr_code', mode='before')
    def validate_qr_code(cls, v):
        # Convert UUID to string
        if v is None:
            return None
        return str(v)

class BookCopyStatusUpdate(BaseModel):
    status: str
    condition: Optional[str] = None
    notes: Optional[str] = None

class BookBorrowStatusResponse(BaseModel):
    book_id: int
    title: str
    total_copies: int
    available_copies: int
    copies_info: List[dict]