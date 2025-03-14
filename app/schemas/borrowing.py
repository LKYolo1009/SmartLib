from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class BorrowBase(BaseModel):
    """Basic information of borrowing"""
    copy_id: int = Field(..., description="Book copy ID", example=1)
    student_id: int = Field(..., description="Student ID", example=1)
    due_date: datetime = Field(..., description="Due date", example="2023-02-01T23:59:59")
    
    @field_validator('due_date')
    def validate_due_date(cls, v):
        """Validate that the due date is after the current date"""
        if v < datetime.now():
            raise ValueError('The due date must be after the current date')
        return v

class BorrowCreate(BorrowBase):
    """创建借阅记录时使用的模型"""
    pass

class BorrowUpdate(BorrowBase):
    """创建借阅记录时使用的模型"""
    pass
class BorrowResponse(BorrowBase):
    """返回借阅基本信息时使用的模型"""
    borrow_id: int
    borrow_date: datetime
    status: str
    extension_date: Optional[datetime] = None
    return_date: Optional[datetime] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "borrow_id": 1,
                "copy_id": 1,
                "student_id": 1,
                "borrow_date": "2023-01-01T12:00:00",
                "due_date": "2023-02-01T23:59:59",
                "extension_date": None,
                "return_date": None,
                "status": "borrowed"
            }
        }

class BorrowDetail(BorrowResponse):
    """返回借阅详细信息时使用的模型，包含关联信息"""
    book_title: str
    call_number: str
    student_name: str
    student_matric_number: str

# for the example of the Api doc
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "borrow_id": 1,
                "copy_id": 1,
                "student_id": 1,
                "borrow_date": "2023-01-01T12:00:00",
                "due_date": "2023-02-01T23:59:59",
                "extension_date": None,
                "return_date": None,
                "status": "borrowed",
                "book_title": "红楼梦",
                "call_number": "F12.345",
                "student_name": "张三",
                "student_matric_number": "S12345678Z"
            }
        }