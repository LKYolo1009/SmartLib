from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class StudentStats(BaseModel):
    """学生个人统计信息"""
    total_borrowed: int
    current_borrowed: int
    overdue_count: int
    due_soon_count: int
    favorite_categories: List[str]
    favorite_authors: List[str]
    last_borrowed_date: Optional[datetime]
    
    class Config:
        from_attributes = True

class SystemStats(BaseModel):
    """系统整体统计信息"""
    total_books: int
    total_copies: int
    total_students: int
    total_borrowings: int
    active_borrowings: int
    overdue_borrowings: int
    popular_categories: List[str]
    popular_authors: List[str]
    recent_borrowings: int  # 最近30天的借阅数
    
    class Config:
        from_attributes = True 