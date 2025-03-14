from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class Author(Base):
    __tablename__ = 'authors'
    
    
    author_id = Column(Integer, primary_key=True)
    author_name = Column(String(255), nullable=False, unique=True)

   
    books = relationship("Book", back_populates="author")