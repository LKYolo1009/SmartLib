from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DailyStats(BaseModel):
    date: datetime
    total_borrows: int
    total_returns: int
    active_readers: int

class CategoryStats(BaseModel):
    category: str
    total_books: int
    available_books: int
    borrowed_books: int
    borrow_count: int

class OverdueBooks(BaseModel):
    book_id: int
    title: str
    student_id: str
    student_name: str
    due_date: datetime
    days_overdue: int

class StudentStats(BaseModel):
    student_id: str
    student_name: str
    total_borrows: int
    active_borrows: int
    overdue_count: int

class KPIMetrics(BaseModel):
    total_books: int
    total_students: int
    active_borrows: int
    overdue_books: int
    average_borrow_duration: float
    return_rate: float

class PopularBooks(BaseModel):
    book_id: int
    title: str
    author: str
    borrow_count: int
    category: str
    availability: int

    class Config:
        from_attributes = True

class BorrowingTrend(BaseModel):
    time_period: str
    total_borrows: int
    unique_readers: int
    average_duration: float
    category_distribution: Dict[str, int]
    data: List[Dict[str, Any]]

class StudentActivity(BaseModel):
    student_id: str
    student_name: str
    borrow_count: int
    favorite_category: str
    average_borrow_duration: float
    return_rate: float

class LibraryUtilization(BaseModel):
    total_books: int
    borrowed_books: int
    available_books: int
    utilization_rate: float
    daily_utilization: Dict[str, int] 