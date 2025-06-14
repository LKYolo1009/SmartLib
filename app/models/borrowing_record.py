from sqlalchemy import Column, Integer, ForeignKey, DateTime, CheckConstraint, Index, Text, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from sqlalchemy import event, text
from .base import Base
from .enums import borrow_status

class BorrowingRecord(Base):
    __tablename__ = 'borrowing_records'
    
    borrow_id = Column(Integer, primary_key=True)
    copy_id = Column(Integer, ForeignKey('book_copies.copy_id'), nullable=False)
    matric_number = Column(String(20), ForeignKey('students.matric_number'), nullable=False)
    borrow_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    extension_date = Column(DateTime(timezone=True))
    return_date = Column(DateTime(timezone=True))
    status = Column(borrow_status, server_default='borrowed')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        # Ensure date logic is correct
        CheckConstraint("borrow_date <= due_date", name='valid_dates'),
        CheckConstraint("extension_date IS NULL OR extension_date > due_date", 
                      name='valid_extension'),
        CheckConstraint("return_date IS NULL OR return_date >= borrow_date", 
                      name='valid_return'),
        # Create indexes for status and due date to improve query performance
        Index('idx_borrowing_status', 'status'),
        Index('idx_borrowing_due_date', 'due_date'),
    )
    
    copy = relationship("BookCopy", back_populates="borrowing_records")
    student = relationship("Student", back_populates="borrowing_records")

    @validates('status')
    def validate_status(self, key, status):
        if status not in ['borrowed', 'returned']:
            raise ValueError("Status must be either 'borrowed' or 'returned'")
    
        
        return status

    @validates('matric_number')
    def validate_matric_number(self, key, matric_number):
        if not matric_number:
            raise ValueError("Matriculation number is required")
        if not matric_number.startswith('A') or len(matric_number) != 9 or not matric_number[1:8].isdigit() or not matric_number[8].isalpha():
            raise ValueError("Invalid matriculation number format. Must be A followed by 7 digits and 1 letter (e.g., A1234567B)")
        return matric_number

    @validates('due_date')
    def validate_due_date(self, key, due_date):
        if not due_date:
            raise ValueError("Due date is required")
        if self.borrow_date and due_date < self.borrow_date:
            raise ValueError("Due date cannot be earlier than borrow date")
        return due_date
