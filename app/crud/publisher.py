from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from ..models.publisher import Publisher
from .base import CRUDBase
from ..schemas.publisher import PublisherCreate

class CRUDPublisher(CRUDBase[Publisher, PublisherCreate, PublisherCreate]):
    """Publisher CRUD operation class"""

    def get(self, db: Session, publisher_id: int) -> Optional[Publisher]:
        return db.query(Publisher).filter(Publisher.publisher_id == publisher_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Publisher]:
        """Get publisher by name"""
        return db.query(Publisher).filter(Publisher.publisher_name == name).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Publisher]:
        return db.query(Publisher).offset(skip).limit(limit).all()
    
    def get_max_id(self, db: Session) -> Optional[int]:
        """Get maximum publisher_id"""
        return db.query(func.max(Publisher.publisher_id)).scalar()
    
    def create(self, db: Session, *, publisher_name: str) -> Publisher:
        existing_publisher = self.get_by_name(db, publisher_name=publisher_name)
        if existing_publisher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Publisher name already exists"
            )
        
        db_obj = Publisher(publisher_name=publisher_name)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_with_id(
        self, 
        db: Session, 
        *,
        obj_in: PublisherCreate,
        publisher_id: int
    ) -> Publisher:
        """Create new publisher with specified ID"""
        db_obj = Publisher(
            publisher_id=publisher_id,
            publisher_name=obj_in.publisher_name
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Create publisher CRUD operation instance
publisher_crud = CRUDPublisher(Publisher)
