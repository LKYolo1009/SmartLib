from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Publisher(Base):
    __tablename__ = 'publishers'
    
    # 出版社ID，主键
    publisher_id = Column(Integer, primary_key=True)
    # 出版社名称，唯一
    publisher_name = Column(String(128), nullable=False, unique=True)

    # 与Book模型的关系，一个出版社可以有多本书
    books = relationship("Book", back_populates="publisher")