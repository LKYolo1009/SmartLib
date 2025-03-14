from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class BookBase(BaseModel):
    """Book's Basic Information"""
    title: str = Field(..., description="Title", example="Dream of the Red Chamber")
    isbn: Optional[str] = Field(None, description="ISBN", example="9787020002207")
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
        schema_extra = {
            "example": {
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
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
        schema_extra = {
            "example": {
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
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
        orm_mode = True
        schema_extra = {
            "example": {
                "book_id": 1,
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
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
    total_copies: int  # Added to show total number of copies
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "book_id": 1,
                "title": "Dream of the Red Chamber",
                "isbn": "9787020002207",
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