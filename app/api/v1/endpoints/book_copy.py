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
):
        
        return book_copy_crud.get_copies_by_title_and_status(
        db, 
        book_title=book_title,
        status=status,
        condition=condition,
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
    update_data = book_copy_in.dict(exclude_unset=True)
    
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
# Done
@router.get("/call-number/{call_number}", response_model=List[BookCopyResponse])
def get_book_copy_by_call_number(
    *,
    db: Session = Depends(get_db),
    call_number: str = Path(..., title="Book call number"),
):
    try:
        # Use joinedload to load related book information and return all matching records
        db_copies = db.query(BookCopy).options(
            joinedload(BookCopy.book)
        ).filter(
            BookCopy.call_number == call_number
        ).all()
        
        if not db_copies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No book copies found with call number: {call_number}"
            )
        
        # Add book_title attribute for each copy and convert UUID to string
        for db_copy in db_copies:
            if db_copy.book:
                setattr(db_copy, "book_title", db_copy.book.title)
            
            # Ensure qr_code is a string
            if db_copy.qr_code is not None:
                db_copy.qr_code = str(db_copy.qr_code)
        
        return db_copies  # Return the list
        
    except Exception as e:
        # Return detailed error in development environment
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to retrieve book copies",
                "error": str(e),
                "traceback": error_details.split('\n')  # Split stack trace into lines
            }
        )
"""
Endpoint for getting a book copy by QR code is temporarily disabled.
"""
# @router.get("/qr-code/{qr_code}", response_model=BookCopyResponse)
# def get_book_copy_by_qr_code(
#     *,
#     db: Session = Depends(get_db),
#     qr_code: str = Path(..., title="Book QR code"),
# ):

#     db_copy = book_copy_crud.get_by_qr_code(db, qr_code=qr_code)
#     if not db_copy:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Book copy not found"
#         )
#     return db_copy


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
                "call_number": copy.call_number,
                "status": copy.status,
                "condition": copy.condition,
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
        
        available_copies = sum(1 for copy in book_copies if copy.status == "available")
        
        results.append({
            "book_id": book.book_id,
            "title": book.title,
            "total_copies": len(book_copies),
            "available_copies": available_copies,
            "copies_info": copies_info
        })
    
    return results
