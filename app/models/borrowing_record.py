from sqlalchemy import Column, Integer, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from .enums import borrow_status

class BorrowingRecord(Base):
    __tablename__ = 'borrowing_records'
    
    # 借阅ID，主键
    borrow_id = Column(Integer, primary_key=True)
    # 图书副本ID，外键
    copy_id = Column(Integer, ForeignKey('book_copies.copy_id'), nullable=False)
    # 学生ID，外键
    student_id = Column(Integer, ForeignKey('students.student_id'), nullable=False)
    # 借阅日期，默认为当前时间
    borrow_date = Column(DateTime(timezone=True), server_default=func.now())
    # 应还日期
    due_date = Column(DateTime(timezone=True), nullable=False)
    # 续借日期（可为空）
    extension_date = Column(DateTime(timezone=True))
    # 归还日期（可为空）
    return_date = Column(DateTime(timezone=True))
    # 借阅状态，默认为已借出
    status = Column(borrow_status, server_default='borrowed')
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 更新时间
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        # 确保日期逻辑正确
        CheckConstraint("borrow_date <= due_date", name='valid_dates'),
        CheckConstraint("extension_date IS NULL OR extension_date > due_date", 
                      name='valid_extension'),
        CheckConstraint("return_date IS NULL OR return_date >= borrow_date", 
                      name='valid_return'),
        # 创建状态和到期日索引以提高查询性能
        Index('idx_borrowing_status', 'status'),
        Index('idx_borrowing_due_date', 'due_date'),
    )
    
    # 定义关系
    copy = relationship("BookCopy", back_populates="borrowing_records")
    student = relationship("Student", back_populates="borrowing_records")