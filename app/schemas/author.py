from pydantic import BaseModel, Field
from typing import Optional

class AuthorBase(BaseModel):
    author_name: str = Field(..., description="Author's name", example="Lu Xun")

class AuthorCreate(AuthorBase):
    pass
    
class AuthorUpdate(AuthorBase):
    pass

class AuthorResponse(AuthorBase):
    """Model used when returning author information"""
    author_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "author_id": 1,
                "author_name": "Lu Xun"
            }
        }