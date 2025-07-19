#!/usr/bin/env python3
"""
智能查询服务 (Intelligent Query Service)
整合自然语言理解、SQL生成和数据库查询的完整服务
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from .nlu_processor import nlu_processor
from .sql_generator import sql_generator
from ..db.session import get_db

logger = logging.getLogger(__name__)

class IntelligentQueryService:
    """智能查询服务"""
    
    def __init__(self):
        self.max_results = 100
        self.query_timeout = 30  # 秒
        
    async def process_natural_query(
        self,
        user_input: str,
        db: Session,
        context: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理自然语言查询的完整流程
        
        Args:
            user_input: 用户的自然语言输入
            db: 数据库会话
            context: 对话上下文
            language: 指定语言
            
        Returns:
            包含查询结果、解释和建议的字典
        """
        try:
            # 1. NLU处理
            nlu_result = nlu_processor.process_text(user_input, language, context)
            logger.info(f"NLU处理结果: {nlu_result}")
            
            # 2. 检查意图识别结果
            if nlu_result["intent"] == "unknown":
                return self._handle_unknown_intent(user_input, nlu_result)
            
            # 3. 验证实体完整性
            is_valid, missing_entities = sql_generator.validate_sql_params(
                nlu_result["intent"],
                nlu_result["entities"]
            )
            
            if not is_valid:
                return self._handle_incomplete_entities(nlu_result, missing_entities)
            
            # 4. 生成SQL查询
            sql_query = sql_generator.generate_sql(
                nlu_result["intent"],
                nlu_result["entities"],
                context
            )
            
            if not sql_query:
                return self._handle_sql_generation_failure(nlu_result)
            
            # 5. 执行查询
            query_results = await self._execute_sql_query(db, sql_query)
            
            # 6. 格式化结果
            formatted_results = self._format_query_results(
                nlu_result["intent"],
                query_results,
                nlu_result["entities"]
            )
            
            # 7. 生成自然语言响应
            natural_response = self._generate_natural_response(
                nlu_result,
                formatted_results
            )
            
            return {
                "status": "success",
                "intent": nlu_result["intent"],
                "entities": nlu_result["entities"],
                "confidence": nlu_result["confidence"],
                "sql_query": sql_query,
                "results": formatted_results,
                "natural_response": natural_response,
                "suggestions": self._generate_follow_up_suggestions(nlu_result, formatted_results),
                "result_count": len(query_results) if query_results else 0
            }
            
        except Exception as e:
            logger.error(f"智能查询处理错误: {e}")
            return {
                "status": "error",
                "error_message": f"查询处理失败: {str(e)}",
                "user_input": user_input,
                "suggestions": ["请尝试重新表述您的问题", "检查输入是否包含必要的信息"]
            }
    
    async def _execute_sql_query(self, db: Session, sql_query: str) -> List[Dict[str, Any]]:
        """执行SQL查询"""
        try:
            result = db.execute(text(sql_query))
            rows = result.fetchall()
            
            # 转换为字典列表
            columns = result.keys()
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            logger.info(f"查询执行成功，返回 {len(results)} 条记录")
            return results
            
        except Exception as e:
            logger.error(f"SQL查询执行错误: {e}")
            logger.error(f"查询语句: {sql_query}")
            raise
    
    def _handle_unknown_intent(self, user_input: str, nlu_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理未知意图"""
        return {
            "status": "unknown_intent",
            "user_input": user_input,
            "message": "抱歉，我无法理解您的请求。",
            "suggestions": [
                "尝试询问：查找某本书",
                "尝试询问：查看借阅记录",
                "尝试询问：统计信息",
                "使用更具体的关键词"
            ],
            "confidence": nlu_result["confidence"],
            "detected_entities": nlu_result["entities"]
        }
    
    def _handle_incomplete_entities(self, nlu_result: Dict[str, Any], missing_entities: List[str]) -> Dict[str, Any]:
        """处理实体不完整的情况"""
        entity_names = {
            "book_title": "书名",
            "author_name": "作者姓名",
            "category_name": "图书类别",
            "student_id": "学生学号或姓名"
        }
        
        missing_names = [entity_names.get(e, e) for e in missing_entities]
        
        return {
            "status": "incomplete_entities",
            "intent": nlu_result["intent"],
            "detected_entities": nlu_result["entities"],
            "missing_entities": missing_entities,
            "message": f"请提供以下信息：{', '.join(missing_names)}",
            "clarifying_questions": self._generate_clarifying_questions(nlu_result["intent"], missing_entities)
        }
    
    def _handle_sql_generation_failure(self, nlu_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理SQL生成失败"""
        return {
            "status": "sql_generation_failed",
            "intent": nlu_result["intent"],
            "entities": nlu_result["entities"],
            "message": "查询生成失败，请重新尝试",
            "suggestions": ["检查输入格式", "使用更简单的表述"]
        }
    
    def _format_query_results(self, intent: str, results: List[Dict[str, Any]], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据意图格式化查询结果"""
        if not results:
            return []
        
        formatters = {
            "query_book_inventory": self._format_book_inventory,
            "query_book_by_title": self._format_book_details,
            "query_book_by_author": self._format_book_details,
            "query_book_by_category": self._format_book_details,
            "query_borrowing_records": self._format_borrowing_records,
            "query_student_borrowing": self._format_borrowing_records,
            "query_statistics": self._format_statistics,
            "query_overdue_books": self._format_overdue_books
        }
        
        formatter = formatters.get(intent, lambda x, e: x)
        return formatter(results, entities)
    
    def _format_book_inventory(self, results: List[Dict[str, Any]], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化图书库存结果"""
        formatted = []
        for item in results:
            formatted.append({
                "copy_id": item.get("copy_id"),
                "title": item.get("title"),
                "author": item.get("author_name"),
                "category": item.get("category_name"),
                "status": item.get("status"),
                "condition": item.get("condition"),
                "call_number": item.get("call_number"),
                "location": item.get("shelf_location"),
                "display_text": f"{item.get('title')} - {item.get('author_name')} ({item.get('status')})"
            })
        return formatted
    
    def _format_book_details(self, results: List[Dict[str, Any]], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化图书详情结果"""
        formatted = []
        for item in results:
            formatted.append({
                "book_id": item.get("book_id"),
                "title": item.get("title"),
                "author": item.get("author_name"),
                "category": item.get("category_name"),
                "publication_year": item.get("publication_year"),
                "total_copies": item.get("total_copies", 0),
                "available_copies": item.get("available_copies", 0),
                "display_text": f"{item.get('title')} - {item.get('author_name')} ({item.get('publication_year', 'N/A')})"
            })
        return formatted
    
    def _format_borrowing_records(self, results: List[Dict[str, Any]], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化借阅记录结果"""
        formatted = []
        for item in results:
            status = item.get("computed_status") or item.get("status")
            formatted.append({
                "borrow_id": item.get("borrow_id"),
                "student_name": item.get("student_name"),
                "student_id": item.get("matric_number"),
                "book_title": item.get("book_title"),
                "author": item.get("author_name"),
                "borrow_date": str(item.get("borrow_date")) if item.get("borrow_date") else None,
                "due_date": str(item.get("due_date")) if item.get("due_date") else None,
                "return_date": str(item.get("return_date")) if item.get("return_date") else None,
                "status": status,
                "display_text": f"{item.get('student_name')} - {item.get('book_title')} ({status})"
            })
        return formatted
    
    def _format_statistics(self, results: List[Dict[str, Any]], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化统计结果"""
        formatted = []
        for item in results:
            formatted.append({
                "title": item.get("title"),
                "author": item.get("author_name"),
                "category": item.get("category_name"),
                "borrow_count": item.get("borrow_count", 0),
                "unique_borrowers": item.get("unique_borrowers", 0),
                "display_text": f"{item.get('title')} - 借阅 {item.get('borrow_count', 0)} 次"
            })
        return formatted
    
    def _format_overdue_books(self, results: List[Dict[str, Any]], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化逾期图书结果"""
        formatted = []
        for item in results:
            formatted.append({
                "borrow_id": item.get("borrow_id"),
                "student_name": item.get("student_name"),
                "student_id": item.get("matric_number"),
                "book_title": item.get("book_title"),
                "author": item.get("author_name"),
                "due_date": str(item.get("due_date")) if item.get("due_date") else None,
                "days_overdue": item.get("days_overdue", 0),
                "call_number": item.get("call_number"),
                "display_text": f"{item.get('student_name')} - {item.get('book_title')} (逾期 {item.get('days_overdue', 0)} 天)"
            })
        return formatted
    
    def _generate_natural_response(self, nlu_result: Dict[str, Any], formatted_results: List[Dict[str, Any]]) -> str:
        """生成自然语言响应"""
        intent = nlu_result["intent"]
        entities = nlu_result["entities"]
        result_count = len(formatted_results)
        
        if result_count == 0:
            return self._generate_no_results_response(intent, entities)
        
        response_templates = {
            "query_book_inventory": f"找到 {result_count} 本图书的库存信息",
            "query_book_by_title": f"找到 {result_count} 本相关图书",
            "query_book_by_author": f"找到该作者的 {result_count} 本作品",
            "query_book_by_category": f"该类别下有 {result_count} 本图书",
            "query_borrowing_records": f"找到 {result_count} 条借阅记录",
            "query_student_borrowing": f"该学生有 {result_count} 条借阅记录",
            "query_statistics": f"统计结果显示 {result_count} 条热门图书信息",
            "query_overdue_books": f"发现 {result_count} 本逾期图书"
        }
        
        base_response = response_templates.get(intent, f"查询完成，找到 {result_count} 条结果")
        
        # 添加具体信息
        if result_count <= 3 and formatted_results:
            examples = [item.get("display_text", "") for item in formatted_results[:3]]
            examples_text = "；".join(filter(None, examples))
            if examples_text:
                base_response += f"：{examples_text}"
        
        return base_response
    
    def _generate_no_results_response(self, intent: str, entities: Dict[str, Any]) -> str:
        """生成无结果时的响应"""
        no_result_templates = {
            "query_book_by_title": f"未找到书名包含 '{entities.get('book_title', '')}' 的图书",
            "query_book_by_author": f"未找到作者 '{entities.get('author_name', '')}' 的作品",
            "query_book_by_category": f"该类别 '{entities.get('category_name', '')}' 下暂无图书",
            "query_student_borrowing": f"学生 '{entities.get('student_id', '')}' 暂无借阅记录",
            "query_overdue_books": "当前没有逾期图书"
        }
        
        return no_result_templates.get(intent, "未找到相关信息")
    
    def _generate_clarifying_questions(self, intent: str, missing_entities: List[str]) -> List[str]:
        """生成澄清问题"""
        questions = []
        
        if "book_title" in missing_entities:
            questions.append("您要查询哪本书？")
        if "author_name" in missing_entities:
            questions.append("请提供作者姓名")
        if "category_name" in missing_entities:
            questions.append("请指定图书类别")
        if "student_id" in missing_entities:
            questions.append("请提供学生学号或姓名")
            
        return questions
    
    def _generate_follow_up_suggestions(self, nlu_result: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
        """生成后续建议"""
        intent = nlu_result["intent"]
        result_count = len(results)
        
        suggestions = []
        
        if result_count > 10:
            suggestions.append("结果较多，您可以添加更多筛选条件")
            
        if intent.startswith("query_book"):
            suggestions.append("您还可以查询该书的借阅情况")
            suggestions.append("查看相同类别的其他图书")
            
        elif intent == "query_student_borrowing":
            suggestions.append("查看学生的逾期图书")
            suggestions.append("查询学生借阅统计")
            
        elif intent == "query_statistics":
            suggestions.append("查看具体时间段的统计")
            suggestions.append("按类别查看统计信息")
        
        return suggestions

# 全局服务实例
intelligent_query_service = IntelligentQueryService()

async def process_natural_language_query(
    user_input: str,
    db: Session,
    context: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """处理自然语言查询的便捷函数"""
    return await intelligent_query_service.process_natural_query(
        user_input, db, context, language
    )
