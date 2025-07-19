#!/usr/bin/env python3
"""
智能查询服务完整测试示例
演示如何使用自然语言查询图书馆管理系统
"""

import asyncio
import json
from typing import Dict, Any
import logging

# 模拟数据库连接和服务实例
class MockDB:
    def execute(self, query):
        # 返回模拟的查询结果
        class MockResult:
            def fetchall(self):
                return [
                    ("001", "三国演义", "罗贯中", "古典文学", "available", "good", "A001", "A区1层"),
                    ("002", "三国演义", "罗贯中", "古典文学", "borrowed", "good", "A002", "A区1层")
                ]
            def keys(self):
                return ["copy_id", "title", "author_name", "category_name", "status", "condition", "call_number", "shelf_location"]
        return MockResult()

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_nlu_pipeline():
    """测试完整的NLU处理流水线"""
    print("=" * 60)
    print("智能图书馆查询系统 - 完整功能演示")
    print("=" * 60)
    
    # 导入我们的服务
    try:
        from app.services.nlu_processor import nlu_processor
        from app.services.sql_generator import sql_generator
        from app.services.intelligent_query_service import intelligent_query_service
    except ImportError:
        print("注意：这是模拟演示，实际使用需要在正确的Python环境中运行")
        print("以下展示预期的功能和结果：")
        await demo_mock_functionality()
        return

    # 测试用例
    test_cases = [
        {
            "input": "查找《三国演义》",
            "description": "按书名查询"
        },
        {
            "input": "鲁迅的作品有哪些？",
            "description": "按作者查询"
        },
        {
            "input": "计算机类别的书籍",
            "description": "按类别查询"
        },
        {
            "input": "张三的借阅记录",
            "description": "学生借阅查询"
        },
        {
            "input": "最热门的10本书",
            "description": "统计查询"
        },
        {
            "input": "有哪些逾期的书？",
            "description": "逾期图书查询"
        }
    ]
    
    db = MockDB()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {test_case['description']}")
        print(f"用户输入: \"{test_case['input']}\"")
        print("-" * 50)
        
        try:
            # 1. NLU处理
            nlu_result = nlu_processor.process_text(test_case['input'])
            print(f"意图识别: {nlu_result['intent']}")
            print(f"实体提取: {nlu_result['entities']}")
            print(f"置信度: {nlu_result['confidence']:.2f}")
            
            # 2. SQL生成
            if nlu_result['intent'] != 'unknown':
                sql_query = sql_generator.generate_sql(
                    nlu_result['intent'],
                    nlu_result['entities']
                )
                print(f"生成SQL: {sql_query[:100]}...")
            
            # 3. 完整查询处理
            complete_result = await intelligent_query_service.process_natural_query(
                test_case['input'], db
            )
            print(f"自然语言响应: {complete_result.get('natural_response', '无响应')}")
            print(f"查询状态: {complete_result.get('status', '未知')}")
            
        except Exception as e:
            print(f"处理错误: {e}")

async def demo_mock_functionality():
    """演示模拟功能"""
    
    demo_results = [
        {
            "input": "查找《三国演义》",
            "intent": "query_book_by_title",
            "entities": {"book_title": "三国演义"},
            "confidence": 0.95,
            "sql": "SELECT * FROM book_copies bc JOIN books b ON bc.book_id = b.book_id WHERE b.title ILIKE '%三国演义%'",
            "response": "找到 2 本相关图书：三国演义 - 罗贯中 (available)；三国演义 - 罗贯中 (borrowed)",
            "results": [
                {"title": "三国演义", "author": "罗贯中", "status": "available"},
                {"title": "三国演义", "author": "罗贯中", "status": "borrowed"}
            ]
        },
        {
            "input": "鲁迅的作品有哪些？",
            "intent": "query_book_by_author",
            "entities": {"author_name": "鲁迅"},
            "confidence": 0.92,
            "sql": "SELECT DISTINCT b.title, a.author_name FROM books b JOIN authors a ON b.author_id = a.author_id WHERE a.author_name ILIKE '%鲁迅%'",
            "response": "找到该作者的 3 本作品：呐喊 - 鲁迅；彷徨 - 鲁迅；野草 - 鲁迅",
            "results": [
                {"title": "呐喊", "author": "鲁迅"},
                {"title": "彷徨", "author": "鲁迅"},
                {"title": "野草", "author": "鲁迅"}
            ]
        },
        {
            "input": "计算机类别的书籍",
            "intent": "query_book_by_category",
            "entities": {"category_name": "计算机"},
            "confidence": 0.88,
            "sql": "SELECT b.title, a.author_name, c.category_name FROM books b JOIN authors a ON b.author_id = a.author_id JOIN categories c ON b.category_id = c.category_id WHERE c.category_name ILIKE '%计算机%'",
            "response": "该类别下有 5 本图书：Python编程 - 张三；数据结构 - 李四；算法导论 - 王五",
            "results": [
                {"title": "Python编程", "author": "张三", "category": "计算机"},
                {"title": "数据结构", "author": "李四", "category": "计算机"},
                {"title": "算法导论", "author": "王五", "category": "计算机"}
            ]
        }
    ]
    
    for i, demo in enumerate(demo_results, 1):
        print(f"\n演示案例 {i}:")
        print(f"用户输入: \"{demo['input']}\"")
        print("-" * 50)
        print(f"意图识别: {demo['intent']}")
        print(f"实体提取: {json.dumps(demo['entities'], ensure_ascii=False)}")
        print(f"置信度: {demo['confidence']}")
        print(f"生成SQL: {demo['sql'][:100]}...")
        print(f"自然语言响应: {demo['response']}")
        print(f"结果数量: {len(demo['results'])}")

