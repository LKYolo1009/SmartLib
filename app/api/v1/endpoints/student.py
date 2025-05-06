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
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of records"),
    status: Optional[str] = Query(None, description="Filter by status: active, inactive, suspended"),
):
    """
    Retrieve all students with optional filters.
    """
    if status == "active":
        return student_crud.get_active_students(db=db, skip=skip, limit=limit)
    return student_crud.get_multi(db=db, skip=skip, limit=limit)


@router.get("/search", response_model=List[StudentResponse])
def search_students(
    *,
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=2, description="Search query (name, matric, email)"),
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of records"),
):
    """
    Search for students by name, matric number, or email.
    """
    return student_crud.search(db=db, query=query, skip=skip, limit=limit)


@router.patch("/{matric_number}", response_model=StudentResponse)
def update_student(
    *,
    db: Session = Depends(get_db),
    matric_number: str = Path(..., description="Student matric number"),
    student_in: StudentUpdate,
):
    """
    Partially update student information by matric number.
    Only the fields provided in the request will be updated.
    """
    db_student = student_crud.get(db, matric_number=matric_number)
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with matric number {matric_number} not found"
        )
    return student_crud.update(db=db, db_obj=db_student, obj_in=student_in)

