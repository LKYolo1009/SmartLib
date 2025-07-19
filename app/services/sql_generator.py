#!/usr/bin/env python3
"""
SQL查询生成器 (SQL Query Generator)
将NLU结果转换为SQL查询语句
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SQLQueryGenerator:
    """SQL查询生成器"""
    
    def __init__(self):
        self.sql_templates = self._load_sql_templates()
        self.filter_builders = self._load_filter_builders()
    
    def _load_sql_templates(self) -> Dict[str, str]:
        """加载SQL模板"""
        return {
            "query_book_inventory": """
                SELECT 
                    bc.copy_id,
                    b.title,
                    a.author_name,
                    c.category_name,
                    bc.status,
                    bc.condition,
                    bc.call_number,
                    bc.shelf_location
                FROM book_copies bc
                JOIN books b ON bc.book_id = b.book_id
                JOIN authors a ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                WHERE 1=1
                {book_title_filter}
                {status_filter}
                {condition_filter}
                ORDER BY b.title
                LIMIT {limit}
            """,
            
            "query_book_by_title": """
                SELECT 
                    bc.copy_id,
                    b.book_id,
                    b.title,
                    a.author_name,
                    c.category_name,
                    bc.status,
                    bc.condition,
                    bc.call_number,
                    bc.shelf_location
                FROM book_copies bc
                JOIN books b ON bc.book_id = b.book_id
                JOIN authors a ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                WHERE b.title ILIKE '%{book_title}%'
                {status_filter}
                {condition_filter}
                ORDER BY b.title
                LIMIT {limit}
            """,
            
            "query_book_by_author": """
                SELECT DISTINCT
                    b.book_id,
                    b.title,
                    a.author_name,
                    c.category_name,
                    b.publication_year,
                    COUNT(bc.copy_id) as total_copies,
                    COUNT(CASE WHEN bc.status = 'available' THEN 1 END) as available_copies
                FROM books b
                JOIN authors a ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                WHERE a.author_name ILIKE '%{author_name}%'
                {category_filter}
                GROUP BY b.book_id, b.title, a.author_name, c.category_name, b.publication_year
                ORDER BY b.title
                LIMIT {limit}
            """,
            
            "query_book_by_category": """
                SELECT DISTINCT
                    b.book_id,
                    b.title,
                    a.author_name,
                    c.category_name,
                    b.publication_year,
                    COUNT(bc.copy_id) as total_copies,
                    COUNT(CASE WHEN bc.status = 'available' THEN 1 END) as available_copies
                FROM books b
                JOIN authors a ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                LEFT JOIN book_copies bc ON b.book_id = bc.book_id
                WHERE c.category_name ILIKE '%{category_name}%'
                {author_filter}
                GROUP BY b.book_id, b.title, a.author_name, c.category_name, b.publication_year
                ORDER BY b.title
                LIMIT {limit}
            """,
            
            "query_borrowing_records": """
                SELECT 
                    br.borrow_id,
                    s.full_name as student_name,
                    s.matric_number,
                    b.title as book_title,
                    a.author_name,
                    c.category_name,
                    br.borrow_date,
                    br.due_date,
                    br.return_date,
                    br.status
                FROM borrowing_records br
                JOIN students s ON br.student_id = s.student_id
                JOIN book_copies bc ON br.copy_id = bc.copy_id
                JOIN books b ON bc.book_id = b.book_id
                JOIN authors a ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                WHERE 1=1
                {student_filter}
                {book_title_filter}
                {author_filter}
                {category_filter}
                {date_range_filter}
                {status_filter}
                ORDER BY br.borrow_date DESC
                LIMIT {limit}
            """,
            
            "query_student_borrowing": """
                SELECT 
                    br.borrow_id,
                    s.full_name as student_name,
                    s.matric_number,
                    b.title as book_title,
                    a.author_name,
                    br.borrow_date,
                    br.due_date,
                    br.return_date,
                    br.status,
                    CASE 
                        WHEN br.return_date IS NULL AND br.due_date < CURRENT_DATE 
                        THEN 'overdue'
                        ELSE br.status::text
                    END as computed_status
                FROM borrowing_records br
                JOIN students s ON br.student_id = s.student_id
                JOIN book_copies bc ON br.copy_id = bc.copy_id
                JOIN books b ON bc.book_id = b.book_id
                JOIN authors a ON b.author_id = a.author_id
                WHERE (s.matric_number = '{student_id}' OR s.full_name ILIKE '%{student_id}%')
                {date_range_filter}
                {status_filter}
                ORDER BY br.borrow_date DESC
                LIMIT {limit}
            """,
            
            "query_statistics": """
                SELECT 
                    'popular_books' as metric_type,
                    b.title,
                    a.author_name,
                    c.category_name,
                    COUNT(br.borrow_id) as borrow_count,
                    COUNT(DISTINCT s.student_id) as unique_borrowers
                FROM borrowing_records br
                JOIN book_copies bc ON br.copy_id = bc.copy_id
                JOIN books b ON bc.book_id = b.book_id
                JOIN authors a ON b.author_id = a.author_id
                JOIN categories c ON b.category_id = c.category_id
                JOIN students s ON br.student_id = s.student_id
                WHERE 1=1
                {date_range_filter}
                {book_title_filter}
                {author_filter}
                {category_filter}
                GROUP BY b.book_id, b.title, a.author_name, c.category_name
                ORDER BY borrow_count DESC
                LIMIT {limit}
            """,
            
            "query_overdue_books": """
                SELECT 
                    br.borrow_id,
                    s.full_name as student_name,
                    s.matric_number,
                    b.title as book_title,
                    a.author_name,
                    br.borrow_date,
                    br.due_date,
                    CURRENT_DATE - br.due_date::date as days_overdue,
                    bc.call_number
                FROM borrowing_records br
                JOIN students s ON br.student_id = s.student_id
                JOIN book_copies bc ON br.copy_id = bc.copy_id
                JOIN books b ON bc.book_id = b.book_id
                JOIN authors a ON b.author_id = a.author_id
                WHERE br.status = 'borrowed'
                AND br.due_date < CURRENT_DATE
                AND br.return_date IS NULL
                {date_range_filter}
                ORDER BY br.due_date ASC
                LIMIT {limit}
            """
        }
    
    def _load_filter_builders(self) -> Dict[str, callable]:
        """加载过滤器构建函数"""
        return {
            "book_title_filter": self._build_book_title_filter,
            "author_filter": self._build_author_filter,
            "category_filter": self._build_category_filter,
            "student_filter": self._build_student_filter,
            "status_filter": self._build_status_filter,
            "condition_filter": self._build_condition_filter,
            "date_range_filter": self._build_date_range_filter,
        }
    
    def _build_book_title_filter(self, entities: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建书名过滤条件"""
        book_title = entities.get("book_title") or params.get("book_title")
        if book_title:
            return f"AND b.title ILIKE '%{book_title}%'"
        return ""
    
    def _build_author_filter(self, entities: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建作者过滤条件"""
        author_name = entities.get("author_name") or params.get("author_name")
        if author_name:
            return f"AND a.author_name ILIKE '%{author_name}%'"
        return ""
    
    def _build_category_filter(self, entities: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建类别过滤条件"""
        category_name = entities.get("category_name") or params.get("category_name")
        if category_name:
            return f"AND c.category_name ILIKE '%{category_name}%'"
        return ""
    
    def _build_student_filter(self, entities: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建学生过滤条件"""
        student_id = entities.get("student_id") or params.get("student_id")
        if student_id:
            return f"AND (s.matric_number = '{student_id}' OR s.full_name ILIKE '%{student_id}%')"
        return ""
    
    def _build_status_filter(self, entities: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建状态过滤条件"""
        status = entities.get("status") or params.get("status")
        if status:
            # 根据上下文决定是图书状态还是借阅状态
            if status in ["available", "borrowed", "missing"]:
                return f"AND bc.status = '{status}'"
            elif status in ["returned", "overdue"]:
                return f"AND br.status = '{status}'"
        return ""
    
    def _build_condition_filter(self, entities: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建条件过滤"""
        condition = entities.get("condition") or params.get("condition")
        if condition:
            return f"AND bc.condition = '{condition}'"
        return ""
    
    def _build_date_range_filter(self, entities: Dict[str, Any], params: Dict[str, Any]) -> str:
        """构建日期范围过滤条件"""
        # 检查时间范围
        time_range = entities.get("time_range") or params.get("time_range")
        if time_range:
            start_date, end_date = self._convert_time_range(time_range)
            return f"AND br.borrow_date BETWEEN '{start_date}' AND '{end_date}'"
        
        # 检查具体日期
        date = entities.get("date") or params.get("date")
        if date:
            return f"AND DATE(br.borrow_date) = '{date}'"
        
        # 检查开始和结束日期参数
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        if start_date and end_date:
            return f"AND br.borrow_date BETWEEN '{start_date}' AND '{end_date}'"
        
        return ""
    
    def _convert_time_range(self, time_range: str) -> tuple:
        """转换时间范围为具体日期"""
        now = datetime.now()
        
        if time_range == "this_month":
            start = now.replace(day=1)
            next_month = start + timedelta(days=32)
            end = next_month.replace(day=1) - timedelta(days=1)
        elif time_range == "last_month":
            first_day = now.replace(day=1)
            end = first_day - timedelta(days=1)
            start = end.replace(day=1)
        elif time_range == "this_year":
            start = now.replace(month=1, day=1)
            end = now.replace(month=12, day=31)
        elif time_range == "last_year":
            last_year = now.year - 1
            start = datetime(last_year, 1, 1)
            end = datetime(last_year, 12, 31)
        elif time_range == "last_7_days":
            start = now - timedelta(days=7)
            end = now
        elif time_range == "last_30_days":
            start = now - timedelta(days=30)
            end = now
        else:
            start = end = now
        
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    def generate_sql(self, intent: str, entities: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> str:
        """生成SQL查询语句"""
        if params is None:
            params = {}
        
        # 获取SQL模板
        template = self.sql_templates.get(intent, "")
        if not template:
            logger.warning(f"未找到意图 {intent} 的SQL模板")
            return ""
        
        try:
            # 设置默认参数
            default_params = {
                "limit": params.get("limit", 50),
                "book_title": entities.get("book_title", ""),
                "author_name": entities.get("author_name", ""),
                "category_name": entities.get("category_name", ""),
                "student_id": entities.get("student_id", "")
            }
            
            # 构建所有过滤条件
            filters = {}
            for filter_name, builder in self.filter_builders.items():
                filters[filter_name] = builder(entities, params)
            
            # 合并参数和过滤条件
            format_params = {**default_params, **filters, **params}
            
            # 替换模板中的占位符
            sql = template.format(**format_params)
            
            # 清理SQL格式
            sql = self._clean_sql(sql)
            
            logger.info(f"生成SQL查询: {sql[:200]}...")
            return sql
            
        except Exception as e:
            logger.error(f"SQL生成错误: {e}")
            return ""
    
    def _clean_sql(self, sql: str) -> str:
        """清理SQL格式"""
        # 移除多余的空白字符
        sql = re.sub(r'\s+', ' ', sql)
        
        # 移除空的WHERE条件
        sql = re.sub(r'WHERE\s+1=1\s+ORDER', 'ORDER', sql)
        sql = re.sub(r'WHERE\s+1=1\s*$', '', sql)
        
        # 移除连续的AND
        sql = re.sub(r'\s+AND\s+AND\s+', ' AND ', sql)
        
        # 移除行首的AND
        sql = re.sub(r'WHERE\s+1=1\s+AND\s+', 'WHERE ', sql)
        
        return sql.strip()
    
    def validate_sql_params(self, intent: str, entities: Dict[str, Any]) -> tuple:
        """验证SQL参数完整性"""
        required_entities = {
            "query_book_by_title": ["book_title"],
            "query_book_by_author": ["author_name"],
            "query_book_by_category": ["category_name"],
            "query_student_borrowing": ["student_id"]
        }
        
        missing_entities = []
        if intent in required_entities:
            for entity in required_entities[intent]:
                if entity not in entities or not entities[entity]:
                    missing_entities.append(entity)
        
        is_valid = len(missing_entities) == 0
        return is_valid, missing_entities

# 全局实例
sql_generator = SQLQueryGenerator()

def generate_sql_query(intent: str, entities: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> str:
    """生成SQL查询的便捷函数"""
    return sql_generator.generate_sql(intent, entities, params)

def validate_query_params(intent: str, entities: Dict[str, Any]) -> tuple:
    """验证查询参数的便捷函数"""
    return sql_generator.validate_sql_params(intent, entities)
