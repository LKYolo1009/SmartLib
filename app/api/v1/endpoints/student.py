from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import student
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate

router = APIRouter()

@router.get("/", response_model=List[StudentResponse])
def get_students(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: str = None,
):
    """
    Retrieve a list of students, with optional filtering by status.
    """
    if status == "active":
        return student.get_active_students(db, skip=skip, limit=limit)
    return student.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    *,
    db: Session = Depends(deps.get_db),
    student_in: StudentCreate,
):
    """
    Create a new student.
    """
    return student.create(db=db, obj_in=student_in)

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
):
    """
    Retrieve detailed information about a student.
    """
    student = student.get(db, student_id=student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    student_in: StudentUpdate,
):
    """
    Update student information.
    """
    student = student.get(db, student_id=student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student.update(db=db, db_obj=student, obj_in=student_in)

@router.put("/{student_id}/status", response_model=StudentResponse)
def update_student_status(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    status: str = Query(..., description="New status"),
):
    """
    Update student status.
    """
    return student.update_status(db=db, student_id=student_id, status=status)

@router.get("/search/", response_model=List[StudentResponse])
def search_students(
    *,
    db: Session = Depends(deps.get_db),
    q: str = Query(..., min_length=1, description="Search keyword"),
    skip: int = 0,
    limit: int = 100,
):
    """
    Search for students by name, matric number, or email.
    """
    return student.search(db, query=q, skip=skip, limit=limit)