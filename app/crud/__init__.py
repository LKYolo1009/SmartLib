# app/crud/__init__.py
from app.models.author import Author
from app.models.book import Book
from app.models.book_copy import BookCopy
from app.models.category import Category
from app.models.language import Language
from app.models.publisher import Publisher
from app.models.student import Student
from app.models.borrowing_record import BorrowingRecord
from app.models.inventory_check import InventoryCheck
from app.models.user import User

# 方便其他模块从crud包导入所有模型
__all__ = [
    "Author", "Book", "BookCopy", "Category", "Language",
    "Publisher", "Student", "BorrowingRecord", "InventoryCheck", "User"
]