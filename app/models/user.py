from sqlalchemy import Column, Integer, String
from app.db.session import Base

class User(Base):
    __tablename__ = 'users'
    
   
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)