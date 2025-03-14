from pydantic import BaseModel, Field, validator
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
    
    @validator('publication_year')
    def validate_publication_year(cls, v):
        """Validate publication year within a reasonable range"""
        if v is not None:
            current_year = datetime.now().year
            if v < 1000 or v > current_year:
                raise ValueError(f'Publication year must be between 1000 and {current_year}')
        return v
    
    @validator('isbn')
    def validate_isbn(cls, v):
        """Simple validation of ISBN format"""
        if v is not None and not (len(v) == 10 or len(v) == 13):
            raise ValueError('ISBN must be 10 or 13 digits')
        return v

class BookCreate(BookBase):
    """Model used when creating a book"""
    pass

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
                "title": "Harry Porter",
                "isbn": "9787020002207",
                "author_id": 1,
                "publisher_id": 1,
                "publication_year": 2020,
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
                "language_code": "EN",
                "language_name": "English",
                "category_id": 1,
                "category_name": "Literature",
                "available_copies": 3,
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00"
            }
        }