def demo_api_usage():
    """演示API使用方法"""
    print("\n" + "=" * 60)
    print("API使用示例")
    print("=" * 60)
    
    api_examples = [
        {
            "endpoint": "POST /api/v1/smart-query/ask",
            "description": "智能查询主接口",
            "request": {
                "query": "查找《三国演义》",
                "language": "zh",
                "context": {},
                "session_id": "user123-session456"
            },
            "response": {
                "status": "success",
                "intent": "query_book_by_title",
                "entities": {"book_title": "三国演义"},
                "confidence": 0.95,
                "results": [
                    {
                        "title": "三国演义",
                        "author": "罗贯中",
                        "status": "available",
                        "display_text": "三国演义 - 罗贯中 (available)"
                    }
                ],
                "natural_response": "找到 1 本相关图书：三国演义 - 罗贯中 (available)",
                "result_count": 1,
                "suggestions": ["您还可以查询该书的借阅情况", "查看相同类别的其他图书"]
            }
        },
        {
            "endpoint": "POST /api/v1/nlu/parse",
            "description": "NLU处理接口",
            "request": {
                "text": "鲁迅的作品",
                "language": "zh"
            },
            "response": {
                "intent": "query_book_by_author",
                "entities": {"author_name": "鲁迅"},
                "confidence": 0.92,
                "language": "zh",
                "sql_query": "SELECT DISTINCT b.title, a.author_name FROM books b...",
                "suggestions": ["您还可以查询该书的借阅情况"]
            }
        }
    ]
    
    for example in api_examples:
        print(f"\n{example['endpoint']}")
        print(f"功能: {example['description']}")
        print("\n请求示例:")
        print(json.dumps(example['request'], indent=2, ensure_ascii=False))
        print("\n响应示例:")
        print(json.dumps(example['response'], indent=2, ensure_ascii=False))
        print("-" * 50)

def demo_supported_queries():
    """演示支持的查询类型"""
    print("\n" + "=" * 60)
    print("支持的查询类型示例")
    print("=" * 60)
    
    query_categories = {
        "图书查询": [
            "查找《红楼梦》",
            "有《哈利波特》这本书吗？",
            "搜索书名包含'python'的图书",
            "这本书有吗？"
        ],
        "作者查询": [
            "鲁迅的作品有哪些？",
            "查找金庸写的书",
            "搜索作者是村上春树的图书",
            "莫言都写过什么书？"
        ],
        "类别查询": [
            "计算机类别的书籍",
            "文学作品有哪些？",
            "查看科学类图书",
            "历史类的书"
        ],
        "借阅记录": [
            "张三的借阅记录",
            "学号12345的借阅情况",
            "最近一个月的借阅记录",
            "查看我的借书历史"
        ],
        "统计信息": [
            "最热门的10本书",
            "借阅量最高的图书",
            "统计信息",
            "图书借阅分析"
        ],
        "逾期查询": [
            "有哪些逾期的书？",
            "逾期图书列表",
            "超期未还的书籍",
            "查看逾期情况"
        ]
    }
    
    for category, examples in query_categories.items():
        print(f"\n{category}:")
        for example in examples:
            print(f"  • {example}")

async def main():
    """主函数"""
    print("SmartLib 智能图书馆查询系统")
    print("Natural Language Understanding & SQL Generation Demo")
    
    # 运行完整测试
    await test_complete_nlu_pipeline()
    
    # 演示API使用
    demo_api_usage()
    
    # 展示支持的查询类型
    demo_supported_queries()
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)
    print("\n实际部署说明:")
    print("1. 确保PostgreSQL数据库运行并包含测试数据")
    print("2. 安装所有依赖包：pip install -r requirements.txt")
    print("3. 启动FastAPI服务器：uvicorn app.main:app --reload")
    print("4. 访问API文档：http://localhost:8000/docs")
    print("5. 使用智能查询接口：POST /api/v1/smart-query/ask")

if __name__ == "__main__":
    asyncio.run(main())
