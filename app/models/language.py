from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base

class Language(Base):
    __tablename__ = "languages"
    
    language_code = Column(String(3), primary_key=True)
    language_name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    
    books = relationship("Book", back_populates="language")