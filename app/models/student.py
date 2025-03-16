from sqlalchemy import Column, Integer, String, CheckConstraint, Index, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from .enums import student_status

class Student(Base):
    __tablename__ = 'students'
    
   
    student_id = Column(Integer, primary_key=True)
    matric_number = Column(String(20), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    status = Column(student_status, server_default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
      
        CheckConstraint("email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", 
                       name='valid_email'),
        
        CheckConstraint("matric_number ~ '^[A-Z][0-9]{7}[A-Z]$'", 
                       name='valid_matric'),
       
        Index('idx_student_status', 'status'),
    )
    
    
    borrowing_records = relationship("BorrowingRecord", back_populates="student")