from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Publisher(Base):
    __tablename__ = 'publishers'
    
    publisher_id = Column(Integer, primary_key=True)
    publisher_name = Column(String(128), nullable=False, unique=True)
    books = relationship("Book", back_populates="publisher")