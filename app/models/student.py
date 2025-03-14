from sqlalchemy import Column, Integer, String, CheckConstraint, Index, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from .enums import student_status

class Student(Base):
    __tablename__ = 'students'
    
    # 学生ID，主键
    student_id = Column(Integer, primary_key=True)
    # 学号，唯一
    matric_number = Column(String(20), nullable=False, unique=True)
    # 学生全名
    full_name = Column(String(255), nullable=False)
    # 邮箱，唯一
    email = Column(String(255), nullable=False, unique=True)
    # 学生状态，默认为活跃
    status = Column(student_status, server_default='active')
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        # 确保邮箱格式正确
        CheckConstraint("email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", 
                       name='valid_email'),
        # 确保学号格式正确（1个大写字母 + 7位数字 + 1个大写字母）
        CheckConstraint("matric_number ~ '^[A-Z][0-9]{7}[A-Z]$'", 
                       name='valid_matric'),
        # 创建状态索引以提高查询性能
        Index('idx_student_status', 'status'),
    )
    
    # 定义关系
    borrowing_records = relationship("BorrowingRecord", back_populates="student")