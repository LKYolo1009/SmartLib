from fastapi import APIRouter
from app.api.v1.endpoints import book, student, borrowing

api_router = APIRouter()

api_router.include_router(book.router, prefix="/books", tags=["books"])
api_router.include_router(student.router, prefix="/students", tags=["students"])
api_router.include_router(borrowing.router, prefix="/borrowings", tags=["borrowings"])
