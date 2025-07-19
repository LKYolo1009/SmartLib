from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.book_location import BookLocation
from app.schemas.book_location import BookLocationCreate, BookLocationUpdate

class BookLocationCRUD:
    def get(self, db: Session, location_id: int) -> Optional[BookLocation]:
        return db.query(BookLocation).filter(BookLocation.location_id == location_id).first()
    
    def get_by_location_qr_code(self, db: Session, location_qr_code: str) -> Optional[BookLocation]:
        return db.query(BookLocation).filter(BookLocation.location_qr_code == location_qr_code).first()
    
    def get_by_name(self, db: Session, location_name: str) -> Optional[BookLocation]:
        return db.query(BookLocation).filter(BookLocation.location_name == location_name).first()
    
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[BookLocation]:
        return db.query(BookLocation).offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: BookLocationCreate) -> BookLocation:
        db_obj = BookLocation(
            location_name=obj_in.location_name,
            location_description=obj_in.location_description
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: BookLocation, obj_in: BookLocationUpdate) -> BookLocation:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, location_id: int) -> BookLocation:
        obj = db.query(BookLocation).get(location_id)
        db.delete(obj)
        db.commit()
        return obj

book_location_crud = BookLocationCRUD() 