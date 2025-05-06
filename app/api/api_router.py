from fastapi import APIRouter
from app.api.v1.endpoints import book, book_copy, borrowing, student, metadata, search, health
import logging

api_router = APIRouter()

api_router.include_router(book.router, prefix="/api/v1/book", tags=["Books"])
api_router.include_router(book_copy.router, prefix="/api/v1/book_copies", tags=["Book Copies"])
api_router.include_router(borrowing.router, prefix="/api/v1/borrowing", tags=["Borrowing"])
api_router.include_router(student.router, prefix="/api/v1/student", tags=["Students"])
api_router.include_router(metadata.router, prefix="/api/v1/metadata", tags=["Metadata"])
api_router.include_router(health.router, prefix="/api/v1/health", tags=["Health"])

logging.basicConfig(level=logging.INFO)
