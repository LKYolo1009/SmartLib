from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from .enums import book_condition

class InventoryCheck(Base):
    __tablename__ = 'inventory_checks'
    
    # 检查ID，主键
    check_id = Column(Integer, primary_key=True)
    # 图书副本ID，外键
    copy_id = Column(Integer, ForeignKey('book_copies.copy_id'), nullable=False)
    # 检查日期，默认为当前时间
    check_date = Column(DateTime(timezone=True), server_default=func.now())
    # 图书状况
    condition = Column(book_condition, nullable=False)
    # 备注
    notes = Column(Text)
    # 检查人
    checked_by = Column(String(100), nullable=False)
    
    # 定义关系
    copy = relationship("BookCopy", back_populates="inventory_checks")