from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.publisher import Publisher
from ..schemas.publisher import PublisherCreate, PublisherUpdate
from .base import CRUDBase

class CRUDPublisher(CRUDBase[Publisher, PublisherCreate, PublisherUpdate]):
    """Publisher CRUD operation class"""

    def get(self, db: Session, publisher_id: int) -> Optional[Publisher]:
        """
        Get publisher by ID
        :param db: Database session
        :param publisher_id: Publisher ID
        :return: Publisher object
        """
        return db.query(Publisher).filter(Publisher.publisher_id == publisher_id).first()
    
    def get_by_name(self, db: Session, publisher_name: str) -> Optional[Publisher]:
        """
        Get publisher by name
        :param db: Database session
        :param publisher_name: Publisher name
        :return: Publisher object
        """
        return db.query(Publisher).filter(Publisher.publisher_name == publisher_name).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Publisher]:
        """
        Get multiple publishers, supports pagination
        :param db: Database session
        :param skip: Number of records to skip
        :param limit: Maximum number of records to return
        :return: List of publishers
        """
        return db.query(Publisher).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: PublisherCreate) -> Publisher:
        """
        Create a new publisher
        :param db: Database session
        :param obj_in: Schema containing publisher data
        :return: Created publisher object
        """
        # Check if publisher name already exists
        existing_publisher = self.get_by_name(db, publisher_name=obj_in.publisher_name)
        if existing_publisher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Publisher name already exists"
            )
        
        db_obj = Publisher(
            publisher_name=obj_in.publisher_name
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Create publisher CRUD operation instance
publisher_crud = CRUDPublisher(Publisher)