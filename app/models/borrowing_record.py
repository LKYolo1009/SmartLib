from sqlalchemy import Column, Integer, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from .enums import borrow_status

class BorrowingRecord(Base):
    __tablename__ = 'borrowing_records'
    
    
    borrow_id = Column(Integer, primary_key=True)
    copy_id = Column(Integer, ForeignKey('book_copies.copy_id'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.student_id'), nullable=False)
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