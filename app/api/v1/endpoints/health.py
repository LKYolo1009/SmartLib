from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()

@router.get("/database")
def check_database(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        database_name = db.execute(text("SELECT current_database()")).scalar()
        schema_name = db.execute(text("SELECT current_schema()")).scalar()
        return {"status": "ok", "message": "Database connection successful", "database_name": database_name, "schema_name": schema_name}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/details")
def database_details(db: Session = Depends(get_db)):
    try:
        version = db.execute(text("SELECT version()")).scalar()
        books_count = db.execute(text("SELECT COUNT(*) FROM books")).scalar()
        copies_count = db.execute(text("SELECT COUNT(*) FROM book_copies")).scalar()
        students_count = db.execute(text("SELECT COUNT(*) FROM students")).scalar()
        borrowings_count = db.execute(text("SELECT COUNT(*) FROM borrowing_records")).scalar()
        
        return {
            "status": "ok",
            "database_version": version,
            "stats": {
                "books_count": books_count,
                "copies_count": copies_count,
                "students_count": students_count,
                "borrowings_count": borrowings_count
            }
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
