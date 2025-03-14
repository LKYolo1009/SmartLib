from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from .base import Base
from .enums import book_status, book_condition, acquisition_type

class BookCopy(Base):
    __tablename__ = 'book_copies'
    
    # 副本ID，主键
    copy_id = Column(Integer, primary_key=True)
    # 图书ID，外键
    book_id = Column(Integer, ForeignKey('books.book_id'), nullable=False)
    # 索书号，唯一
    call_number = Column(String(50), nullable=False, unique=True)
    # 二维码UUID，默认自动生成
    qr_code = Column(UUID, server_default=text("uuid_generate_v4()"))
    # 获取方式：购买/捐赠
    acquisition_type = Column(acquisition_type, nullable=False)
    # 获取日期
    acquisition_date = Column(Date, nullable=False)
    # 价格
    price = Column(Numeric(10,2))
    # 图书状况，默认为良好
    condition = Column(book_condition, server_default='good')
    # 图书状态，默认为可借阅
    status = Column(book_status, server_default='available')
    # 备注
    notes = Column(Text)
    
    __table_args__ = (
        # 确保索书号格式正确
        CheckConstraint("call_number ~ '^[A-Z0-9.-]+$'", name='valid_call_number'),
    )
    
    # 定义关系
    book = relationship("Book", back_populates="copies")
    borrowing_records = relationship("BorrowingRecord", back_populates="copy")
    inventory_checks = relationship("InventoryCheck", back_populates="copy")