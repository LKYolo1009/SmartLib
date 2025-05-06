from sqlalchemy import Column, Integer, String, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Category(Base):
    __tablename__ = 'dewey_categories'
    
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_code = Column(String(20), nullable=False, unique=True)
    category_name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('dewey_categories.category_id'), nullable=True)
    
    parent = relationship("Category", 
                        remote_side=[category_id], 
                        backref="subcategories")
    
    books = relationship("Book", back_populates="category")
    
    __table_args__ = (
        CheckConstraint(r"category_code ~ '^[0-9]{3}(\.[0-9]+)?$'", name='valid_dewey_code'),
    )