from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.category import Category
from ..schemas.category import CategoryCreate, CategoryUpdate
from .base import CRUDBase

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    
    def get(self, db: Session, category_id: int) -> Optional[Category]:
        return db.query(Category).filter(Category.category_id == category_id).first()
    
    def get_by_code(self, db: Session, category_code: str) -> Optional[Category]:
        return db.query(Category).filter(Category.category_code == category_code).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """
        Get multiple categories
        """
        return db.query(Category).offset(skip).limit(limit).all()
    
    def get_main_categories(self, db: Session) -> List[Category]:
        """
        Get main categories (categories without a parent)
        """
        return db.query(Category).filter(Category.parent_id.is_(None)).all()
    
    def get_subcategories(self, db: Session, parent_id: int) -> List[Category]:
        """Get all subcategories for a given parent"""
        return db.query(Category).filter(Category.parent_id == parent_id).all()
    
    def create(self, db: Session, *, obj_in: CategoryCreate) -> Category:
        existing_category = self.get_by_code(db, category_code=obj_in.category_code)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category code already exists"
            )
        
        # Validate parent_id if provided
        if obj_in.parent_id is not None:
            parent_category = self.get(db, category_id=obj_in.parent_id)
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with ID {obj_in.parent_id} does not exist"
                )
        
        db_obj = Category(
            category_name=obj_in.category_name,
            category_code=obj_in.category_code,
            parent_id=obj_in.parent_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: Category, obj_in: CategoryUpdate
    ) -> Category:
        obj_data = obj_in.dict(exclude_unset=True)
        
        # Check if category_code is being updated and validate uniqueness
        if "category_code" in obj_data and obj_data["category_code"] != db_obj.category_code:
            existing = self.get_by_code(db, category_code=obj_data["category_code"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category code already exists"
                )
        
        # Validate parent_id if provided
        if "parent_id" in obj_data and obj_data["parent_id"] is not None:
            # Prevent circular references
            if obj_data["parent_id"] == db_obj.category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A category cannot be its own parent"
                )
            
            parent_category = self.get(db, category_id=obj_data["parent_id"])
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Parent category with ID {obj_data['parent_id']} does not exist"
                )
        
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

category_crud = CRUDCategory(Category)