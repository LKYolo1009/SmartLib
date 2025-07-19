from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class BookLocation(Base):
    __tablename__ = 'book_locations'

    location_id = Column(Integer, primary_key=True)
    location_name = Column(Text, nullable=False, unique=True)
    location_description = Column(Text, nullable=True)
    location_qr_code = Column(UUID, server_default=text("uuid_generate_v4()"), unique=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship to book copies
    book_copies = relationship("BookCopy", back_populates="location") 