# app/models/base.py
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from app.db.base import Base

class BaseModel(Base):
    """base class for all models"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
