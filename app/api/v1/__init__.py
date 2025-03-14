from fastapi import APIRouter

from app.api.v1.endpoints import (
    book, book_copy, student, borrowing, login, category, author, publisher, inventory
)

api_router = APIRouter()

# 添加各模块的路由
api_router.include_router(login.router, prefix="/login", tags=["登录"])
api_router.include_router(book.router, prefix="/books", tags=["图书"])
api_router.include_router(book_copy.router, prefix="/book-copies", tags=["图书副本"])
api_router.include_router(category.router, prefix="/categories", tags=["分类"])
api_router.include_router(author.router, prefix="/authors", tags=["作者"])
api_router.include_router(publisher.router, prefix="/publishers", tags=["出版社"])
api_router.include_router(student.router, prefix="/students", tags=["学生"])
api_router.include_router(borrowing.router, prefix="/borrowing", tags=["借阅"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["库存"])