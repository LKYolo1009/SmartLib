from sqlalchemy import create_engine, text
import pandas as pd
from pathlib import Path
import sys

# 导入本地配置
from config import SQLALCHEMY_DATABASE_URI

def get_db_engine():
    """获取数据库引擎"""
    return create_engine(SQLALCHEMY_DATABASE_URI)

def get_borrowing_stats():
    """获取借阅统计信息"""
    engine = get_db_engine()
    query = """
    SELECT 
        COUNT(*) FILTER (WHERE status = 'borrowed') as current_borrowed,
        COUNT(*) FILTER (WHERE status = 'borrowed' AND due_date < CURRENT_TIMESTAMP) as overdue,
        COUNT(*) FILTER (WHERE borrow_date >= CURRENT_DATE - INTERVAL '30 days') as new_borrows
    FROM borrowing_records
    """
    return pd.read_sql(query, engine).iloc[0]

def get_borrowing_trend():
    """获取借阅趋势数据"""
    engine = get_db_engine()
    query = """
    SELECT 
        DATE_TRUNC('day', borrow_date) as date,
        COUNT(*) as borrow_count
    FROM borrowing_records
    WHERE borrow_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE_TRUNC('day', borrow_date)
    ORDER BY date
    """
    return pd.read_sql(query, engine)

def get_borrowing_records(search_query=None, status=None):
    """获取借阅记录"""
    engine = get_db_engine()
    query = """
    SELECT 
        br.borrow_id,
        s.matric_number,
        s.full_name,
        b.title,
        bc.call_number,
        br.borrow_date,
        br.due_date,
        br.return_date,
        br.status
    FROM borrowing_records br
    JOIN students s ON br.matric_number = s.matric_number
    JOIN book_copies bc ON br.copy_id = bc.copy_id
    JOIN books b ON bc.book_id = b.book_id
    WHERE 1=1
    """
    
    if search_query:
        query += f"""
        AND (
            s.matric_number ILIKE '%{search_query}%'
            OR s.full_name ILIKE '%{search_query}%'
            OR b.title ILIKE '%{search_query}%'
            OR bc.call_number ILIKE '%{search_query}%'
        )
        """
    
    if status and status != "全部":
        query += f" AND br.status = '{status}'"
    
    query += " ORDER BY br.borrow_date DESC"
    
    return pd.read_sql(query, engine)

def get_books(search_query=None):
    """获取图书列表"""
    engine = get_db_engine()
    query = """
    SELECT 
        b.book_id,
        b.isbn,
        b.title,
        a.author_name,
        p.publisher_name,
        b.publication_year,
        l.language_name,
        dc.category_name,
        COUNT(bc.copy_id) as total_copies,
        COUNT(bc.copy_id) FILTER (WHERE bc.status = 'available') as available_copies
    FROM books b
    JOIN authors a ON b.author_id = a.author_id
    LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
    LEFT JOIN languages l ON b.language_code = l.language_code
    JOIN dewey_categories dc ON b.category_id = dc.category_id
    LEFT JOIN book_copies bc ON b.book_id = bc.book_id
    """
    
    if search_query:
        query += f"""
        WHERE 
            b.title ILIKE '%{search_query}%'
            OR a.author_name ILIKE '%{search_query}%'
            OR b.isbn ILIKE '%{search_query}%'
        """
    
    query += " GROUP BY b.book_id, a.author_name, p.publisher_name, l.language_name, dc.category_name"
    
    return pd.read_sql(query, engine)

def get_students(search_query=None):
    """获取学生列表"""
    engine = get_db_engine()
    query = """
    SELECT 
        matric_number,
        full_name,
        email,
        status,
        created_at,
        telegram_id
    FROM students
    """
    
    if search_query:
        query += f"""
        WHERE 
            matric_number ILIKE '%{search_query}%'
            OR full_name ILIKE '%{search_query}%'
            OR email ILIKE '%{search_query}%'
        """
    
    return pd.read_sql(query, engine) 