#!/usr/bin/env python3
"""
LLM增强的SQL查询生成器 (LLM-Enhanced SQL Generator)
使用Llama3.2生成更智能、更优化的SQL查询
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMSQLGenerator:
    """基于LLM的SQL查询生成器"""
    
    def __init__(self, llm_endpoint: str = "http://localhost:11434", model_name: str = "llama3.2"):
        self.llm_endpoint = llm_endpoint
        self.model_name = model_name
        self.timeout = 30
        
        # 数据库模式信息
        self.schema_info = self._load_schema_info()
        
        # SQL生成提示模板
        self.sql_generation_prompt = self._create_sql_prompt_template()
    
    def _load_schema_info(self) -> Dict[str, Any]:
        """加载数据库模式信息"""
        return {
            "tables": {
                "books": {
                    "columns": [
                        {"name": "book_id", "type": "INTEGER", "description": "图书ID，主键"},
                        {"name": "title", "type": "VARCHAR", "description": "图书标题"},
                        {"name": "author_id", "type": "INTEGER", "description": "作者ID，外键"},
                        {"name": "category_id", "type": "INTEGER", "description": "类别ID，外键"},
                        {"name": "publication_year", "type": "INTEGER", "description": "出版年份"},
                        {"name": "isbn", "type": "VARCHAR", "description": "ISBN号码"},
                        {"name": "description", "type": "TEXT", "description": "图书描述"}
                    ],
                    "description": "图书基础信息表"
                },
                "authors": {
                    "columns": [
                        {"name": "author_id", "type": "INTEGER", "description": "作者ID，主键"},
                        {"name": "author_name", "type": "VARCHAR", "description": "作者姓名"},
                        {"name": "birth_year", "type": "INTEGER", "description": "出生年份"},
                        {"name": "nationality", "type": "VARCHAR", "description": "国籍"}
                    ],
                    "description": "作者信息表"
                },
                "categories": {
                    "columns": [
                        {"name": "category_id", "type": "INTEGER", "description": "类别ID，主键"},
                        {"name": "category_name", "type": "VARCHAR", "description": "类别名称"},
                        {"name": "parent_category_id", "type": "INTEGER", "description": "父类别ID"},
                        {"name": "description", "type": "TEXT", "description": "类别描述"}
                    ],
                    "description": "图书分类表"
                },
                "book_copies": {
                    "columns": [
                        {"name": "copy_id", "type": "INTEGER", "description": "副本ID，主键"},
                        {"name": "book_id", "type": "INTEGER", "description": "图书ID，外键"},
                        {"name": "status", "type": "VARCHAR", "description": "状态：available/borrowed/missing"},
                        {"name": "condition", "type": "VARCHAR", "description": "状况：good/fair/poor"},
                        {"name": "call_number", "type": "VARCHAR", "description": "索书号"},
                        {"name": "shelf_location", "type": "VARCHAR", "description": "书架位置"}
                    ],
                    "description": "图书副本表，记录每本书的具体副本"
                },
                "students": {
                    "columns": [
                        {"name": "student_id", "type": "INTEGER", "description": "学生ID，主键"},
                        {"name": "matric_number", "type": "VARCHAR", "description": "学号"},
                        {"name": "full_name", "type": "VARCHAR", "description": "学生姓名"},
                        {"name": "email", "type": "VARCHAR", "description": "邮箱地址"},
                        {"name": "phone", "type": "VARCHAR", "description": "电话号码"},
                        {"name": "department", "type": "VARCHAR", "description": "院系"}
                    ],
                    "description": "学生信息表"
                },
                "borrowing_records": {
                    "columns": [
                        {"name": "borrow_id", "type": "INTEGER", "description": "借阅ID，主键"},
                        {"name": "student_id", "type": "INTEGER", "description": "学生ID，外键"},
                        {"name": "copy_id", "type": "INTEGER", "description": "副本ID，外键"},
                        {"name": "borrow_date", "type": "TIMESTAMP", "description": "借阅日期"},
                        {"name": "due_date", "type": "TIMESTAMP", "description": "应还日期"},
                        {"name": "return_date", "type": "TIMESTAMP", "description": "实际归还日期"},
                        {"name": "status", "type": "VARCHAR", "description": "借阅状态：borrowed/returned/overdue"}
                    ],
                    "description": "借阅记录表"
                }
            },
            "relationships": [
                "books.author_id -> authors.author_id",
                "books.category_id -> categories.category_id", 
                "book_copies.book_id -> books.book_id",
                "borrowing_records.student_id -> students.student_id",
                "borrowing_records.copy_id -> book_copies.copy_id"
            ]
        }
    
    def _create_sql_prompt_template(self) -> str:
        """创建SQL生成提示模板"""
        schema_description = self._format_schema_for_prompt()
        
        return f"""
