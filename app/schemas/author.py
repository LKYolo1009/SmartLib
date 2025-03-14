from pydantic import BaseModel, Field
from typing import Optional

class AuthorBase(BaseModel):
    """作者的基本信息"""
    author_name: str = Field(..., description="作者姓名", example="鲁迅")

class AuthorCreate(AuthorBase):
    """创建作者时使用的模型"""
    pass

class AuthorResponse(AuthorBase):
    """返回作者信息时使用的模型"""
    author_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "author_id": 1,
                "author_name": "鲁迅"
            }
        }