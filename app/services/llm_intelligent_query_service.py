#!/usr/bin/env python3
"""
LLM增强的智能查询服务 (LLM-Enhanced Intelligent Query Service)
整合LLM驱动的NLU和SQL生成，提供更智能的查询体验
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import asyncio
from datetime import datetime

from .llm_nlu_processor import llm_nlu_processor
from .llm_sql_generator import llm_sql_generator
from .intelligent_query_service import intelligent_query_service  # 作为降级方案

logger = logging.getLogger(__name__)

class LLMIntelligentQueryService:
    """LLM增强的智能查询服务"""
    
    def __init__(self):
        self.max_results = 100
        self.query_timeout = 60  # 增加超时时间以适应LLM处理
        self.enable_fallback = True  # 启用降级到规则基础系统
        
    async def process_natural_query(
        self,
        user_input: str,
        db: Session,
        context: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        使用LLM处理自然语言查询的完整流程
        
        Args:
            user_input: 用户的自然语言输入
            db: 数据库会话
            context: 对话上下文
            language: 指定语言
            use_llm: 是否使用LLM处理
            
        Returns:
            包含查询结果、解释和建议的详细字典
        """
        processing_start = datetime.now()
        
        try:
            if use_llm:
                return await self._process_with_llm(user_input, db, context, language)
            else:
                return await self._process_with_rules(user_input, db, context, language)
                
        except Exception as e:
            logger.error(f"LLM智能查询处理错误: {e}")
            
            # 如果启用降级，尝试使用规则系统
            if self.enable_fallback and use_llm:
                logger.info("降级到规则基础查询处理")
                try:
                    result = await self._process_with_rules(user_input, db, context, language)
                    result["processing_method"] = "llm_fallback_to_rules"
                    result["llm_error"] = str(e)
                    return result
                except Exception as fallback_error:
                    logger.error(f"降级处理也失败: {fallback_error}")
            
            return self._create_error_response(user_input, str(e), processing_start)
    
    async def _process_with_llm(
        self,
        user_input: str,
        db: Session,
        context: Optional[Dict[str, Any]],
        language: Optional[str]
    ) -> Dict[str, Any]:
        """使用LLM处理查询"""
        processing_steps = []
        
        # 1. LLM NLU处理
        step_start = datetime.now()
        nlu_result = await llm_nlu_processor.process_text(user_input, language, context)
        processing_steps.append({
            "step": "llm_nlu_processing",
            "duration": (datetime.now() - step_start).total_seconds(),
            "result": {
                "intent": nlu_result["intent"],
                "entities": nlu_result["entities"],
                "confidence": nlu_result["confidence"]
            }
        })
        
        logger.info(f"LLM NLU处理结果: {nlu_result['intent']} ({nlu_result['confidence']:.2f})")
        
        # 检查意图识别结果
        if nlu_result["intent"] == "unknown" or nlu_result["confidence"] < 0.3:
            return await self._handle_low_confidence_intent(user_input, nlu_result, processing_steps)
        
        # 2. LLM SQL生成
        step_start = datetime.now()
        sql_result = await llm_sql_generator.generate_sql(
            nlu_result["intent"],
            nlu_result["entities"],
            context
        )
        processing_steps.append({
            "step": "llm_sql_generation",
            "duration": (datetime.now() - step_start).total_seconds(),
            "result": {
                "sql_generated": bool(sql_result.get("sql_query")),
                "confidence": sql_result.get("confidence", 0.0)
            }
        })
        
        if not sql_result.get("sql_query"):
            return self._handle_sql_generation_failure(nlu_result, sql_result, processing_steps)
        
        # 3. 执行查询
        step_start = datetime.now()
        try:
            query_results = await self._execute_sql_query(db, sql_result["sql_query"])
            processing_steps.append({
                "step": "query_execution",
                "duration": (datetime.now() - step_start).total_seconds(),
                "result": {"rows_returned": len(query_results)}
            })
        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            processing_steps.append({
                "step": "query_execution",
                "duration": (datetime.now() - step_start).total_seconds(),
                "error": str(e)
            })
            return self._handle_query_execution_failure(nlu_result, sql_result, str(e), processing_steps)
        
        # 4. LLM增强结果处理
        step_start = datetime.now()
        enhanced_results = await self._enhance_results_with_llm(
            user_input, nlu_result, sql_result, query_results
        )
        processing_steps.append({
            "step": "llm_result_enhancement",
            "duration": (datetime.now() - step_start).total_seconds(),
            "result": {"enhancement_applied": True}
        })
        
        # 5. 生成智能建议
        step_start = datetime.now()
        smart_suggestions = await self._generate_smart_suggestions_llm(
            user_input, nlu_result, query_results, context
        )
        processing_steps.append({
            "step": "smart_suggestions_generation",
            "duration": (datetime.now() - step_start).total_seconds(),
            "result": {"suggestions_count": len(smart_suggestions)}
        })
        
        return {
            "status": "success",
            "processing_method": "llm_enhanced",
            "intent": nlu_result["intent"],
            "entities": nlu_result["entities"],
            "nlu_confidence": nlu_result["confidence"],
            "sql_confidence": sql_result.get("confidence", 0.0),
            "sql_query": sql_result["sql_query"],
            "sql_explanation": sql_result.get("explanation", ""),
            "results": enhanced_results["formatted_results"],
            "natural_response": enhanced_results["natural_response"],
            "result_summary": enhanced_results["result_summary"],
            "suggestions": smart_suggestions,
            "result_count": len(query_results),
            "processing_steps": processing_steps,
            "user_input": user_input,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _process_with_rules(
        self,
        user_input: str,
        db: Session,
        context: Optional[Dict[str, Any]],
        language: Optional[str]
    ) -> Dict[str, Any]:
        """使用规则系统处理查询"""
        result = await intelligent_query_service.process_natural_query(
            user_input, db, context, language
        )
        result["processing_method"] = "rule_based"
        return result
    
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
    
    async def _enhance_results_with_llm(
        self,
        user_input: str,
        nlu_result: Dict[str, Any],
        sql_result: Dict[str, Any],
        query_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用LLM增强查询结果"""
        
        if not query_results:
            return await self._generate_no_results_response_llm(user_input, nlu_result)
        
        # 限制传递给LLM的数据量
        sample_results = query_results[:5]  # 只传递前5条结果作为示例
        
        enhancement_prompt = f"""
用户查询："{user_input}"
识别意图：{nlu_result["intent"]}
查询结果示例（共{len(query_results)}条）：
{json.dumps(sample_results, ensure_ascii=False, indent=2)}

请生成：
1. 自然语言的结果总结
2. 格式化的结果描述
3. 简洁的结果摘要

返回JSON格式：
{{
  "natural_response": "自然语言回应",
  "result_summary": "结果摘要",
  "key_insights": ["关键洞察"],
  "data_highlights": ["数据亮点"]
}}

增强结果："""
        
        try:
            response = await llm_sql_generator._call_llm(enhancement_prompt, max_tokens=400)
            enhanced = json.loads(llm_sql_generator._extract_json(response))
            
            # 格式化所有结果
            formatted_results = self._format_all_results(
                nlu_result["intent"], 
                query_results, 
                nlu_result["entities"]
            )
            
            return {
                "natural_response": enhanced.get("natural_response", f"找到{len(query_results)}条结果"),
                "result_summary": enhanced.get("result_summary", "查询完成"),
                "formatted_results": formatted_results,
                "key_insights": enhanced.get("key_insights", []),
                "data_highlights": enhanced.get("data_highlights", [])
            }
            
        except Exception as e:
            logger.error(f"LLM结果增强失败: {e}")
            # 降级到基础格式化
            return {
                "natural_response": f"查询完成，找到{len(query_results)}条结果",
                "result_summary": "结果已获取",
                "formatted_results": self._format_all_results(
                    nlu_result["intent"], query_results, nlu_result["entities"]
                ),
                "key_insights": [],
                "data_highlights": []
            }
    
    async def _generate_smart_suggestions_llm(
        self,
        user_input: str,
        nlu_result: Dict[str, Any],
        query_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """使用LLM生成智能建议"""
        
        suggestion_prompt = f"""
基于用户查询和结果，生成3-5个有用的后续查询建议。

用户查询："{user_input}"
识别意图：{nlu_result["intent"]}
结果数量：{len(query_results)}
上下文：{json.dumps(context or {}, ensure_ascii=False)}

请生成相关的、有价值的后续查询建议，返回JSON数组格式：
["建议1", "建议2", "建议3", "建议4", "建议5"]

建议要求：
1. 与当前查询相关但不重复
2. 实用且用户可能感兴趣
3. 涵盖不同的查询角度
4. 使用自然语言表达

智能建议："""
        
        try:
            response = await llm_sql_generator._call_llm(suggestion_prompt, max_tokens=300)
            suggestions_json = llm_sql_generator._extract_json(response)
            suggestions = json.loads(suggestions_json)
            
            # 确保返回列表
            if isinstance(suggestions, list):
                return suggestions[:5]  # 最多5个建议
            else:
                return []
                
        except Exception as e:
            logger.error(f"智能建议生成失败: {e}")
            return self._generate_fallback_suggestions(nlu_result, query_results)
    
    async def _handle_low_confidence_intent(
        self,
        user_input: str,
        nlu_result: Dict[str, Any],
        processing_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理低置信度意图"""
        
        clarification_prompt = f"""
用户输入："{user_input}"
当前理解：意图={nlu_result["intent"]}, 置信度={nlu_result["confidence"]}

系统无法确定用户的具体需求。请生成：
1. 澄清问题帮助理解用户意图
2. 相关的查询建议
3. 可能的意图解释

返回JSON格式：
{{
  "clarification_questions": ["澄清问题1", "澄清问题2"],
  "suggested_queries": ["建议查询1", "建议查询2"],
  "possible_intents": [
    {{"intent": "可能意图1", "explanation": "解释"}},
    {{"intent": "可能意图2", "explanation": "解释"}}
  ],
  "help_message": "帮助信息"
}}

澄清结果："""
        
        try:
            response = await llm_sql_generator._call_llm(clarification_prompt, max_tokens=400)
            clarification = json.loads(llm_sql_generator._extract_json(response))
            
            return {
                "status": "needs_clarification",
                "processing_method": "llm_enhanced",
                "user_input": user_input,
                "detected_intent": nlu_result["intent"],
                "confidence": nlu_result["confidence"],
                "clarification_questions": clarification.get("clarification_questions", []),
                "suggested_queries": clarification.get("suggested_queries", []),
                "possible_intents": clarification.get("possible_intents", []),
                "help_message": clarification.get("help_message", "请提供更多详细信息"),
                "processing_steps": processing_steps
            }
            
        except Exception as e:
            logger.error(f"澄清生成失败: {e}")
            return {
                "status": "needs_clarification",
                "processing_method": "llm_enhanced",
                "user_input": user_input,
                "message": "抱歉，我无法理解您的请求。请尝试更具体的描述。",
                "suggestions": ["尝试询问具体的书名或作者", "查询借阅记录", "查看统计信息"]
            }
    
    async def _generate_no_results_response_llm(
        self,
        user_input: str,
        nlu_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用LLM生成无结果响应"""
        
        no_results_prompt = f"""
用户查询："{user_input}"
意图：{nlu_result["intent"]}
实体：{json.dumps(nlu_result["entities"], ensure_ascii=False)}

查询没有返回结果。请生成：
1. 友好的无结果说明
2. 可能的原因分析
3. 替代查询建议

返回JSON格式：
{{
  "natural_response": "友好的回应",
  "possible_reasons": ["可能原因1", "可能原因2"],
  "alternative_queries": ["替代查询1", "替代查询2"],
  "search_tips": ["搜索提示1", "搜索提示2"]
}}

无结果响应："""
        
        try:
            response = await llm_sql_generator._call_llm(no_results_prompt, max_tokens=300)
            no_results_info = json.loads(llm_sql_generator._extract_json(response))
            
            return {
                "natural_response": no_results_info.get("natural_response", "未找到相关结果"),
                "result_summary": "无查询结果",
                "formatted_results": [],
                "possible_reasons": no_results_info.get("possible_reasons", []),
                "alternative_queries": no_results_info.get("alternative_queries", []),
                "search_tips": no_results_info.get("search_tips", [])
            }
            
        except Exception as e:
            logger.error(f"无结果响应生成失败: {e}")
            return {
                "natural_response": "未找到相关信息，请尝试调整搜索条件",
                "result_summary": "无查询结果",
                "formatted_results": []
            }
    
    def _format_all_results(
        self, 
        intent: str, 
        results: List[Dict[str, Any]], 
        entities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """格式化所有查询结果"""
        # 重用原有的格式化逻辑
        return intelligent_query_service._format_query_results(intent, results, entities)
    
    def _generate_fallback_suggestions(
        self, 
        nlu_result: Dict[str, Any], 
        query_results: List[Dict[str, Any]]
    ) -> List[str]:
        """生成降级建议"""
        intent = nlu_result["intent"]
        result_count = len(query_results)
        
        suggestions = []
        
        if result_count > 10:
            suggestions.append("结果较多，可以添加更多筛选条件")
            
        if intent.startswith("query_book"):
            suggestions.append("查询该书的借阅情况")
            suggestions.append("查看相同类别的其他图书")
            
        elif intent == "query_student_borrowing":
            suggestions.append("查看学生的逾期图书")
            suggestions.append("查询学生借阅统计")
        
        return suggestions
    
    def _handle_sql_generation_failure(
        self,
        nlu_result: Dict[str, Any],
        sql_result: Dict[str, Any],
        processing_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理SQL生成失败"""
        return {
            "status": "sql_generation_failed",
            "processing_method": "llm_enhanced",
            "intent": nlu_result["intent"],
            "entities": nlu_result["entities"],
            "message": sql_result.get("explanation", "查询生成失败"),
            "error": sql_result.get("error", "未知错误"),
            "processing_steps": processing_steps,
            "suggestions": ["请尝试重新表述您的问题", "使用更简单的查询"]
        }
    
    def _handle_query_execution_failure(
        self,
        nlu_result: Dict[str, Any],
        sql_result: Dict[str, Any],
        error_msg: str,
        processing_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理查询执行失败"""
        return {
            "status": "query_execution_failed",
            "processing_method": "llm_enhanced",
            "intent": nlu_result["intent"],
            "entities": nlu_result["entities"],
            "sql_query": sql_result["sql_query"],
            "message": "查询执行失败，请稍后重试",
            "error": error_msg,
            "processing_steps": processing_steps,
            "suggestions": ["检查输入信息是否正确", "尝试简化查询条件"]
        }
    
    def _create_error_response(
        self, 
        user_input: str, 
        error_msg: str, 
        processing_start: datetime
    ) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "status": "error",
            "processing_method": "llm_enhanced",
            "user_input": user_input,
            "error_message": f"处理失败: {error_msg}",
            "processing_duration": (datetime.now() - processing_start).total_seconds(),
            "suggestions": ["请检查您的输入", "稍后重试", "联系系统管理员"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            # 测试LLM连接
            test_nlu = await llm_nlu_processor.process_text("测试", "zh")
            test_sql = await llm_sql_generator.generate_sql("query_book_by_title", {"book_title": "测试"})
            
            return {
                "status": "healthy",
                "processing_method": "llm_enhanced",
                "components": {
                    "llm_nlu_processor": "healthy" if test_nlu.get("intent") else "error",
                    "llm_sql_generator": "healthy" if test_sql.get("sql_query") else "error",
                    "fallback_enabled": self.enable_fallback
                },
                "llm_info": {
                    "endpoint": llm_nlu_processor.llm_endpoint,
                    "model": llm_nlu_processor.model_name
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "degraded",
                "processing_method": "fallback_available" if self.enable_fallback else "unavailable",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# 全局服务实例
llm_intelligent_query_service = LLMIntelligentQueryService()

async def process_query_with_llm(
    user_input: str,
    db: Session,
    context: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
    use_llm: bool = True
) -> Dict[str, Any]:
    """使用LLM处理查询的便捷函数"""
    return await llm_intelligent_query_service.process_natural_query(
        user_input, db, context, language, use_llm
    )