你是一个专业的数据库查询专家。请根据用户的查询意图和提取的实体生成高质量的PostgreSQL查询语句。

数据库模式：
{schema_description}

查询优化原则：
1. 使用适当的JOIN来连接相关表
2. 使用ILIKE进行不区分大小写的模糊匹配
3. 添加适当的ORDER BY和LIMIT子句
4. 避免SELECT *，只选择需要的列
5. 使用WHERE条件过滤数据
6. 对于统计查询使用GROUP BY和聚合函数

用户查询意图：{{intent}}
提取的实体：{{entities}}
额外参数：{{params}}

请生成优化的SQL查询语句，并返回JSON格式：
{{
  "sql_query": "完整的SQL查询语句",
  "explanation": "查询逻辑的中文解释",
  "confidence": 0.0-1.0之间的置信度,
  "estimated_rows": "预估返回行数范围",
  "optimization_notes": "优化说明"
}}

SQL查询："""
    
    def _format_schema_for_prompt(self) -> str:
        """格式化数据库模式信息用于提示"""
        schema_text = ""
        
        for table_name, table_info in self.schema_info["tables"].items():
            schema_text += f"\n{table_name} ({table_info['description']}):\n"
            for col in table_info["columns"]:
                schema_text += f"  - {col['name']} ({col['type']}): {col['description']}\n"
        
        schema_text += f"\n关系:\n"
        for rel in self.schema_info["relationships"]:
            schema_text += f"  - {rel}\n"
        
        return schema_text
    
    async def generate_sql(
        self, 
        intent: str, 
        entities: Dict[str, Any], 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用LLM生成SQL查询"""
        
        if params is None:
            params = {}
        
        try:
            # 构建提示
            prompt = self.sql_generation_prompt.format(
                intent=intent,
                entities=json.dumps(entities, ensure_ascii=False),
                params=json.dumps(params, ensure_ascii=False)
            )
            
            # 调用LLM
            response = await self._call_llm(prompt, max_tokens=800)
            result = json.loads(self._extract_json(response))
            
            # 验证和优化SQL
            validated_result = await self._validate_and_optimize_sql(result, intent, entities)
            
            logger.info(f"LLM SQL生成完成: {intent} -> {len(validated_result['sql_query'])} chars")
            return validated_result
            
        except Exception as e:
            logger.error(f"LLM SQL生成错误: {e}")
            # 降级到模板基础生成
            return await self._fallback_template_based(intent, entities, params)
    
    async def _validate_and_optimize_sql(
        self, 
        result: Dict[str, Any], 
        intent: str, 
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证和优化生成的SQL"""
        
        sql_query = result.get("sql_query", "")
        
        # 基本SQL注入检查
        dangerous_patterns = [
            r';\s*(drop|delete|truncate|alter|create)\s+',
            r'union\s+select',
            r'--\s*$',
            r'/\*.*\*/',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_query.lower()):
                logger.warning(f"检测到潜在的SQL注入模式: {pattern}")
                raise Exception("生成的SQL包含潜在的安全风险")
        
        # 添加默认限制
        if "limit" not in sql_query.lower() and intent != "query_statistics":
            if sql_query.strip().endswith(';'):
                sql_query = sql_query.strip()[:-1] + " LIMIT 50;"
            else:
                sql_query += " LIMIT 50"
        
        # 优化查询性能
        optimized_sql = await self._optimize_query_performance(sql_query, intent)
        
        result.update({
            "sql_query": optimized_sql,
            "validation_passed": True,
            "security_check": "passed",
            "performance_optimized": True
        })
        
        return result
    
    async def _optimize_query_performance(self, sql_query: str, intent: str) -> str:
        """优化查询性能"""
        
        optimization_prompt = f"""
请优化以下PostgreSQL查询的性能，保持查询逻辑不变：

原始查询：
{sql_query}

查询意图：{intent}

优化要求：
1. 确保使用了合适的索引字段作为WHERE条件
2. 避免不必要的子查询
3. 使用EXPLAIN ANALYZE友好的写法
4. 保持结果集的正确性

请只返回优化后的SQL语句："""
        
        try:
            optimized = await self._call_llm(optimization_prompt, max_tokens=600)
            # 提取SQL语句
            sql_match = re.search(r'SELECT.*?(?=\n\n|\n[A-Z]|\Z)', optimized, re.DOTALL | re.IGNORECASE)
            if sql_match:
                return sql_match.group(0).strip()
        except:
            logger.info("SQL优化失败，使用原始查询")
        
        return sql_query
    
    async def generate_complex_query(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """直接从自然语言生成复杂查询"""
        
        complex_prompt = f"""
用户输入了一个复杂的数据库查询请求。请理解用户意图并生成相应的PostgreSQL查询。

用户输入："{user_input}"
{f"上下文：{json.dumps(context, ensure_ascii=False)}" if context else ""}

数据库模式：
{self._format_schema_for_prompt()}

请分析用户需求并生成查询，返回JSON格式：
{{
  "interpreted_intent": "理解的用户意图",
  "sql_query": "完整的SQL查询语句",
  "explanation": "查询逻辑解释",
  "confidence": 0.0-1.0之间的置信度,
  "assumptions": ["做出的假设"],
  "alternative_queries": ["可选的查询方案"]
}}

分析结果："""
        
        try:
            response = await self._call_llm(complex_prompt, max_tokens=1000)
            result = json.loads(self._extract_json(response))
            
            # 验证复杂查询
            if result.get("sql_query"):
                result = await self._validate_and_optimize_sql(
                    result, "complex_query", {}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"复杂查询生成错误: {e}")
            return {
                "interpreted_intent": "无法理解的查询",
                "sql_query": "",
                "explanation": f"查询生成失败: {e}",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def explain_query(self, sql_query: str) -> Dict[str, Any]:
        """解释SQL查询的作用"""
        
        explain_prompt = f"""
请用中文解释以下PostgreSQL查询的作用和逻辑：

SQL查询：
{sql_query}

数据库模式：
{self._format_schema_for_prompt()}

请返回JSON格式的解释：
{{
  "purpose": "查询的主要目的",
  "step_by_step": ["逐步执行逻辑"],
  "tables_involved": ["涉及的表"],
  "key_conditions": ["关键过滤条件"],
  "expected_result": "预期结果描述",
  "performance_notes": "性能注意事项"
}}

解释结果："""
        
        try:
            response = await self._call_llm(explain_prompt, max_tokens=600)
            return json.loads(self._extract_json(response))
        except Exception as e:
            logger.error(f"查询解释错误: {e}")
            return {
                "purpose": "查询解释失败",
                "error": str(e)
            }
    
    async def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """调用本地Llama3.2模型"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stop": ["```", "---", "===", "\n\n#"]
        }
        
        try:
            response = requests.post(
                f"{self.llm_endpoint}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 处理Ollama流式响应
            result = ""
            for line in response.text.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        result += data['response']
                    if data.get('done', False):
                        break
            
            return result.strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API调用失败: {e}")
            raise Exception(f"LLM服务不可用: {e}")
    
    def _extract_json(self, text: str) -> str:
        """从LLM响应中提取JSON"""
        # 尝试找到JSON块
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            # 选择最长的JSON（通常是最完整的）
            return max(matches, key=len)
        
        # 如果没有找到，尝试修复
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        
        raise ValueError("无法从响应中提取有效的JSON")
    
    async def _fallback_template_based(
        self, 
        intent: str, 
        entities: Dict[str, Any], 
        params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """降级到模板基础的SQL生成"""
        logger.info("降级到模板基础SQL生成")
        
        try:
            from .sql_generator import sql_generator
            sql_query = sql_generator.generate_sql(intent, entities, params)
            
            return {
                "sql_query": sql_query,
                "explanation": f"使用模板生成的{intent}查询",
                "confidence": 0.7,
                "generation_method": "template_fallback",
                "validation_passed": True
            }
        except Exception as e:
            logger.error(f"模板SQL生成也失败: {e}")
            return {
                "sql_query": "",
                "explanation": "SQL生成失败",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def get_supported_intents(self) -> List[str]:
        """获取支持的意图类型"""
        return [
            "query_book_by_title",
            "query_book_by_author", 
            "query_book_by_category",
            "query_borrowing_records",
            "query_student_borrowing",
            "query_statistics",
            "query_overdue_books",
            "query_book_inventory",
            "complex_query"
        ]

# 全局实例
llm_sql_generator = LLMSQLGenerator()

async def generate_sql_with_llm(
    intent: str,
    entities: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """使用LLM生成SQL的便捷函数"""
    return await llm_sql_generator.generate_sql(intent, entities, params)
