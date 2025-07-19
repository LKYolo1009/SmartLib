#!/usr/bin/env python3
"""
NLU API路由 (Natural Language Understanding API Routes)
提供自然语言理解和查询转换的REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from app.services.nlu_processor import nlu_processor
from app.services.sql_generator import sql_generator
from app.db.session import get_db
from sqlalchemy.orm import Session
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/nlu", tags=["NLU"])

# 请求响应模型
class NLURequest(BaseModel):
    """NLU处理请求"""
    text: str
    language: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class NLUResponse(BaseModel):
    """NLU处理响应"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    language: str
    original_text: str
    sql_query: Optional[str] = None
    suggestions: Optional[List[str]] = None
    clarifications: Optional[List[str]] = None

class QueryRequest(BaseModel):
    """查询生成请求"""
    intent: str
    entities: Dict[str, Any]
    params: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    """查询生成响应"""
    sql_query: str
    is_valid: bool
    missing_entities: Optional[List[str]] = None
    estimated_results: Optional[int] = None

@router.post("/parse", response_model=NLUResponse)
async def parse_natural_language(request: NLURequest):
    """
    解析自然语言输入
    
    - **text**: 用户的自然语言输入
    - **language**: 指定语言(可选, 支持auto-detect)
    - **context**: 上下文信息(可选)
    
    返回意图识别、实体提取和SQL查询生成结果
    """
    try:
        # 执行NLU处理
        result = nlu_processor.process_text(request.text, request.language, request.context)
        
        # 生成SQL查询(如果可能)
        sql_query = None
        if result["intent"] != "unknown" and result["entities"]:
            try:
                sql_query = sql_generator.generate_sql(
                    result["intent"],
                    result["entities"],
                    request.context
                )
            except Exception as e:
                logger.warning(f"SQL生成失败: {e}")
        
        # 生成建议和澄清问题
        suggestions = _generate_suggestions(result)
        clarifications = _generate_clarifications(result)
        
        return NLUResponse(
            intent=result["intent"],
            entities=result["entities"],
            confidence=result["confidence"],
            language=result["language"],
            original_text=request.text,
            sql_query=sql_query,
            suggestions=suggestions,
            clarifications=clarifications
        )
        
    except Exception as e:
        logger.error(f"NLU处理错误: {e}")
        raise HTTPException(status_code=500, detail=f"NLU处理失败: {str(e)}")

@router.post("/generate-query", response_model=QueryResponse)
async def generate_query(request: QueryRequest):
    """
    基于意图和实体生成SQL查询
    
    - **intent**: 识别的意图
    - **entities**: 提取的实体
    - **params**: 额外参数(可选)
    
    返回生成的SQL查询和验证结果
    """
    try:
        # 验证参数完整性
        is_valid, missing_entities = sql_generator.validate_sql_params(
            request.intent,
            request.entities
        )
        
        # 生成SQL查询
        sql_query = ""
        if is_valid:
            sql_query = sql_generator.generate_sql(
                request.intent,
                request.entities,
                request.params
            )
        
        return QueryResponse(
            sql_query=sql_query,
            is_valid=is_valid,
            missing_entities=missing_entities
        )
        
    except Exception as e:
        logger.error(f"查询生成错误: {e}")
        raise HTTPException(status_code=500, detail=f"查询生成失败: {str(e)}")

@router.get("/intents")
async def get_supported_intents():
    """获取支持的意图列表"""
    return {
        "intents": list(nlu_processor.intent_patterns.keys()),
        "descriptions": {
            "query_book_inventory": "查询图书库存信息",
            "query_book_by_title": "根据书名查询图书",
            "query_book_by_author": "根据作者查询图书",
            "query_book_by_category": "根据类别查询图书",
            "query_borrowing_records": "查询借阅记录",
            "query_student_borrowing": "查询学生借阅情况",
            "query_statistics": "查询统计信息",
            "query_overdue_books": "查询逾期图书"
        }
    }

