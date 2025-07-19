#!/usr/bin/env python3
"""
LLM增强的智能查询API路由 (LLM-Enhanced Smart Query API Routes)
提供基于Llama3.2的高级自然语言查询接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging
import asyncio

from app.services.llm_intelligent_query_service import llm_intelligent_query_service
from app.services.llm_nlu_processor import llm_nlu_processor  
from app.services.llm_sql_generator import llm_sql_generator
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/llm-query", tags=["LLM Smart Query"])

# 请求响应模型
class LLMQueryRequest(BaseModel):
    """LLM查询请求"""
    query: str = Field(..., description="用户的自然语言查询")
    context: Optional[Dict[str, Any]] = Field(None, description="对话上下文")
    language: Optional[str] = Field(None, description="指定语言 (zh/en/auto)")
    session_id: Optional[str] = Field(None, description="会话ID")
    use_llm: bool = Field(True, description="是否使用LLM处理")
    detailed_response: bool = Field(False, description="是否返回详细处理步骤")

class LLMQueryResponse(BaseModel):
    """LLM查询响应"""
    status: str = Field(..., description="查询状态")
    processing_method: str = Field(..., description="处理方法")
    intent: Optional[str] = Field(None, description="识别的意图")
    entities: Optional[Dict[str, Any]] = Field(None, description="提取的实体")
    nlu_confidence: Optional[float] = Field(None, description="NLU置信度")
    sql_confidence: Optional[float] = Field(None, description="SQL生成置信度")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="查询结果")
    natural_response: Optional[str] = Field(None, description="自然语言响应")
    result_summary: Optional[str] = Field(None, description="结果摘要")
    suggestions: Optional[List[str]] = Field(None, description="智能建议")
    result_count: Optional[int] = Field(None, description="结果数量")
    sql_query: Optional[str] = Field(None, description="生成的SQL查询")
    sql_explanation: Optional[str] = Field(None, description="SQL查询解释")
    key_insights: Optional[List[str]] = Field(None, description="关键洞察")
    processing_steps: Optional[List[Dict[str, Any]]] = Field(None, description="处理步骤")
    error_message: Optional[str] = Field(None, description="错误信息")
    timestamp: Optional[str] = Field(None, description="处理时间戳")

class ComplexQueryRequest(BaseModel):
    """复杂查询请求"""
    query: str = Field(..., description="复杂的自然语言查询")
    context: Optional[Dict[str, Any]] = Field(None, description="查询上下文")

@router.post("/ask", response_model=LLMQueryResponse)
async def llm_smart_query(
    request: LLMQueryRequest,
    db: Session = Depends(get_db)
):
    """
    LLM增强的智能查询主接口
    
    使用本地部署的Llama3.2进行更智能的意图识别和SQL生成
    
    Features:
    - 🤖 **LLM驱动的意图理解**: 使用Llama3.2进行上下文感知的意图识别
    - 🔍 **智能实体提取**: 自动识别和提取查询中的关键实体
    - 📊 **动态SQL生成**: 根据意图和实体生成优化的SQL查询
    - 💬 **自然语言响应**: 生成友好的自然语言查询结果描述
    - 🎯 **智能建议**: 提供相关的后续查询建议
    - 🛡️ **安全可靠**: 包含SQL注入防护和错误恢复机制
    
    Examples:
    - "帮我找找鲁迅写的所有作品，特别是小说类的"
    - "查看张三最近借了哪些计算机相关的书籍"
    - "统计一下本月最受欢迎的10本书，按借阅次数排序"
    - "有没有逾期超过一周的图书？需要催还的那种"
    """
    try:
        result = await llm_intelligent_query_service.process_natural_query(
            user_input=request.query,
            db=db,
            context=request.context,
            language=request.language,
            use_llm=request.use_llm
        )
        
        # 构建响应，过滤不需要的字段（如果不需要详细信息）
        response_data = result.copy()
        if not request.detailed_response:
            # 移除详细的处理步骤以减少响应大小
            response_data.pop("processing_steps", None)
            response_data.pop("sql_query", None)  # 可选：隐藏SQL查询
        
        response = LLMQueryResponse(**response_data)
        
        logger.info(f"LLM智能查询完成: {request.query} -> {result.get('status')}")
        return response
        
    except Exception as e:
        logger.error(f"LLM智能查询错误: {e}")
        return LLMQueryResponse(
            status="error",
            processing_method="llm_enhanced",
            error_message=f"查询处理失败: {str(e)}",
            suggestions=["检查查询格式", "稍后重试", "使用更简单的表述"]
        )

@router.post("/complex-query")
async def complex_query_analysis(
    request: ComplexQueryRequest,
    db: Session = Depends(get_db)
):
    """
    复杂查询分析接口
    
    直接使用LLM分析复杂的自然语言查询，无需预定义意图
    适用于复杂的、多条件的、或者跨多个概念的查询
    
    Examples:
    - "找出借阅量最高的科技类图书，同时显示这些书的作者信息和当前库存状态"
    - "统计每个院系学生的借阅偏好，按图书类别分组显示"
    - "查询今年新入库的图书中，哪些还没有被借阅过"
    """
    try:
        # 使用LLM直接处理复杂查询
        complex_result = await llm_sql_generator.generate_complex_query(
            request.query,
            request.context
        )
        
        if not complex_result.get("sql_query"):
            return {
                "status": "analysis_failed",
                "message": "无法理解复杂查询需求",
                "interpreted_intent": complex_result.get("interpreted_intent", "未知意图"),
                "suggestions": complex_result.get("alternative_queries", []),
                "error": complex_result.get("error", "查询分析失败")
            }
        
        # 执行生成的查询
        try:
            result = db.execute(complex_result["sql_query"])
            rows = result.fetchall()
            columns = result.keys()
            query_results = [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"复杂查询执行失败: {e}")
            return {
                "status": "execution_failed", 
                "sql_query": complex_result["sql_query"],
                "error": str(e),
                "interpreted_intent": complex_result.get("interpreted_intent"),
                "suggestions": ["检查查询条件", "简化查询需求"]
            }
        
        return {
            "status": "success",
            "interpreted_intent": complex_result.get("interpreted_intent"),
            "sql_query": complex_result["sql_query"],
            "explanation": complex_result.get("explanation"),
            "confidence": complex_result.get("confidence", 0.0),
            "results": query_results,
            "result_count": len(query_results),
            "assumptions": complex_result.get("assumptions", []),
            "alternative_queries": complex_result.get("alternative_queries", [])
        }
        
    except Exception as e:
        logger.error(f"复杂查询处理错误: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "suggestions": ["检查查询格式", "使用标准查询接口"]
        }

class SQLExplainRequest(BaseModel):
    """SQL解释请求"""
    sql_query: str = Field(..., description="要解释的SQL查询")

class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    queries: List[str] = Field(..., description="批量查询列表")

@router.post("/explain-sql")
async def explain_sql_query(
    request: SQLExplainRequest,
):
    """
    SQL查询解释接口
    
    使用LLM解释SQL查询的作用和逻辑，帮助理解复杂查询
    """
    try:
        explanation = await llm_sql_generator.explain_query(request.sql_query)
        
        return {
            "status": "success",
            "sql_query": request.sql_query,
            "explanation": explanation,
            "timestamp": llm_intelligent_query_service._create_error_response.__defaults__[0]
        }
        
    except Exception as e:
        logger.error(f"SQL解释错误: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "sql_query": request.sql_query
        }

@router.get("/llm-status")
async def get_llm_service_status():
    """
    获取LLM服务状态
    
    检查Llama3.2连接状态和各组件健康情况
    """
    try:
        status = await llm_intelligent_query_service.get_service_status()
        return status
        
    except Exception as e:
        logger.error(f"LLM状态检查错误: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "无法获取LLM服务状态"
        }

@router.get("/capabilities")
async def get_llm_capabilities():
    """
    获取LLM增强查询的能力说明
    """
    return {
        "llm_model": "llama3.2",
        "enhanced_features": [
            {
                "name": "上下文感知意图识别",
                "description": "理解复杂的、多层次的查询意图",
                "examples": ["找找那种适合计算机专业学生看的编程入门书籍"]
            },
            {
                "name": "智能实体提取",
                "description": "准确识别查询中的关键信息",
                "examples": ["张三最近借的那些关于机器学习的书"]
            },
            {
                "name": "动态SQL生成",
                "description": "根据理解生成优化的数据库查询",
                "examples": ["生成包含多表连接和聚合的复杂查询"]
            },
            {
                "name": "自然语言结果描述",
                "description": "用自然语言解释查询结果",
                "examples": ["找到3本相关图书，其中2本可以借阅"]
            },
            {
                "name": "智能查询建议",
                "description": "基于当前查询推荐相关查询",
                "examples": ["您还可以查看这些作者的其他作品"]
            },
            {
                "name": "错误恢复机制",
                "description": "当LLM不可用时自动降级到规则系统",
                "examples": ["保证服务的持续可用性"]
            }
        ],
        "supported_query_types": [
            "复杂的图书查询（多条件、模糊匹配）",
            "智能的作者和类别搜索",
            "上下文相关的借阅记录查询",
            "动态的统计分析查询",
            "自然语言的库存管理查询"
        ],
        "performance_features": [
            "并发处理支持",
            "查询结果缓存",
            "SQL注入防护",
            "自动查询优化"
        ],
        "limitations": [
            "依赖本地Llama3.2服务的可用性",
            "复杂查询的处理时间较长（通常5-15秒）",
            "LLM响应质量取决于模型训练和提示设计"
        ]
    }

@router.get("/examples")
async def get_llm_query_examples():
    """
    获取LLM增强查询的示例
    
    展示各种复杂查询的使用方法
    """
    return {
        "basic_enhanced_queries": {
            "智能书籍搜索": [
                "帮我找找鲁迅写的小说，最好是比较有名的那种",
                "有没有适合初学者的Python编程书籍？",
                "推荐一些关于人工智能的入门读物"
            ],
            "上下文相关查询": [
                "张三这个月借了什么书？都是什么类型的？",
                "计算机专业的学生最喜欢借什么书？",
                "最近一周有哪些热门图书被借走了？"
            ]
        },
        "complex_queries": {
            "多条件组合查询": [
                "找出借阅量最高的科技类图书，同时显示作者信息和库存状态",
                "查询今年新增的图书中，哪些还没有被任何学生借阅过",
                "统计各个院系学生的借阅偏好，按图书类别分组"
            ],
            "分析型查询": [
                "分析一下哪些图书容易逾期不还，找出规律",
                "比较不同类别图书的平均借阅周期",
                "预测哪些图书下个月可能会很热门"
            ]
        },
        "conversational_queries": {
            "对话式查询": [
                "我想找一本关于数据结构的书 - 有什么特定的作者偏好吗？",
                "查看我的借阅记录 - 您是指最近的记录还是所有历史记录？",
                "推荐一些好书 - 您对哪个领域比较感兴趣？"
            ]
        },
        "advanced_features": {
            "智能推理": [
                "这本书适合什么水平的读者？（基于书籍内容和借阅模式推断）",
                "根据我的借阅历史，推荐相似的书籍",
                "预测这本书什么时候会有空余副本可以借阅"
            ]
        }
    }

@router.post("/batch-process")
async def batch_process_queries(
    request: BatchProcessRequest,
    db: Session = Depends(get_db)
):
    """
    批量处理多个查询
    
    适用于需要同时处理多个查询的场景
    """
    if len(request.queries) > 10:
        raise HTTPException(status_code=400, detail="批量查询数量不能超过10个")
    
    try:
        # 使用异步批量处理
        tasks = []
        for query in request.queries:
            task = llm_intelligent_query_service.process_natural_query(
                query, db, use_llm=True
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "query": request.queries[i],
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append({
                    "query": request.queries[i],
                    "result": result
                })
        
        return {
            "status": "completed",
            "processed_count": len(request.queries),
            "results": processed_results,
            "processing_method": "llm_batch"
        }
        
    except Exception as e:
        logger.error(f"批量处理错误: {e}")
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")
