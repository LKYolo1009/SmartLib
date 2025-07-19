from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime

class BookLocationBase(BaseModel):
    location_name: str
    location_description: Optional[str] = None

class BookLocationCreate(BookLocationBase):
    pass

class BookLocationUpdate(BaseModel):
    location_name: Optional[str] = None
    location_description: Optional[str] = None

class BookLocationResponse(BookLocationBase):
    location_id: int
    location_qr_code: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookLocationWithCopiesResponse(BookLocationResponse):
    book_copies_count: int = 0 