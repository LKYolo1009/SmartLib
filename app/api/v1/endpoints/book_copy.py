from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from app.models.book_copy import BookCopy
from app.db.session import get_db
from app.crud.book_copy import book_copy_crud
from app.crud.book import book_crud
from app.schemas.book_copy import (
    BookCopyCreate,
    BookCopyResponse,
    BookCopyUpdate,
    BookCopyStatusUpdate,
    BookBorrowStatusResponse
)
import logging
import traceback

router = APIRouter()
#done
@router.get("/", response_model=List[BookCopyResponse])
def get_book_copies(
    db: Session = Depends(get_db),
    limit: int = 20,
    book_title: Optional[str] = None,
    status: Optional[str] = None,
    condition: Optional[str] = None,
    location: Optional[str] = None,  # 添加位置查询参数
):
    """
    Get all book copies with optional filtering.
    
    - **limit**: Maximum number of copies to return
    - **book_title**: Filter by book title (optional)
    - **status**: Filter by status (optional)
    - **condition**: Filter by condition (optional)
    - **location**: Filter by location (optional)
    """
    return book_copy_crud.get_copies_by_title_and_status(
        db,
        book_title=book_title,
        status=status,
        condition=condition,
        location=location,  # 添加位置参数
        limit=limit
    )
    # try:
        # return book_copy_crud.get_copies_by_title_and_status(
        #     db,
        #     book_title=book_title,
        #     status=status,
        #     condition=condition,
        #     limit=limit
        # )
    # except Exception as e:
    #     error_message = f"Error retrieving books: {str(e)}"
    #     logging.error(error_message, exc_info=True)

    #     # Return detailed error in development environment
    #     import traceback
    #     error_details = traceback.format_exc()

    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail={
    #             "message": "Failed to retrieve books",
    #             "error": str(e),
    #             "traceback": error_details.split('\n')  # Split stack trace into lines
    #         }
    #     )

@router.post("/", response_model=BookCopyResponse, status_code=status.HTTP_201_CREATED)
def create_book_copy(
    *,
    db: Session = Depends(get_db),
    book_copy_in: BookCopyCreate,
):
    """
    Create a new book copy.

    - **book_copy_in**: Book copy creation data
    """
    return book_copy_crud.create(db=db, obj_in=book_copy_in)

# Done
@router.get("/{copy_id}", response_model=BookCopyResponse)
def get_book_copy(
    *,
    db: Session = Depends(get_db),
    copy_id: int = Path(..., title="Book Copy ID"),
):
    """
    Get detailed information about a book copy.

    - **copy_id**: Copy ID
    """
    db_copy = book_copy_crud.get_with_book(db, copy_id=copy_id)
    if not db_copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found"
        )
    return db_copy

@router.put("/{copy_id}", response_model=BookCopyResponse)
def update_book_copy(
    *,
    db: Session = Depends(get_db),
    copy_id: int = Path(..., title="Book Copy ID"),
    book_copy_in: BookCopyUpdate,
):
    """
    Update book copy information.

    - **copy_id**: Copy ID
    - **book_copy_in**: Updated copy data
    """
    db_copy = book_copy_crud.get(db, copy_id=copy_id)
    if not db_copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found"
        )

    return book_copy_crud.update(db=db, db_obj=db_copy, obj_in=book_copy_in)
#done
@router.patch("/{copy_id}", response_model=BookCopyResponse)
def partial_update_book_copy(
    *,
    db: Session = Depends(get_db),
    copy_id: int = Path(..., title="Book Copy ID"),
    book_copy_in: BookCopyUpdate,
):
    """
    Partially update book copy information.
    Only the fields provided will be updated.

    - **copy_id**: Copy ID
    - **book_copy_in**: Updated copy data (only include fields that need to be updated)
    """
    db_copy = book_copy_crud.get(db, copy_id=copy_id)
    if not db_copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found"
        )

    # filter out the fields that are not provided
    update_data = book_copy_in.model_dump(exclude_unset=True)

    return book_copy_crud.update(db=db, db_obj=db_copy, obj_in=update_data)


