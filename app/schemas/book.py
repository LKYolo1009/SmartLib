from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SortOrder(str, Enum):
    """Sort order options for book search results"""
    ASCENDING = "asc"
    DESCENDING = "desc"


class BookBase(BaseModel):
    """Book's Basic Information"""
    title: str = Field(..., description="Title", example="Dream of the Red Chamber")
    isbn: Optional[str] = Field(None, description="ISBN", example="9787020002207")
    call_number: str = Field(..., description="Call Number", example="LIT-123-1")
    author_id: int = Field(..., description="Author ID", example=1)
    publisher_id: Optional[int] = Field(None, description="Publisher ID", example=1)
    publication_year: Optional[int] = Field(None, description="Publication Year", example=1982)
    language_code: Optional[str] = Field(None, description="Language Code", example="EN")
    category_id: int = Field(..., description="Category ID", example=1)

    @field_validator('publication_year')
    def validate_publication_year(cls, v):
        """Validate publication year within a reasonable range"""
        if v is not None:
            current_year = datetime.now().year
            if v < 1000 or v > current_year:
                raise ValueError(f'Publication year must be between 1000 and {current_year}')
        return v

    @field_validator('isbn')
    def validate_isbn(cls, v):
        """Validation of ISBN format"""
        if v is not None:
            # Remove hyphens for validation
            clean_isbn = v.replace('-', '')
            # Check if it consists of only digits
            if not clean_isbn.isdigit():
                raise ValueError('ISBN must contain only digits (hyphens allowed)')
            # Check if it's a valid length
            if len(clean_isbn) not in [10, 13]:
                raise ValueError('ISBN must be 10 or 13 digits')
        return v


class BookCreate(BookBase):
    """Model used when creating a book"""
    initial_copies: Optional[int] = Field(0, description="Number of initial copies to create", example=1)

    @field_validator('initial_copies')
    def validate_initial_copies(cls, v):
        """Validate the number of initial copies is non-negative"""
        if v < 0:
            raise ValueError('Number of initial copies must be non-negative')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
                "call_number": "LIT-123",
                "author_id": 1,
                "publisher_id": 1,
                "publication_year": 1982,
                "language_code": "ZH",
                "category_id": 1,
                "initial_copies": 3
            }
        }


class BookUpdate(BookBase):
    """Model used when updating a book"""
    title: Optional[str] = Field(None, description="Title", example="Dream of the Red Chamber")
    isbn: Optional[str] = Field(None, description="ISBN", example="9787020002207")
    author_id: Optional[int] = Field(None, description="Author ID", example=1)
    publisher_id: Optional[int] = Field(None, description="Publisher ID", example=1)
    publication_year: Optional[int] = Field(None, description="Publication Year", example=1982)
    language_code: Optional[str] = Field(None, description="Language Code", example="EN")
    category_id: Optional[int] = Field(None, description="Category ID", example=1)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
                "call_number": "LIT-123",
                "author_id": 1,
                "publisher_id": 1,
                "publication_year": 1982,
                "language_code": "EN",
                "category_id": 1
            }
        }


class BookResponse(BookBase):
    """Model used when returning book basic information"""
    book_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes  = True
        json_schema_extra = {
            "example": {
                "book_id": 1,
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
                "call_number": "LIT-123",
                "author_id": 1,
                "publisher_id": 1,
                "publication_year": 1982,
                "language_code": "EN",
                "category_id": 1,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00"
            }
        }

class BookDetail(BookResponse):
    """Model used when returning book detailed information, including associated information"""
    author_name: str
    publisher_name: Optional[str] = None
    language_name: Optional[str] = None
    category_name: str
    available_copies: int
    total_copies: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "book_id": 1,
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
                "call_number": "LIT-123",
                "author_id": 1,
                "author_name": "Cao Xueqin",
                "publisher_id": 1,
                "publisher_name": "People's Literature Publishing House",
                "publication_year": 1982,
                "language_code": "ZH",
                "language_name": "Chinese",
                "category_id": 1,
                "category_name": "Literature",
                "available_copies": 2,
                "total_copies": 3,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00"
            }
        }

class BookSearchParams(BaseModel):
    """Parameters for advanced book search"""
    title: Optional[str] = Field(None, description="Book title (partial match)")
    isbn: Optional[str] = Field(None, description="ISBN (exact or partial match)")
    author_id: Optional[int] = Field(None, description="Author ID")
    publisher_id: Optional[int] = Field(None, description="Publisher ID")
    category_id: Optional[int] = Field(None, description="Category ID")
    language_code: Optional[str] = Field(None, description="Language code")
    publication_year: Optional[int] = Field(None, description="Publication year")
    query: Optional[str] = Field(None, description="General search query across multiple fields")
    use_or: bool = Field(False, description="Use OR logic between filters instead of AND")
    sort_by: Optional[str] = Field(None, description="Field to sort results by")
    sort_desc: bool = Field(False, description="Sort in descending order if True")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "red chamber",
                "author_id": 1,
                "category_id": 1,
                "use_or": True,
                "sort_by": "publication_year",
                "sort_desc": True
            }
        }


class BookBatchStatusUpdate(BaseModel):
    """Model for batch updating book statuses"""
    book_ids: List[int] = Field(..., description="List of book IDs to update")
    status: str = Field(..., description="New status for the books")
    notes: Optional[str] = Field(None, description="Optional notes about the status change")

    @field_validator('status')
    def validate_status(cls, v):
        """Validate book status"""
        valid_statuses = ["active", "unpublished", "removed"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "book_ids": [1, 2, 3],
                "status": "unpublished",
                "notes": "Temporarily removed for review"
            }
        }


class BookAvailabilityResponse(BaseModel):
    """Response model for book availability check"""
    book_id: int
    title: str
    isbn: Optional[str]
    total_copies: int
    available_copies: int
    is_available: bool

    class Config:
        json_schema_extra = {
            "example": {
                "book_id": 1,
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
                "total_copies": 3,
                "available_copies": 2,
                "is_available": True
            }
        }