from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json

from . import book, book_copy, student, borrowing, schemas, library_helper
from .database import get_db

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    actions: Optional[List[Dict[str, Any]]] = None

@router.post("/", response_model=ChatResponse)
def process_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    处理来自聊天界面的消息。
    - 分析用户意图
    - 提取关键实体
    - 执行相应操作
    - 返回自然语言响应
    """
    # 在实际实现中，这里会使用NLP模型分析用户意图
    # 这里提供一个简化的示例实现
    
    message = request.message.lower()
    
    # 提取意图 (简化版)
    intent = "unknown"
    if any(word in message for word in ["add", "new", "create"]) and "book" in message:
        intent = "add_book"
    elif "borrow" in message:
        intent = "borrow_book"
    elif "return" in message:
        intent = "return_book"
    elif any(word in message for word in ["find", "search", "looking for"]):
        intent = "search_book"
    elif "availability" in message or "available" in message:
        intent = "check_availability"
    
    # 基于意图处理
    if intent == "add_book":
        # 这里应该启动一个对话流程来收集书籍信息
        # 简化示例:
        return {
            "response": "I can help you add a new book. Please provide the following information:\n"
                        "- Title\n"
                        "- Author\n"
                        "- ISBN (optional)\n"
                        "- Category (optional)",
            "actions": [{
                "type": "start_flow",
                "flow": "add_book"
            }]
        }
    
    elif intent == "search_book":
        # 提取可能的书名 (简化)
        # 实际实现应该使用更复杂的NER
        possible_title = extract_quoted_text(message)
        if possible_title:
            try:
                # 搜索书籍
                books = book.search_books_by_title(db, title=possible_title)
                if books:
                    book_list = "\n".join([f"- {b.title} by {b.author}" for b in books[:5]])
                    return {
                        "response": f"I found these books matching '{possible_title}':\n{book_list}",
                        "actions": [{
                            "type": "show_books",
                            "books": [{"id": b.id, "title": b.title, "author": b.author} for b in books[:5]]
                        }]
                    }
                else:
                    return {
                        "response": f"I couldn't find any books matching '{possible_title}'. Would you like to add it as a new book?",
                        "actions": None
                    }
            except Exception as e:
                return {
                    "response": f"Sorry, I encountered an error while searching: {str(e)}",
                    "actions": None
                }
        else:
            return {
                "response": "What book are you looking for? Please provide a title.",
                "actions": None
            }
    
    # 其他意图处理...
    
    return {
        "response": "I'm still learning how to help with library management. Could you rephrase or provide more details?",
        "actions": None
    }

# 用于管理员添加图书的对话流程API
@router.post("/flow/add-book", response_model=ChatResponse)
def add_book_flow(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    处理添加图书的对话流程。
    这是一个多步骤流程的一部分，用于收集所有必要的书籍信息。
    """
    step = data.get("step", 1)
    session_data = data.get("session_data", {})
    
    if step == 1:
        # 收集书名
        title = data.get("message", "").strip()
        if not title:
            return {
                "response": "Please provide the title of the book you want to add.",
                "actions": [{"type": "continue_flow", "flow": "add_book", "step": 1}]
            }
        
        session_data["title"] = title
        return {
            "response": f"Title: {title}\nNow, please provide the author's name.",
            "actions": [{"type": "continue_flow", "flow": "add_book", "step": 2, "session_data": session_data}]
        }
    
    elif step == 2:
        # 收集作者
        author = data.get("message", "").strip()
        if not author:
            return {
                "response": "Please provide the author's name.",
                "actions": [{"type": "continue_flow", "flow": "add_book", "step": 2, "session_data": session_data}]
            }
        
        session_data["author"] = author
        return {
            "response": f"Author: {author}\nPlease provide the ISBN (or type 'skip' if not available).",
            "actions": [{"type": "continue_flow", "flow": "add_book", "step": 3, "session_data": session_data}]
        }
    
    elif step == 3:
        # 收集ISBN
        isbn = data.get("message", "").strip()
        if isbn.lower() == "skip":
            isbn = None
        
        session_data["isbn"] = isbn
        return {
            "response": f"ISBN: {isbn or 'Not provided'}\nPlease provide the category (or type 'skip').",
            "actions": [{"type": "continue_flow", "flow": "add_book", "step": 4, "session_data": session_data}]
        }
    
    elif step == 4:
        # 收集类别
        category = data.get("message", "").strip()
        if category.lower() == "skip":
            category = "General"
        
        session_data["category"] = category
        return {
            "response": f"Category: {category}\nHow many copies would you like to add? (Default: 1)",
            "actions": [{"type": "continue_flow", "flow": "add_book", "step": 5, "session_data": session_data}]
        }
    
    elif step == 5:
        # 收集副本数量
        copies_str = data.get("message", "").strip()
        try:
            copies = int(copies_str) if copies_str else 1
        except ValueError:
            copies = 1
        
        session_data["copies"] = copies
        
        # 准备确认信息
        confirm_message = f"Please confirm the following information:\n"
        confirm_message += f"- Title: {session_data.get('title')}\n"
        confirm_message += f"- Author: {session_data.get('author')}\n"
        confirm_message += f"- ISBN: {session_data.get('isbn') or 'Not provided'}\n"
        confirm_message += f"- Category: {session_data.get('category')}\n"
        confirm_message += f"- Copies: {copies}\n\n"
        confirm_message += "Type 'confirm' to add this book or 'cancel' to abort."
        
        return {
            "response": confirm_message,
            "actions": [{"type": "continue_flow", "flow": "add_book", "step": 6, "session_data": session_data}]
        }
    
    elif step == 6:
        # 确认并添加
        confirmation = data.get("message", "").strip().lower()
        if confirmation != "confirm":
            return {
                "response": "Book addition cancelled.",
                "actions": None
            }
        
        try:
            # 创建书籍对象
            book_data = schemas.BookCreate(
                title=session_data.get("title"),
                author=session_data.get("author"),
                isbn=session_data.get("isbn"),
                category=session_data.get("category")
            )
            
            # 添加书籍和副本
            result = library_helper.add_new_book(
                book_data=book_data,
                initial_copies=session_data.get("copies", 1),
                db=db
            )
            
            # 构建响应
            call_numbers = [copy.call_number for copy in result.copies]
            call_numbers_str = ", ".join(call_numbers)
            
            return {
                "response": f"Successfully added '{result.book.title}' with {len(result.copies)} copies.\n"
                            f"Call numbers: {call_numbers_str}",
                "actions": [{
                    "type": "book_added",
                    "book_id": result.book.id,
                    "copies": len(result.copies)
                }]
            }
            
        except Exception as e:
            return {
                "response": f"Error adding book: {str(e)}",
                "actions": None
            }
    
    return {
        "response": "Unknown step in the add book flow.",
        "actions": None
    }

# 辅助函数
def extract_quoted_text(text):
    """从文本中提取引号内的内容"""
    import re
    match = re.search(r'"([^"]*)"', text)
    if match:
        return match.group(1)
    
    match = re.search(r"'([^']*)'", text)
    if match:
        return match.group(1)
    
    # 如果没有引号，尝试找到关键词后的文本
    keywords = ["titled", "called", "named", "book", "for"]
    for keyword in keywords:
        pattern = f"{keyword}\\s+([\\w\\s]+)(?:\\s|$|\\?|\\.|,)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None