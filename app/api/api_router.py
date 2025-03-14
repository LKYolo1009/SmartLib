from fastapi import APIRouter


from app.api.v1.endpoints  import (
    book,
    book_copy,
    borrowing,
    student,
    metadata # New consolidated metadata router

)

api_router = APIRouter()

# Books and copies
api_router.include_router(book.router, prefix="/book", tags=["Books"])
api_router.include_router(book_copy.router, prefix="/book_copy", tags=["Book Copies"])

# Borrowing
api_router.include_router(borrowing.router, prefix="/borrowing", tags=["Borrowing"])

# Students
api_router.include_router(student.router, prefix="/student", tags=["Students"])

# Metadata (consolidated from author, category, publisher, language)
api_router.include_router(metadata.router, prefix="/metadata", tags=["Metadata"])
