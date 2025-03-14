from fastapi import APIRouter

# 确保导入所有必要的模块
# from app.api.v1 import login, author, category, inventory, language, publisher

from app.api.v1.endpoints import (
    book, book_copy, student, borrowing,library_helper, chat
)

# 只导入必要的模块，避免循环导入

# 创建主API路由器
api_router = APIRouter()

# # 添加各模块的路由
# api_router.include_router(login.router, prefix="/login", tags=["Login"])
# api_router.include_router(book.router, prefix="/books", tags=["Books"])
# api_router.include_router(book_copy.router, prefix="/book-copies", tags=["Book Copies"])
# api_router.include_router(category.router, prefix="/categories", tags=["Categories"])
# api_router.include_router(author.router, prefix="/authors", tags=["Authors"])
# api_router.include_router(publisher.router, prefix="/publishers", tags=["Publishers"])
# api_router.include_router(language.router, prefix="/languages", tags=["Languages"])
# api_router.include_router(student.router, prefix="/students", tags=["Students"])
# api_router.include_router(borrowing.router, prefix="/borrowing", tags=["Borrowing"])
# api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])


api_router.include_router(book.router, prefix="/book", tags=["Books"])
api_router.include_router(book_copy.router, prefix="/book_copy", tags=["Book Copies"])
api_router.include_router(student.router, prefix="/student", tags=["Students"])
api_router.include_router(borrowing.router, prefix="/borrowing", tags=["Borrowing"])
api_router.include_router(library_helper.router)
api_router.include_router(chat.router)