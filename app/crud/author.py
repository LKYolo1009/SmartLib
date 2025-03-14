from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.author import Author
from .base import CRUDBase

class CRUDAuthor(CRUDBase[Author, str, str]):
    """Author CRUD operation class"""

    def get(self, db: Session, author_id: int) -> Optional[Author]:
        return db.query(Author).filter(Author.author_id == author_id).first()
    
    def get_by_name(self, db: Session, author_name: str) -> Optional[Author]:
        return db.query(Author).filter(Author.author_name == author_name).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Author]:
        return db.query(Author).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, author_name: str) -> Author:
        existing_author = self.get_by_name(db, author_name=author_name)
        if existing_author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Author name already exists"
            )
        
        db_obj = Author(author_name=author_name)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Create author CRUD operation instance
author_crud = CRUDAuthor(Author)