from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.student import student_crud
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse

router = APIRouter()

# done
@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    *,
    db: Session = Depends(get_db),
    student_in: StudentCreate,
):
    """
    Create a new student.
    """
    return student_crud.create(db=db, obj_in=student_in)


@router.get("/", response_model=List[StudentResponse])
def get_students(
    *,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status: active, inactive, suspended"),
):
    """
    Retrieve all students with optional filters.
    """
    if status == "active":
        return student_crud.get_active_students(db=db)
    return student_crud.get_multi(db=db)


@router.get("/search", response_model=List[StudentResponse])
def search_students(
    *,
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=2, description="Search query (name, matric, email)"),
):
    """
    Search for students by telegram id, name, matric number or email.
    Returns up to 10 most relevant results for chatbot usage.
    """
    return student_crud.search(db=db, query=query, limit=10)


@router.patch("/{identifier}", response_model=StudentResponse)
def update_student(
    *,
    db: Session = Depends(get_db),
    identifier: str = Path(..., description="Student matric number or Telegram ID"),
    student_in: StudentUpdate,
):
    """
    Partially update student information by matric number or Telegram ID.
    Only the fields provided in the request will be updated.
    """
    # Find by matric number first
    db_student = student_crud.get(db, matric_number=identifier)
    
    # If not found, try by Telegram ID
    if not db_student:
        db_student = student_crud.get_by_telegram_id(db=db, telegram_id=identifier)
    
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with identifier {identifier} not found"
        )
    
    return student_crud.update(db=db, db_obj=db_student, obj_in=student_in)


