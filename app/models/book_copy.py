from sqlalchemy import Column, Integer, ForeignKey, Date, Text, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from .base import Base
from .enums import book_status, book_condition, acquisition_type
from datetime import datetime

class BookCopy(Base):
    __tablename__ = 'book_copies'

    copy_id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.book_id'), nullable=False)
    qr_code = Column(UUID, server_default=text("uuid_generate_v4()"))
    acquisition_type = Column(acquisition_type, nullable=False)
    acquisition_date = Column(Date, nullable=False)
    price = Column(Numeric(10,2))
    condition = Column(book_condition, server_default='good')
    status = Column(book_status, server_default='available')
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # No table args needed after moving call_number to Book model

    book = relationship("Book", back_populates="copies")
    borrowing_records = relationship("BorrowingRecord", back_populates="copy")
    # inventory_checks = relationship("InventoryCheck", back_populates="copy")