from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.student import Student
from ..schemas.student import StudentCreate, StudentUpdate
from ..crud.base import CRUDBase

class CRUDStudent(CRUDBase[Student, StudentCreate, StudentUpdate]):
    """Student CRUD operations class"""

    def get(self, db: Session, student_id: int) -> Optional[Student]:
        """
        Get student by ID
        :param db: Database session
        :param student_id: Student ID
        :return: Student object
        """
        return db.query(Student).filter(Student.student_id == student_id).first()
    
    def get_by_matric(self, db: Session, matric_number: str) -> Optional[Student]:
        """
        Get student by matric number
        :param db: Database session
        :param matric_number: Matric number
        :return: Student object
        """
        return db.query(Student).filter(Student.matric_number == matric_number).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[Student]:
        """
        Get student by email
        :param db: Database session
        :param email: Email
        :return: Student object
        """
        return db.query(Student).filter(Student.email == email).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Student]:
        """
        Get multiple students, supports pagination
        :param db: Database session
        :param skip: Number of records to skip
        :param limit: Maximum number of records to return
        :return: List of students
        """
        return db.query(Student).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: StudentCreate) -> Student:
        """
        Create a new student
        :param db: Database session
        :param obj_in: Schema containing student data
        :return: Created student object
        """
        # Check if matric number already exists
        existing_matric = self.get_by_matric(db, matric_number=obj_in.matric_number)
        if existing_matric:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Matric number already exists"
            )
        
        # Check if email already exists
        existing_email = self.get_by_email(db, email=obj_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        db_obj = Student(
            matric_number=obj_in.matric_number,
            full_name=obj_in.full_name,
            email=obj_in.email,
            status=obj_in.status
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: Student, obj_in: StudentUpdate
    ) -> Student:
        """
        Update student information
        :param db: Database session
        :param db_obj: Student object to update
        :param obj_in: Schema containing update data
        :return: Updated student object
        """
        update_data = obj_in.dict(exclude_unset=True)
        
        # If update includes matric number, check if it already exists
        if "matric_number" in update_data and update_data["matric_number"] != db_obj.matric_number:
            existing_matric = self.get_by_matric(db, matric_number=update_data["matric_number"])
            if existing_matric:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Matric number already exists"
                )
        
        # If update includes email, check if it already exists
        if "email" in update_data and update_data["email"] != db_obj.email:
            existing_email = self.get_by_email(db, email=update_data["email"])
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Update student information
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_status(
        self, db: Session, *, student_id: int, status: str
    ) -> Student:
        """
        Update student status
        :param db: Database session
        :param student_id: Student ID
        :param status: New status
        :return: Updated student object
        """
        student = self.get(db, student_id=student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Validate status value
        valid_statuses = ["active", "inactive", "suspended"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value, valid values are: {', '.join(valid_statuses)}"
            )
        
        student.status = status
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    
    def search(
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[Student]:
        """
        Search students
        :param db: Database session
        :param query: Search keyword
        :param skip: Number of records to skip
        :param limit: Maximum number of records to return
        :return: List of students
        """
        search_query = f"%{query}%"
        return db.query(Student).filter(
            Student.full_name.ilike(search_query) | 
            Student.matric_number.ilike(search_query) |
            Student.email.ilike(search_query)
        ).offset(skip).limit(limit).all()
    
    def get_active_students(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Student]:
        """
        Get all active students
        :param db: Database session
        :param skip: Number of records to skip
        :param limit: Maximum number of records to return
        :return: List of students
        """
        return db.query(Student).filter(
            Student.status == "active"
        ).offset(skip).limit(limit).all()

# Create student CRUD operations instance
student_crud = CRUDStudent(Student)