# Done
@router.delete("/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_copy(
    *,
    db: Session = Depends(get_db),
    copy_id: int = Path(..., title="Book Copy ID"),
):
    """
    Delete a book copy. Copies that are currently borrowed cannot be deleted.

    - **copy_id**: Copy ID
    """
    db_copy = book_copy_crud.get(db, copy_id=copy_id)
    if not db_copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found"
        )

    # Check if the copy is currently borrowed
    if db_copy.status == "borrowed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a copy that is currently borrowed"
        )

    book_copy_crud.remove(db=db, id=copy_id)
    return None
"""
Endpoint for getting a book copy by QR code is temporarily disabled.
"""
@router.get("/qr-code/{qr_code}", response_model=BookCopyResponse)
def get_book_copy_by_qr_code(
    *,
    db: Session = Depends(get_db),
    qr_code: str = Path(..., title="Book QR code"),
):

    db_copy = book_copy_crud.get_by_qr_code(db, qr_code=qr_code)
    if not db_copy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found"
        )
    return db_copy


# done

# Get the borrowing status of all copies of a specific book.
@router.get("/title/{title}/status", response_model=List[BookBorrowStatusResponse])
def get_book_borrow_status_by_title(
    *,
    db: Session = Depends(get_db),
    title: str = Path(..., title="Book title"),
    exact_match: bool = False,
    limit: int = 5,
):
    """
    Get the borrowing status of all copies of a specific book.
    Returns the availability information of books that match the title.

    - **title**: Title
    - **exact_match**: Whether to match exactly
    - **limit**: Maximum number of books to return
    """


    # First get a list of books that match the title
    books = []
    if exact_match:
        books = book_crud.search_by_exact_title(db, title=title, limit=limit)
    else:
        books = book_crud.search_by_title(db, title=title, limit=limit)

    results = []
    for book in books:
        # Get all copies of this book
        book_copies = book_copy_crud.get_by_book(db, book_id=book.book_id)

        # If there are no copies, continue to the next book
        if not book_copies:
            continue

        from app.crud import borrowing as borrowing_crud

        copies_info = []
        for copy in book_copies:
            copy_info = {
                "copy_id": copy.copy_id,
                "status": copy.status,
                "condition": copy.condition,
                "location_name": copy.location.location_name if copy.location else None,  # 添加位置信息
                "borrow_info": None
            }

            if copy.status == "borrowed":
                current_borrow = borrowing_crud.get_current_by_copy(db, copy_id=copy.copy_id)
                if current_borrow:
                    copy_info["borrow_info"] = {
                        "borrow_id": current_borrow.borrow_id,
                        "student_id": current_borrow.student_id,
                        "due_date": current_borrow.due_date,
                        "is_overdue": current_borrow.due_date < datetime.now() if not current_borrow.return_date else False
                    }

            copies_info.append(copy_info)

        # Calculate counts
        total_copies = len(book_copies)
        available_copies = len([c for c in book_copies if c.status == "available"])

        results.append({
            "book_id": book.book_id,
            "title": book.title,
            "total_copies": total_copies,
            "available_copies": available_copies,
            "copies_info": copies_info
        })

    return results


@router.get("/location/{location}", response_model=List[BookCopyResponse])
def get_book_copies_by_location(
    *,
    db: Session = Depends(get_db),
    location: str = Path(..., title="Book location"),
    status: Optional[str] = None,
    condition: Optional[str] = None,
    limit: int = 50,
):
    """
    Retrieve book copies by location name.
    
    - **location**: Location name to search for (e.g., "Main Shelf A", "Reference Section")
    - **status**: Filter by status (optional)
    - **condition**: Filter by condition (optional)
    - **limit**: Maximum number of copies to return
    """
    # First find the location by name
    from app.models.book_location import BookLocation
    location_obj = db.query(BookLocation).filter(BookLocation.location_name == location).first()
    
    if not location_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location}' not found"
        )
    
    # Get copies by location_id
    return book_copy_crud.get_copies_by_title_and_status(
        db,
        location_id=location_obj.location_id,
        status=status,
        condition=condition,
        limit=limit
    )



