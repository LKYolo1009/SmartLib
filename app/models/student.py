from sqlalchemy import Column, Integer, String, CheckConstraint, Index, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from .enums import student_status

class Student(Base):
    __tablename__ = 'students'

    matric_number = Column(String(20), primary_key=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    status = Column(student_status, server_default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    borrowing_records = relationship("BorrowingRecord", back_populates="student")

    @property
    def active_borrows_count(self):
        """Get the current number of active borrowings"""
        return sum(1 for record in self.borrowing_records if record.status == 'borrowed')

    @property
    def can_borrow(self):
        """Check if the student can borrow books"""
        return self.status != 'suspended' and self.active_borrows_count < 3

    def __repr__(self):
        return f"<Student {self.full_name} ({self.matric_number})>"

    __table_args__ = (
        # Check constraint for matric_number: A + 8 digits + 1 letter
        CheckConstraint(
            "matric_number ~ '^A[0-9]{8}[A-Za-z]$'",
            name='valid_matric'
        ),
        
        # Check constraint for email: Must end with @u.nus.edu
        CheckConstraint(
            "email ~ '^[A-Za-z0-9._%+-]+@u\.nus\.edu$'",
            name='valid_email'
        ),
        
        # Index on status for faster filtering
        Index('idx_student_status', 'status'),
    )