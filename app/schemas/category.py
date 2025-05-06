from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class CategoryBase(BaseModel):
    """Basic information of a category"""
    category_name: str = Field(..., description="Category name", example="Science")
    category_code: str = Field(..., description="Category code", example="500")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    
    @field_validator('category_code')
    def validate_category_code(cls, v):
        """Validate the category code format: must match Dewey format"""
        import re
        if not re.match(r'^[0-9]{3}(\.[0-9]+)?$', v):
            raise ValueError('Category code must be in Dewey Decimal format (e.g. 500 or 500.1)')
        return v

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    category_name: Optional[str] = None
    category_code: Optional[str] = None

class SubCategoryResponse(BaseModel):
    """Model for representing subcategories"""
    category_id: int
    category_name: str
    category_code: str

    class Config:
        orm_mode = True

class CategoryResponse(CategoryBase):
    """Model used when returning category information"""
    category_id: int
    parent_name: Optional[str] = None
    subcategories: List[SubCategoryResponse] = []
    
    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "category_id": 2,
                "category_name": "Science",
                "category_code": "500",
                "parent_id": None,
                "parent_name": None,
                "subcategories": [
                    {
                        "category_id": 5,
                        "category_name": "Theory of Science",
                        "category_code": "500.1"
                    }
                ]
            }
        }