from pydantic import BaseModel, Field
from typing import Optional

class PublisherBase(BaseModel):
    """出版社的基本信息"""
    publisher_name: str = Field(..., description="出版社名称", example="人民文学出版社")

class PublisherCreate(PublisherBase):
    """创建出版社时使用的模型"""
    pass

class PublisherResponse(PublisherBase):
    """返回出版社信息时使用的模型"""
    publisher_id: int

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "publisher_id": 1,
                "publisher_name": "人民文学出版社"
            }
        }