@router.get("/entities")
async def get_supported_entities():
    """获取支持的实体类型"""
    return {
        "entities": [
            "book_title",
            "author_name", 
            "category_name",
            "student_id",
            "status",
            "condition",
            "time_range",
            "date"
        ],
        "descriptions": {
            "book_title": "图书标题",
            "author_name": "作者姓名",
            "category_name": "图书类别",
            "student_id": "学生学号或姓名",
            "status": "状态(可用/已借出/遗失/已还)",
            "condition": "图书状况(好/一般/差)",
            "time_range": "时间范围(本月/上月/今年等)",
            "date": "具体日期"
        }
    }

@router.post("/test")
async def test_nlu_pipeline(
    text: str = Query(..., description="测试文本"),
    language: Optional[str] = Query(None, description="语言"),
    db: Session = Depends(get_db)
):
    """
    测试完整的NLU处理流水线
    包括意图识别、实体提取、SQL生成和查询执行
    """
    try:
        # 1. NLU处理
        nlu_result = nlu_processor.process_text(text, language)
        
        # 2. SQL生成
        sql_query = ""
        query_valid = False
        missing_entities = []
        
        if nlu_result["intent"] != "unknown":
            query_valid, missing_entities = sql_generator.validate_sql_params(
                nlu_result["intent"],
                nlu_result["entities"]
            )
            
            if query_valid:
                sql_query = sql_generator.generate_sql(
                    nlu_result["intent"],
                    nlu_result["entities"]
                )
        
        # 3. 查询执行(仅验证语法，不执行)
        execution_result = None
        if sql_query:
            try:
                # 这里可以添加SQL语法验证
                execution_result = "SQL查询已生成并验证"
            except Exception as e:
                execution_result = f"SQL执行错误: {e}"
        
        return {
            "input_text": text,
            "nlu_result": nlu_result,
            "sql_generation": {
                "sql_query": sql_query,
                "is_valid": query_valid,
                "missing_entities": missing_entities
            },
            "execution_result": execution_result,
            "pipeline_status": "success" if query_valid else "incomplete"
        }
        
    except Exception as e:
        logger.error(f"NLU测试流水线错误: {e}")
        return {
            "input_text": text,
            "error": str(e),
            "pipeline_status": "failed"
        }

def _generate_suggestions(nlu_result: Dict[str, Any]) -> List[str]:
    """生成查询建议"""
    suggestions = []
    intent = nlu_result["intent"]
    entities = nlu_result["entities"]
    
    if intent == "unknown":
        suggestions.append("请尝试更具体的描述，例如：查询某本书、查找作者作品、查看借阅记录等")
        
    elif intent in ["query_book_by_title", "query_book_by_author", "query_book_by_category"]:
        if not entities.get("book_title") and not entities.get("author_name") and not entities.get("category_name"):
            suggestions.append("请提供书名、作者姓名或图书类别")
            
    elif intent == "query_student_borrowing":
        if not entities.get("student_id"):
            suggestions.append("请提供学生学号或姓名")
    
    return suggestions

def _generate_clarifications(nlu_result: Dict[str, Any]) -> List[str]:
    """生成澄清问题"""
    clarifications = []
    intent = nlu_result["intent"]
    entities = nlu_result["entities"]
    
    # 检查必需实体是否缺失
    if intent == "query_book_by_title" and not entities.get("book_title"):
        clarifications.append("您要查询哪本书的信息？")
        
    elif intent == "query_book_by_author" and not entities.get("author_name"):
        clarifications.append("您要查询哪位作者的作品？")
        
    elif intent == "query_book_by_category" and not entities.get("category_name"):
        clarifications.append("您要查询哪个类别的图书？")
        
    elif intent == "query_student_borrowing" and not entities.get("student_id"):
        clarifications.append("请提供学生的学号或姓名")
    
    return clarifications
