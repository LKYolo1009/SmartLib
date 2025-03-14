from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base

class Book(Base):
    __tablename__ = "books"
    
    book_id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), unique=True)
    title = Column(String(255), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.author_id"), nullable=False)
    publisher_id = Column(Integer, ForeignKey("publishers.publisher_id"))
    publication_year = Column(SmallInteger)
    language_code = Column(String(3), ForeignKey("languages.language_code"))
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    author = relationship("Author", back_populates="books")
    publisher = relationship("Publisher", back_populates="books")
    language = relationship("Language", back_populates="books")
    category = relationship("Category", back_populates="books")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")