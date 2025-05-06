from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.author import author_crud
from app.crud.category import category_crud
from app.crud.publisher import publisher_crud
from app.crud.language import language_crud
from app.schemas.author import AuthorCreate, AuthorResponse, AuthorUpdate
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.publisher import PublisherCreate, PublisherResponse, PublisherUpdate
from app.schemas.language import LanguageCreate, LanguageResponse, LanguageUpdate

router = APIRouter()
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('app.log')  # Save to file simultaneously
    ]
)
# Author endpoints
@router.get("/authors/", response_model=List[AuthorResponse], tags=["Metadata"])
def get_authors(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of authors.
    """
    return author_crud.get_multi(db, skip=skip, limit=limit)

@router.post("/authors/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED, tags=["Metadata"])
def create_author(
    *,
    db: Session = Depends(get_db),
    author_in: AuthorCreate,
):
    """
    Create a new author.
    """
    return author_crud.create(db=db, obj_in=author_in)



@router.get("/authors/{author_id}", response_model=AuthorResponse, tags=["Metadata"])
def get_author(
    *,
    db: Session = Depends(get_db),
    author_id: int,
):
    """
    Retrieve detailed information about an author.
    """
    db_author = author_crud.get(db, id=author_id)
    if not db_author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )
    return db_author

@router.put("/authors/{author_id}", response_model=AuthorResponse, tags=["Metadata"])
def update_author(
    *,
    db: Session = Depends(get_db),
    author_id: int,
    author_in: AuthorUpdate,
):
    """
    Update author information.
    """
    db_author = author_crud.get(db, id=author_id)
    if not db_author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )
    return author_crud.update(db=db, db_obj=db_author, obj_in=author_in)

# Category endpoints

@router.get("/categories", response_model=List[CategoryResponse], tags=["Metadata"])
def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    main_only: bool = False,
):
    """
    Retrieve a list of categories.
    
    - **main_only**: If true, returns only main categories (no parent)
    """
    if main_only:
        return category_crud.get_main_categories(db)
    return category_crud.get_multi(db, skip=skip, limit=limit)

@router.get("/categories/{category_id}/subcategories", response_model=List[CategoryResponse], tags=["Metadata"])
def get_subcategories(
    *,
    db: Session = Depends(get_db),
    category_id: int,
):
    """
    Retrieve all subcategories for a specific category.
    """
    db_category = category_crud.get(db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category_crud.get_subcategories(db, parent_id=category_id)

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, tags=["Metadata"])
def create_category(
    *,
    db: Session = Depends(get_db),
    category_in: CategoryCreate,
):
    """
    Create a new category.
    """
    return category_crud.create(db=db, obj_in=category_in)

@router.get("/categories/{category_id}", response_model=CategoryResponse, tags=["Metadata"])
def get_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
):
    """
    Retrieve detailed information about a category.
    """
    db_category = category_crud.get(db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    

    result = db_category.__dict__.copy()
    if db_category.parent:
        result["parent_name"] = db_category.parent.category_name
    
    return result

# category is fixed
# @router.put("/  /{category_id}", response_model=CategoryResponse, tags=["Metadata"])
# def update_category(
#     *,
#     db: Session = Depends(get_db),
#     category_id: int,
#     category_in: CategoryUpdate,
# ):
#     """
#     Update category information.
#     """
#     db_category = category_crud.get(db, category_id=category_id)
#     if not db_category:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Category not found"
#         )
#     return category_crud.update(db=db, db_obj=db_category, obj_in=category_in)

# Publisher endpoints
@router.get("/publishers", response_model=List[PublisherResponse], tags=["Metadata"])
def get_publishers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of publishers.
    """
    return publisher_crud.get_multi(db, skip=skip, limit=limit)

#Done
@router.post("/publishers", response_model=PublisherResponse, status_code=status.HTTP_201_CREATED, tags=["Metadata"])
def create_publisher(
    *,
    db: Session = Depends(get_db),
    publisher_in: PublisherCreate
):
    """
    Create a new publisher or return existing one.
    If publisher exists, return it.
    If not exists, create new one with auto-incremented publisher_id.
    """
    # First check if publisher already exists
    existing_publisher = publisher_crud.get_by_name(db, name=publisher_in.publisher_name)
    if existing_publisher:
        return existing_publisher
    
    # If not exists, get the max publisher_id and increment
    max_id = publisher_crud.get_max_id(db)
    new_id = (max_id or 0) + 1
    
    # Create new publisher with the incremented ID
    return publisher_crud.create_with_id(
        db=db, 
        obj_in=publisher_in, 
        publisher_id=new_id
    )
