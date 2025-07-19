#!/usr/bin/env python3
"""
自然语言理解处理器 (NLU Processor)
实现意图识别、实体抽取和置信度计算
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NLUResult:
    """NLU解析结果"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    original_query: str

class NLUProcessor:
    """自然语言理解处理器"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.time_patterns = self._load_time_patterns()
        self.category_mapping = self._load_category_mapping()
        
    def _load_intent_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """加载意图识别模式"""
        return {
            "query_book_inventory": {
                "zh": [
                    r"(查询|查看|看看).*?库存",
                    r"库存.*?(查询|情况)",
                    r"有多少.*?书",
                    r"书.*?(数量|库存)"
                ],
                "en": [
                    r"(stock|inventory|available).*?books?",
                    r"books?.*?(stock|inventory)",
                    r"how many.*?books?",
                    r"book.*?(count|quantity)"
                ]
            },
            
            "query_book_by_title": {
                "zh": [
                    r"(查找|查询|搜索).*?[《《](.+?)[》》]",
                    r"[《《](.+?)[》》].*?(查找|查询)",
                    r"(找|要|需要).*?书.*?叫.*?[《《](.+?)[》》]",
                    r"书名.*?(是|叫).*?[《《](.+?)[》》]"
                ],
                "en": [
                    r"find.*?book.*?['\"](.+?)['\"]",
                    r"['\"](.+?)['\"].*?book",
                    r"search.*?for.*?['\"](.+?)['\"]",
                    r"book.*?titled.*?['\"](.+?)['\"]"
                ]
            },
            
            "query_book_by_author": {
                "zh": [
                    r"([^，。！？\s]+)(写的|著的|创作的).*?书",
                    r"(.+?)作者.*?书",
                    r"作者.*?(是|为).*?([^，。！？\s]+).*?书",
                    r"([^，。！？\s]+).*?的作品"
                ],
                "en": [
                    r"books?\s+by\s+([^,\.!?]+)",
                    r"([^,\.!?]+)\'?s?\s+books?",
                    r"author.*?([^,\.!?]+).*?books?",
                    r"works?\s+by\s+([^,\.!?]+)"
                ]
            },
            
            "query_book_by_category": {
                "zh": [
                    r"([^，。！？\s]+)类.*?图书",
                    r"图书.*?([^，。！？\s]+)类",
                    r"([^，。！？\s]+).*?书籍",
                    r"类别.*?(是|为).*?([^，。！？\s]+)"
                ],
                "en": [
                    r"([a-zA-Z\s]+)\s+(books?|literature)",
                    r"(fiction|non-fiction|science|history|biography).*?books?",
                    r"books?.*?(fiction|non-fiction|science|history|biography)",
                    r"category.*?([a-zA-Z\s]+)"
                ]
            },
            
            "query_borrowing_records": {
                "zh": [
                    r"(查询|查看|统计).*?借阅.*?记录",
                    r"借阅.*?记录.*?(查询|查看)",
                    r"借书.*?(历史|记录|情况)",
                    r"(过去|最近|本月|上月).*?借阅"
                ],
                "en": [
                    r"(borrowing|lending).*?records?",
                    r"records?.*?(borrowing|lending)",
                    r"borrow.*?(history|records?)",
                    r"(recent|past|this|last).*?(month|week).*?borrowing"
                ]
            },
            
            "query_student_borrowing": {
                "zh": [
                    r"(学号|学生ID?|姓名)\s*[为是]?\s*([A-Z0-9\u4e00-\u9fa5]+).*?借阅",
                    r"学生.*?([A-Z0-9\u4e00-\u9fa5]+).*?借阅",
                    r"([A-Z0-9]+).*?学生.*?借书"
                ],
                "en": [
                    r"student\s+([A-Z0-9]+).*?borrowing",
                    r"borrowing.*?student\s+([A-Z0-9]+)",
                    r"([A-Z0-9]+).*?student.*?books?"
                ]
            },
            
            "query_statistics": {
                "zh": [
                    r"(统计|报表|分析).*?(热门|流行|受欢迎)",
                    r"热门.*?图书",
                    r"(数据|报告|趋势).*?(分析|统计)",
                    r"(最多|最受欢迎).*?书"
                ],
                "en": [
                    r"(statistics?|reports?|analytics?).*?(popular|trending)",
                    r"popular.*?books?",
                    r"(most|top).*?(borrowed|popular)",
                    r"trending.*?(books?|titles?)"
                ]
            },
            
            "query_overdue_books": {
                "zh": [
                    r"(查询|查看).*?逾期.*?图书",
                    r"逾期.*?图书.*?(查询|查看)",
                    r"(超期|过期).*?书",
                    r"未归还.*?书"
                ],
                "en": [
                    r"overdue.*?books?",
                    r"books?.*?overdue",
                    r"(late|expired).*?returns?",
                    r"unreturned.*?books?"
                ]
            }
        }
    
    def _load_entity_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """加载实体抽取模式"""
        return {
            "book_title": {
                "zh": [
                    r"[《《](.+?)[》》]",
                    r"书名.*?(是|叫|为).*?[《《](.+?)[》》]",
                    r"(找|要|查).*?[《《](.+?)[》》]"
                ],
                "en": [
                    r"['\"](.+?)['\"]",
                    r"book.*?['\"](.+?)['\"]",
                    r"titled.*?['\"](.+?)['\"]"
                ]
            },
            
            "author_name": {
                "zh": [
                    r"([^，。！？\s]+)(写的|著的|创作的)",
                    r"作者.*?(是|为).*?([^，。！？\s]+)",
                    r"([^，。！？\s]+).*?的作品"
                ],
                "en": [
                    r"by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                    r"author\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\'?s?\s+books?"
                ]
            },
            
            "category_name": {
                "zh": [
                    r"([^，。！？\s]+)类.*?图书",
                    r"([^，。！？\s]+).*?书籍",
                    r"类别.*?(是|为).*?([^，。！？\s]+)"
                ],
                "en": [
                    r"(fiction|non-fiction|science|history|biography|literature|mystery|romance|fantasy|horror)",
                    r"([a-zA-Z\s]+)\s+(books?|literature)"
                ]
            },
            
            "student_id": {
                "zh": [
                    r"学号.*?([A-Z0-9]+)",
                    r"学生.*?([A-Z0-9]+)",
                    r"([A-Z]\d{7}[A-Z])"
                ],
                "en": [
                    r"student\s+([A-Z0-9]+)",
                    r"ID\s+([A-Z0-9]+)",
                    r"([A-Z]\d{7}[A-Z])"
                ]
            },
            
            "date": {
                "zh": [
                    r"(\d{4})年(\d{1,2})月(\d{1,2})日",
                    r"(\d{4})-(\d{1,2})-(\d{1,2})",
                    r"(\d{1,2})/(\d{1,2})/(\d{4})"
                ],
                "en": [
                    r"(\d{4})-(\d{1,2})-(\d{1,2})",
                    r"(\d{1,2})/(\d{1,2})/(\d{4})",
                    r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
                ]
            }
        }
    
    def _load_time_patterns(self) -> Dict[str, List[str]]:
        """加载时间范围模式"""
        return {
            "this_month": [
                r"本月", r"这个月", r"当月", 
                r"this month", r"current month"
            ],
            "last_month": [
                r"上月", r"上个月", r"前月",
                r"last month", r"previous month"
            ],
            "this_year": [
                r"今年", r"本年", r"这一年",
                r"this year", r"current year"
            ],
            "last_year": [
                r"去年", r"上年", r"前年",
                r"last year", r"previous year"
            ],
            "last_7_days": [
                r"最近(7|七)天", r"过去(7|七)天", r"近一周",
                r"last 7 days", r"past 7 days", r"last week"
            ],
            "last_30_days": [
                r"最近(30|三十)天", r"过去(30|三十)天", r"近一个月",
                r"last 30 days", r"past 30 days"
            ]
        }
    
    def _load_category_mapping(self) -> Dict[str, str]:
        """加载类别映射"""
        return {
            # 中文到英文映射
            "科幻": "Science Fiction",
            "文学": "Literature", 
            "历史": "History",
            "计算机": "Computer Science",
            "小说": "Fiction",
            "传记": "Biography",
            "哲学": "Philosophy",
            "艺术": "Art",
            "医学": "Medicine",
            "工程": "Engineering",
            
            # 英文标准化
            "sci-fi": "Science Fiction",
            "biography": "Biography",
            "computer": "Computer Science"
        }
    
    def detect_language(self, query: str) -> str:
        """检测查询语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', query))
        total_chars = len(query.replace(' ', ''))
        
        if total_chars == 0:
            return "en"
        
        chinese_ratio = chinese_chars / total_chars
        return "zh" if chinese_ratio > 0.3 else "en"
    
    def extract_intent(self, query: str, language: str) -> Tuple[str, float]:
        """提取意图"""
        query_lower = query.lower()
        best_intent = "unknown"
        max_matches = 0
        
        for intent, patterns in self.intent_patterns.items():
            if language not in patterns:
                continue
                
            matches = 0
            for pattern in patterns[language]:
                if re.search(pattern, query_lower):
                    matches += 1
            
            if matches > max_matches:
                max_matches = matches
                best_intent = intent
        
        # 计算基础置信度
        confidence = min(0.9, 0.4 + (max_matches * 0.2))
        
        return best_intent, confidence
    
    def extract_entities(self, query: str, language: str) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        # 提取各类实体
        for entity_type, patterns in self.entity_patterns.items():
            if language not in patterns:
                continue
                
            for pattern in patterns[entity_type]:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        # 取第一个非空组
                        entity_value = next((g for g in match.groups() if g), None)
                        if entity_value:
                            entities[entity_type] = entity_value.strip()
                            break
            
            if entity_type in entities:
                # 特殊处理
                if entity_type == "category_name":
                    entities[entity_type] = self._normalize_category(entities[entity_type])
                elif entity_type == "date":
                    entities[entity_type] = self._normalize_date(entities[entity_type])
        
        # 提取时间范围
        time_range = self.extract_time_range(query, language)
        if time_range:
            entities["time_range"] = time_range
        
        return entities
    
    def extract_time_range(self, query: str, language: str) -> Optional[str]:
        """提取时间范围"""
        query_lower = query.lower()
        
        for time_range, patterns in self.time_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return time_range
        
        return None
    
    def _normalize_category(self, category: str) -> str:
        """标准化类别名称"""
        category = category.strip()
        return self.category_mapping.get(category, category)
    
    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式"""
        # 简单的日期标准化，转换为YYYY-MM-DD格式
        date_patterns = [
            (r"(\d{4})年(\d{1,2})月(\d{1,2})日", r"\1-\2-\3"),
            (r"(\d{1,2})/(\d{1,2})/(\d{4})", r"\3-\1-\2")
        ]
        
        for pattern, replacement in date_patterns:
            if re.match(pattern, date_str):
                return re.sub(pattern, replacement, date_str)
        
        return date_str
    
    def calculate_confidence(self, intent: str, entities: Dict[str, Any], query: str) -> float:
        """计算置信度"""
        base_confidence = 0.5
        
        # 意图匹配加分
        if intent != "unknown":
            base_confidence += 0.2
        
        # 实体数量加分
        entity_count = len(entities)
        entity_bonus = min(0.2, entity_count * 0.05)
        base_confidence += entity_bonus
        
        # 查询长度调整
        query_length = len(query.strip())
        if query_length > 5:
            length_factor = min(1.2, query_length / 10)
            base_confidence *= length_factor
        
        # 确保置信度在合理范围内
        return min(0.95, max(0.1, base_confidence))
    
    def process_text(self, text: str, language: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理文本并返回NLU结果 (规则基础版本)
        
        Args:
            text: 输入文本
            language: 语言设置
            context: 上下文信息
            
        Returns:
            NLU结果字典
        """
        # 使用现有的parse_query方法
        nlu_result = self.parse_query(text)
        
        return {
            "intent": nlu_result.intent,
            "entities": nlu_result.entities,
            "confidence": nlu_result.confidence,
            "language": language or self.detect_language(text),
            "original_text": text,
            "processing_method": "rule_based"
        }
    
    async def process_text_enhanced(
        self, 
        text: str, 
        language: Optional[str] = None, 
        context: Optional[Dict[str, Any]] = None,
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """
        增强版文本处理，支持LLM选项
        
        Args:
            text: 输入文本
            language: 语言设置
            context: 上下文信息
            use_llm: 是否使用LLM增强处理
        
        Returns:
            处理结果字典
        """
        if use_llm:
            try:
                # 尝试使用LLM处理
                from .llm_nlu_processor import llm_nlu_processor
                return await llm_nlu_processor.process_text(text, language, context)
            except ImportError:
                logger.warning("LLM处理器不可用，降级到规则处理")
            except Exception as e:
                logger.error(f"LLM处理失败，降级到规则处理: {e}")
        
        # 使用规则基础处理
        return self.process_text(text, language, context)

    def parse_query(self, query: str) -> NLUResult:
        """解析查询"""
        try:
            # 预处理
            query = query.strip()
            if not query:
                return NLUResult("unknown", {}, 0.1, query)
            
            # 语言检测
            language = self.detect_language(query)
            logger.info(f"检测到语言: {language}")
            
            # 意图识别
            intent, intent_confidence = self.extract_intent(query, language)
            logger.info(f"识别意图: {intent}, 置信度: {intent_confidence}")
            
            # 实体抽取
            entities = self.extract_entities(query, language)
            logger.info(f"提取实体: {entities}")
            
            # 计算最终置信度
            final_confidence = self.calculate_confidence(intent, entities, query)
            
            return NLUResult(
                intent=intent,
                entities=entities,
                confidence=final_confidence,
                original_query=query
            )
            
        except Exception as e:
            logger.error(f"NLU解析错误: {e}")
            return NLUResult("unknown", {}, 0.1, query)

# 全局实例
nlu_processor = NLUProcessor()

def parse_natural_language(query: str) -> NLUResult:
    """解析自然语言查询的便捷函数"""
    return nlu_processor.parse_query(query)
