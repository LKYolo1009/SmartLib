from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import or_

from ..models.student import Student
from ..schemas.student import StudentCreate, StudentUpdate
from ..crud.base import CRUDBase

class CRUDStudent(CRUDBase[Student, StudentCreate, StudentUpdate]):
    """Student CRUD operations class"""

    def get(self, db: Session, matric_number: str) -> Optional[Student]:
        """
        Get student by matric number
        
        Args:
            db: Database session
            matric_number: Matric number
            
        Returns:
            Student object if found, None otherwise
        """
        return db.query(Student).filter(Student.matric_number == matric_number).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[Student]:
        """
        Get student by email
        
        Args:
            db: Database session
            email: Email
            
        Returns:
            Student object if found, None otherwise
        """
        return db.query(Student).filter(Student.email == email).first()
    
    def get_student(self, db: Session, *, identifier: str) -> Optional[Student]:
        """
        Get student by matric number or email
        
        Args:
            db: Database session
            identifier: Matric number or email
            
        Returns:
            Student object if found, None otherwise
        """
        # Try to get by matric number first
        student = self.get(db, matric_number=identifier)
        if student:
            return student
        
        # Then try by email
        return self.get_by_email(db, email=identifier)
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Student]:
        """
        Get multiple students, supports pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of students
        """
        return db.query(Student).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: StudentCreate) -> Student:
        """
        Create a new student
        
        Args:
            db: Database session
            obj_in: Schema containing student data
            
        Returns:
            Created student object
            
        Raises:
            HTTPException: If matric number or email already exists
        """
        # Check if matric number already exists
        existing_matric = self.get(db, matric_number=obj_in.matric_number)
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
        self, db: Session, *, db_obj: Student, obj_in: Union[StudentUpdate, Dict[str, Any]]
    ) -> Student:
        """
        Update student information
        
        Args:
            db: Database session
            db_obj: Student object to update
            obj_in: Schema or dict containing update data
            
        Returns:
            Updated student object
            
        Raises:
            HTTPException: If matric number or email already exists
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # If update includes matric number, check if it already exists
        if "matric_number" in update_data and update_data["matric_number"] != db_obj.matric_number:
            existing_matric = self.get(db, matric_number=update_data["matric_number"])
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
        self, db: Session, *, matric_number: str, status: str
    ) -> Student:
        """
        Update student status by matric number
        
        Args:
            db: Database session
            matric_number: Matric number
            status: New status
            
        Returns:
            Updated student object
            
        Raises:
            HTTPException: If student not found or status is invalid
        """
        student = self.get(db, matric_number=matric_number)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with matric number {matric_number} not found"
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
        Search students by name, matric number, or email
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching students
        """
        return db.query(Student).filter(
            or_(
                Student.full_name.ilike(f"%{query}%"),
                Student.matric_number.ilike(f"%{query}%"),
                Student.email.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit).all()
    
    def get_active_students(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Student]:
        """
        Get active students
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active students
        """
        return db.query(Student).filter(
            Student.status == "active"
        ).offset(skip).limit(limit).all()

# Create student CRUD operations instance
student_crud = CRUDStudent(Student)