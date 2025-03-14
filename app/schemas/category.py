from pydantic import BaseModel, validator, Field
from typing import Optional

class CategoryBase(BaseModel):
    """分类的基本信息"""
    category_name: str = Field(..., description="分类名称", example="科学")
    category_code: str = Field(..., description="分类代码", example="SCI")
    
    @validator('category_code')
    def validate_category_code(cls, v):
        """验证分类代码格式：只能包含大写字母和数字"""
        if not v.isalnum() or not v.isupper():
            raise ValueError('分类代码必须只包含大写字母和数字')
        return v

class CategoryCreate(CategoryBase):
    """创建分类时使用的模型"""
    pass

class CategoryResponse(CategoryBase):
    """返回分类信息时使用的模型"""
    category_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "category_id": 1,
                "category_name": "科学",
                "category_code": "SCI"
            }
        }