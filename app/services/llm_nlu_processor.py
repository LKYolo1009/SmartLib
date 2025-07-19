#!/usr/bin/env python3
"""
LLM增强的自然语言理解处理器 (LLM-Enhanced NLU Processor)
使用Llama3.2进行更智能的意图识别和实体提取
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
import requests
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMNLUProcessor:
    """基于LLM的自然语言理解处理器"""
    
    def __init__(self, llm_endpoint: str = "http://localhost:11434", model_name: str = "llama3.2"):
        self.llm_endpoint = llm_endpoint
        self.model_name = model_name
        self.timeout = 30
        
        # 意图定义和示例
        self.intent_definitions = {
            "query_book_by_title": {
                "description": "用户想要根据书名查询图书信息",
                "examples": [
                    "查找《三国演义》",
                    "有《哈利波特》这本书吗？",
                    "搜索Python编程相关的书",
                    "找一下数据结构这本书"
                ],
                "entities": ["book_title"]
            },
            "query_book_by_author": {
                "description": "用户想要查询某个作者的作品",
                "examples": [
                    "鲁迅的作品有哪些？",
                    "查找金庸写的书",
                    "村上春树都有什么作品",
                    "莫言的小说"
                ],
                "entities": ["author_name"]
            },
            "query_book_by_category": {
                "description": "用户想要查询某个类别的图书",
                "examples": [
                    "计算机类别的书籍",
                    "文学作品有哪些？",
                    "科学类图书",
                    "历史相关的书"
                ],
                "entities": ["category_name"]
            },
            "query_borrowing_records": {
                "description": "用户想要查询借阅记录",
                "examples": [
                    "最近的借阅记录",
                    "本月借阅情况",
                    "查看借书历史",
                    "借阅记录统计"
                ],
                "entities": ["time_range", "date"]
            },
            "query_student_borrowing": {
                "description": "用户想要查询特定学生的借阅情况",
                "examples": [
                    "张三的借阅记录",
                    "学号12345的借阅情况",
                    "查看李明的借书记录",
                    "学生王小红借了什么书"
                ],
                "entities": ["student_id", "student_name"]
            },
            "query_statistics": {
                "description": "用户想要查询统计信息",
                "examples": [
                    "最热门的10本书",
                    "借阅量最高的图书",
                    "统计信息",
                    "图书借阅分析",
                    "热门书籍排行"
                ],
                "entities": ["time_range", "limit"]
            },
            "query_overdue_books": {
                "description": "用户想要查询逾期图书",
                "examples": [
                    "有哪些逾期的书？",
                    "逾期图书列表",
                    "超期未还的书籍",
                    "过期书籍查询"
                ],
                "entities": ["time_range"]
            },
            "query_book_inventory": {
                "description": "用户想要查询图书库存情况",
                "examples": [
                    "图书库存情况",
                    "哪些书可以借阅？",
                    "查看图书状态",
                    "可用图书列表"
                ],
                "entities": ["status", "condition"]
            }
        }
        
        # 实体类型定义
        self.entity_types = {
            "book_title": "图书标题或书名",
            "author_name": "作者姓名",
            "category_name": "图书类别或学科分类",
            "student_id": "学生学号",
            "student_name": "学生姓名",
            "status": "状态信息(可用、已借出、遗失等)",
            "condition": "图书状况(好、一般、差等)",
            "time_range": "时间范围(本月、上月、今年等)",
            "date": "具体日期",
            "limit": "数量限制"
        }
    
    async def process_text(
        self, 
        text: str, 
        language: Optional[str] = None, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用LLM处理自然语言输入"""
        try:
            # 检测语言
            if not language:
                language = await self._detect_language_llm(text)
            
            # 使用LLM进行意图识别
            intent_result = await self._classify_intent_llm(text, language, context)
            
            # 使用LLM进行实体提取
            entities_result = await self._extract_entities_llm(
                text, intent_result["intent"], language
            )
            
            # 计算置信度
            confidence = min(intent_result["confidence"], entities_result["confidence"])
            
            # 生成解释
            explanation = await self._generate_explanation_llm(
                text, intent_result["intent"], entities_result["entities"]
            )
            
            result = {
                "intent": intent_result["intent"],
                "entities": entities_result["entities"],
                "confidence": confidence,
                "language": language,
                "original_text": text,
                "explanation": explanation,
                "processing_method": "llm_enhanced",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"LLM NLU处理完成: {text} -> {result['intent']} ({confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"LLM NLU处理错误: {e}")
            # 降级到规则基础处理
            return await self._fallback_rule_based(text, language, context)
    
    async def _detect_language_llm(self, text: str) -> str:
        """使用LLM检测语言"""
        prompt = f"""
请检测以下文本的语言，只回答 'zh' (中文) 或 'en' (英文)：

文本："{text}"

语言："""
        
        try:
            response = await self._call_llm(prompt, max_tokens=10)
            language = response.strip().lower()
            return "zh" if "zh" in language else "en"
        except:
            # 降级到简单检测
            return "zh" if any('\u4e00' <= char <= '\u9fff' for char in text) else "en"
    
    async def _classify_intent_llm(
        self, 
        text: str, 
        language: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用LLM进行意图分类"""
        
        # 构建意图描述
        intent_descriptions = []
        for intent, info in self.intent_definitions.items():
            examples = "、".join(info["examples"][:2])
            intent_descriptions.append(f"- {intent}: {info['description']} (例如: {examples})")
        
        context_info = ""
        if context:
            context_info = f"\n对话上下文: {json.dumps(context, ensure_ascii=False)}"
        
        prompt = f"""
你是一个图书馆管理系统的自然语言理解专家。请分析用户输入的意图。

支持的意图类型：
{chr(10).join(intent_descriptions)}

用户输入："{text}"{context_info}

请分析并返回JSON格式结果：
{{
  "intent": "最匹配的意图类型",
  "confidence": 0.0-1.0之间的置信度分数,
  "reasoning": "判断理由"
}}

JSON结果："""
        
        try:
            response = await self._call_llm(prompt, max_tokens=200)
            result = json.loads(self._extract_json(response))
            
            # 验证意图是否有效
            if result["intent"] not in self.intent_definitions:
                result["intent"] = "unknown"
                result["confidence"] = 0.1
            
            return result
            
        except Exception as e:
            logger.error(f"LLM意图识别错误: {e}")
            return {"intent": "unknown", "confidence": 0.0, "reasoning": "LLM处理失败"}
    
    async def _extract_entities_llm(
        self, 
        text: str, 
        intent: str, 
        language: str
    ) -> Dict[str, Any]:
        """使用LLM进行实体提取"""
        
        if intent == "unknown":
            return {"entities": {}, "confidence": 0.0}
        
        # 获取相关实体类型
        relevant_entities = self.intent_definitions.get(intent, {}).get("entities", [])
        entity_descriptions = []
        for entity in relevant_entities:
            desc = self.entity_types.get(entity, entity)
            entity_descriptions.append(f"- {entity}: {desc}")
        
        prompt = f"""
你是一个实体提取专家。请从用户输入中提取相关实体信息。

用户输入："{text}"
意图类型：{intent}

需要提取的实体类型：
{chr(10).join(entity_descriptions)}

请返回JSON格式结果：
{{
  "entities": {{
    "entity_name": "提取的值",
    ...
  }},
  "confidence": 0.0-1.0之间的置信度分数,
  "extraction_notes": "提取说明"
}}

注意：
1. 只提取实际存在的实体，不要编造
2. 实体值要保持原始格式
3. 书名去掉书名号《》
4. 如果没有找到实体，entities为空对象{{}}

JSON结果："""
        
        try:
            response = await self._call_llm(prompt, max_tokens=300)
            result = json.loads(self._extract_json(response))
            
            # 清理和验证实体
            cleaned_entities = {}
            for entity, value in result.get("entities", {}).items():
                if entity in relevant_entities and value and str(value).strip():
                    # 清理书名中的书名号
                    if entity == "book_title":
                        value = re.sub(r'[《》""'']', '', str(value))
                    cleaned_entities[entity] = str(value).strip()
            
            result["entities"] = cleaned_entities
            return result
            
        except Exception as e:
            logger.error(f"LLM实体提取错误: {e}")
            return {"entities": {}, "confidence": 0.0, "extraction_notes": "LLM处理失败"}
    
    async def _generate_explanation_llm(
        self, 
        text: str, 
        intent: str, 
        entities: Dict[str, Any]
    ) -> str:
        """生成处理结果的解释"""
        
        prompt = f"""
请为自然语言理解的结果生成一个简短的中文解释。

用户输入："{text}"
识别意图：{intent}
提取实体：{json.dumps(entities, ensure_ascii=False)}

请用一句话解释系统是如何理解用户需求的："""
        
        try:
            response = await self._call_llm(prompt, max_tokens=100)
            return response.strip()
        except:
            return f"系统识别用户想要{self.intent_definitions.get(intent, {}).get('description', '进行查询')}"
    
    async def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """调用本地Llama3.2模型"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stop": ["```", "---", "==="]
        }
        
        try:
            # 使用Ollama API
            response = requests.post(
                f"{self.llm_endpoint}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Ollama返回流式响应，需要处理
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
            return matches[0]
        
        # 如果没有找到完整的JSON，尝试修复
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        
        raise ValueError("无法从响应中提取有效的JSON")
    
    async def _fallback_rule_based(
        self, 
        text: str, 
        language: Optional[str], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """降级到规则基础的处理"""
        logger.info("降级到规则基础NLU处理")
        
        # 导入原始处理器作为降级方案
        try:
            from .nlu_processor import nlu_processor
            return nlu_processor.process_text(text, language, context)
        except:
            return {
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0,
                "language": language or "zh",
                "original_text": text,
                "explanation": "系统暂时无法理解该请求",
                "processing_method": "fallback",
                "timestamp": datetime.now().isoformat()
            }
    
    async def batch_process(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量处理多个文本"""
        tasks = [self.process_text(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量处理第{i}个文本失败: {result}")
                processed_results.append({
                    "intent": "unknown",
                    "entities": {},
                    "confidence": 0.0,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "endpoint": self.llm_endpoint,
            "supported_intents": list(self.intent_definitions.keys()),
            "supported_entities": list(self.entity_types.keys()),
            "processing_method": "llm_enhanced"
        }

# 全局实例
llm_nlu_processor = LLMNLUProcessor()

async def process_text_with_llm(
    text: str, 
    language: Optional[str] = None, 
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """使用LLM处理文本的便捷函数"""
    return await llm_nlu_processor.process_text(text, language, context)
