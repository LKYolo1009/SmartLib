from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.orm import relationship
from .base import Base

class Category(Base):
    __tablename__ = 'categories'
    
    # 分类ID，主键
    category_id = Column(Integer, primary_key=True)
    # 分类名称
    category_name = Column(String(100), nullable=False)
    # 分类代码，唯一
    category_code = Column(String(20), nullable=False, unique=True)
    
    __table_args__ = (
        # 确保分类代码只包含大写字母和数字
        CheckConstraint("category_code ~ '^[A-Z0-9]+$'", name='valid_category_code'),
    )
    
    # 与Book模型的关系，一个分类可以有多本书
    books = relationship("Book", back_populates="category")