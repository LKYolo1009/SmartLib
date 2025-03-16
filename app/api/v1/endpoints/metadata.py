from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import author as author_crud
from app.crud import category as category_crud
from app.crud import publisher as publisher_crud
from app.crud import language as language_crud
from app.schemas.author import AuthorCreate, AuthorResponse, AuthorUpdate
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.publisher import PublisherCreate, PublisherResponse, PublisherUpdate
from app.schemas.language import LanguageCreate, LanguageResponse, LanguageUpdate

router = APIRouter()

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
@router.get("/categories/", response_model=List[CategoryResponse], tags=["Metadata"])
def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of categories.
    """
    return category_crud.get_multi(db, skip=skip, limit=limit)

@router.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, tags=["Metadata"])
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
    db_category = category_crud.get(db, id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return db_category

@router.put("/categories/{category_id}", response_model=CategoryResponse, tags=["Metadata"])
def update_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    category_in: CategoryUpdate,
):
    """
    Update category information.
    """
    db_category = category_crud.get(db, id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category_crud.update(db=db, db_obj=db_category, obj_in=category_in)

# Publisher endpoints
@router.get("/publishers/", response_model=List[PublisherResponse], tags=["Metadata"])
def get_publishers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of publishers.
    """
    return publisher_crud.get_multi(db, skip=skip, limit=limit)

@router.post("/publishers/", response_model=PublisherResponse, status_code=status.HTTP_201_CREATED, tags=["Metadata"])
def create_publisher(
    *,
    db: Session = Depends(get_db),
    publisher_in: PublisherCreate,
):
    """
    Create a new publisher.
    """
    return publisher_crud.create(db=db, obj_in=publisher_in)

@router.get("/publishers/{publisher_id}", response_model=PublisherResponse, tags=["Metadata"])
def get_publisher(
    *,
    db: Session = Depends(get_db),
    publisher_id: int,
):
    """
    Retrieve detailed information about a publisher.
    """
    db_publisher = publisher_crud.get(db, id=publisher_id)
    if not db_publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    return db_publisher

@router.put("/publishers/{publisher_id}", response_model=PublisherResponse, tags=["Metadata"])
def update_publisher(
    *,
    db: Session = Depends(get_db),
    publisher_id: int,
    publisher_in: PublisherUpdate,
):
    """
    Update publisher information.
    """
    db_publisher = publisher_crud.get(db, id=publisher_id)
    if not db_publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found"
        )
    return publisher_crud.update(db=db, db_obj=db_publisher, obj_in=publisher_in)

# Language endpoints
@router.get("/languages/", response_model=List[LanguageResponse], tags=["Metadata"])
def get_languages(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of languages.
    """
    return language_crud.get_multi(db, skip=skip, limit=limit)

@router.post("/languages/", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED, tags=["Metadata"])
def create_language(
    *,
    db: Session = Depends(get_db),
    language_in: LanguageCreate,
):
    """
    Create a new language.
    """
    return language_crud.create(db=db, obj_in=language_in)

@router.get("/languages/{language_id}", response_model=LanguageResponse, tags=["Metadata"])
def get_language(
    *,
    db: Session = Depends(get_db),
    language_id: int,
):
    """
    Retrieve detailed information about a language.
    """
    db_language = language_crud.get(db, id=language_id)
    if not db_language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    return db_language

@router.put("/languages/{language_id}", response_model=LanguageResponse, tags=["Metadata"])
def update_language(
    *,
    db: Session = Depends(get_db),
    language_id: int,
    language_in: LanguageUpdate,
):
    """
    Update language information.
    """
    db_language = language_crud.get(db, id=language_id)
    if not db_language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    return language_crud.update(db=db, db_obj=db_language, obj_in=language_in)