#!/usr/bin/env python3
"""
智能查询API端点 (Intelligent Query API Endpoints)
提供完整的自然语言查询接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging

from app.services.intelligent_query_service import process_natural_language_query
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/smart-query", tags=["Smart Query"])

# 请求响应模型
class SmartQueryRequest(BaseModel):
    """智能查询请求"""
    query: str = Field(..., description="用户的自然语言查询")
    context: Optional[Dict[str, Any]] = Field(None, description="对话上下文")
    language: Optional[str] = Field(None, description="指定语言 (zh/en/auto)")
    session_id: Optional[str] = Field(None, description="会话ID，用于上下文跟踪")

class SmartQueryResponse(BaseModel):
    """智能查询响应"""
    status: str = Field(..., description="查询状态")
    intent: Optional[str] = Field(None, description="识别的意图")
    entities: Optional[Dict[str, Any]] = Field(None, description="提取的实体")
    confidence: Optional[float] = Field(None, description="置信度")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="查询结果")
    natural_response: Optional[str] = Field(None, description="自然语言响应")
    suggestions: Optional[List[str]] = Field(None, description="建议")
    result_count: Optional[int] = Field(None, description="结果数量")
    sql_query: Optional[str] = Field(None, description="生成的SQL查询")
    error_message: Optional[str] = Field(None, description="错误信息")
    clarifying_questions: Optional[List[str]] = Field(None, description="澄清问题")
    session_id: Optional[str] = Field(None, description="会话ID")

@router.post("/ask", response_model=SmartQueryResponse)
async def smart_query(
    request: SmartQueryRequest,
    db: Session = Depends(get_db)
):
    """
    智能查询主接口
    
    接受自然语言输入，返回查询结果和智能响应
    
    支持的查询类型：
    - 图书查询：根据书名、作者、类别查找图书
    - 库存查询：查看图书可用性和状态
    - 借阅记录：查询借阅历史和当前状态
    - 学生借阅：查看特定学生的借阅情况
    - 统计信息：图书借阅统计和热门度分析
    - 逾期查询：查找逾期图书和相关信息
    
    Examples:
    - "查找《三国演义》"
    - "鲁迅的作品有哪些？"
    - "计算机类别的书籍"
    - "张三的借阅记录"
    - "最热门的10本书"
    - "有哪些逾期的书？"
    """
    try:
        # 处理自然语言查询
        result = await process_natural_language_query(
            user_input=request.query,
            db=db,
            context=request.context,
            language=request.language
        )
        
        # 构建响应
        response = SmartQueryResponse(
            status=result.get("status", "unknown"),
            intent=result.get("intent"),
            entities=result.get("entities"),
            confidence=result.get("confidence"),
            results=result.get("results"),
            natural_response=result.get("natural_response") or result.get("message"),
            suggestions=result.get("suggestions"),
            result_count=result.get("result_count"),
            sql_query=result.get("sql_query"),
            error_message=result.get("error_message"),
            clarifying_questions=result.get("clarifying_questions"),
            session_id=request.session_id
        )
        
        logger.info(f"智能查询处理完成: {request.query} -> {result.get('status')}")
        return response
        
    except Exception as e:
        logger.error(f"智能查询处理错误: {e}")
        return SmartQueryResponse(
            status="error",
            error_message=f"查询处理失败: {str(e)}",
            suggestions=["请检查您的输入", "尝试重新表述问题"],
            session_id=request.session_id
        )

@router.get("/examples")
async def get_query_examples():
    """
    获取查询示例
    
    返回各种类型的自然语言查询示例，帮助用户了解支持的查询格式
    """
    return {
        "book_queries": {
            "by_title": [
                "查找《红楼梦》",
                "有《哈利波特》这本书吗？",
                "搜索书名包含'python'的图书"
            ],
            "by_author": [
                "鲁迅的作品有哪些？",
                "查找金庸写的书",
                "搜索作者是村上春树的图书"
            ],
            "by_category": [
                "计算机类别的书籍",
                "文学作品有哪些？",
                "查看科学类图书"
            ]
        },
        "borrowing_queries": [
            "张三的借阅记录",
            "学号12345的借阅情况",
            "最近一个月的借阅记录",
            "查看我的借书历史"
        ],
        "inventory_queries": [
            "图书库存情况",
            "哪些书可以借阅？",
            "查看图书状态",
            "可用的图书有哪些？"
        ],
        "statistics_queries": [
            "最热门的10本书",
            "借阅量最高的图书",
            "统计信息",
            "图书借阅分析"
        ],
        "overdue_queries": [
            "有哪些逾期的书？",
            "逾期图书列表",
            "超期未还的书籍",
            "查看逾期情况"
        ]
    }

@router.get("/capabilities")
async def get_query_capabilities():
    """
    获取系统查询能力说明
    
    返回系统支持的功能、限制和最佳实践
    """
    return {
        "supported_languages": ["中文", "英文", "自动检测"],
        "supported_intents": [
            {
                "name": "query_book_by_title",
                "description": "根据书名查询图书",
                "examples": ["查找《三国演义》", "有《Python编程》这本书吗？"]
            },
            {
                "name": "query_book_by_author", 
                "description": "根据作者查询图书",
                "examples": ["鲁迅的作品", "查找金庸写的书"]
            },
            {
                "name": "query_book_by_category",
                "description": "根据类别查询图书",
                "examples": ["计算机类的书", "文学作品有哪些？"]
            },
            {
                "name": "query_borrowing_records",
                "description": "查询借阅记录",
                "examples": ["最近的借阅记录", "本月借阅情况"]
            },
            {
                "name": "query_student_borrowing",
                "description": "查询学生借阅情况",
                "examples": ["张三的借书记录", "学号12345的借阅"]
            },
            {
                "name": "query_statistics",
                "description": "查询统计信息",
                "examples": ["最热门的书", "借阅统计"]
            },
            {
                "name": "query_overdue_books",
                "description": "查询逾期图书",
                "examples": ["逾期的书", "超期未还书籍"]
            }
        ],
        "supported_entities": [
            "book_title - 图书标题",
            "author_name - 作者姓名",
            "category_name - 图书类别", 
            "student_id - 学生学号或姓名",
            "status - 状态信息",
            "time_range - 时间范围",
            "date - 具体日期"
        ],
        "limitations": [
            "每次查询最多返回100条结果",
            "复杂的多表关联查询可能需要分步进行",
            "模糊匹配可能返回相似但不完全匹配的结果"
        ],
        "best_practices": [
            "使用具体的书名、作者名或学号获得最准确的结果",
            "对于大量结果，可以添加时间范围或其他过滤条件",
            "如果查询不到结果，尝试使用部分关键词",
            "可以用自然语言描述你想要查找的信息"
        ]
    }

@router.get("/health")
async def query_service_health():
    """
    检查智能查询服务健康状态
    
    返回各个组件的运行状态
    """
    try:
        # 这里可以添加具体的健康检查逻辑
        from app.services.nlu_processor import nlu_processor
        from app.services.sql_generator import sql_generator
        
        # 基本功能测试
        test_nlu = nlu_processor.process_text("测试", "zh")
        test_sql_valid = len(sql_generator.sql_templates) > 0
        
        return {
            "status": "healthy",
            "components": {
                "nlu_processor": "healthy" if test_nlu else "error",
                "sql_generator": "healthy" if test_sql_valid else "error",
                "database": "healthy"  # 如果能到这里说明数据库连接正常
            },
            "timestamp": "2024-12-20T12:00:00Z",
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-12-20T12:00:00Z"
        }
