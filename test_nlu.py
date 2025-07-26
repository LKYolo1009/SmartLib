#!/usr/bin/env python3
"""
NLU模块测试脚本
测试自然语言理解功能的各种场景
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def test_nlu_parse(query, expected_intent=None, expected_entities=None):
    """测试NLU解析功能"""
    print(f"\n{'='*60}")
    print(f"测试查询: {query}")
    print(f"{'='*60}")
    
    try:
        # 发送NLU解析请求
        response = requests.post(
            f"{BASE_URL}/api/v1/nlu/parse",
            json={"query": query}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 解析成功")
            print(f"意图: {result['intent']}")
            print(f"置信度: {result['confidence']:.2f}")
            print(f"实体: {json.dumps(result['entities'], ensure_ascii=False, indent=2)}")
            
            # 验证预期结果
            if expected_intent and result['intent'] != expected_intent:
                print(f"⚠️  意图不匹配: 期望 {expected_intent}, 实际 {result['intent']}")
            
            if expected_entities:
                for entity_type, expected_value in expected_entities.items():
                    if entity_type in result['entities']:
                        actual_value = result['entities'][entity_type]
                        if actual_value != expected_value:
                            print(f"⚠️  实体不匹配 {entity_type}: 期望 {expected_value}, 实际 {actual_value}")
                    else:
                        print(f"⚠️  缺少预期实体: {entity_type}")
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def test_available_intents():
    """测试获取可用意图"""
    print(f"\n{'='*60}")
    print("测试获取可用意图")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/nlu/intents")
        if response.status_code == 200:
            result = response.json()
            print("✅ 可用意图:")
            for intent, description in result['intent_descriptions'].items():
                print(f"  - {intent}: {description}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def test_available_entities():
    """测试获取可用实体"""
    print(f"\n{'='*60}")
    print("测试获取可用实体")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/nlu/entities")
        if response.status_code == 200:
            result = response.json()
            print("✅ 可用实体:")
            for entity, description in result['entity_descriptions'].items():
                print(f"  - {entity}: {description}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始NLU模块测试")
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 测试获取可用意图和实体
    test_available_intents()
    test_available_entities()
    
    # 测试各种查询场景
    test_cases = [
        # 图书库存查询
        ("查询图书库存", "query_book_inventory"),
        ("How many books are in stock?", "query_book_inventory"),
        
        # 按书名查询
        ("查找《三体》这本书", "query_book_by_title", {"book_title": "三体"}),
        ("搜索三体这本书", "query_book_by_title", {"book_title": "三体"}),
        ("Find the book 'The Three-Body Problem'", "query_book_by_title", {"book_title": "The Three-Body Problem"}),
        
        # 按作者查询
        ("刘慈欣写的书", "query_book_by_author", {"author_name": "刘慈欣"}),
        ("作者是刘慈欣的书", "query_book_by_author", {"author_name": "刘慈欣"}),
        ("Books by Liu Cixin", "query_book_by_author", {"author_name": "Liu Cixin"}),
        
        # 按类别查询
        ("科幻类图书", "query_book_by_category", {"category_name": "科幻"}),
        ("类别是科幻的书", "query_book_by_category", {"category_name": "科幻"}),
        ("Science fiction books", "query_book_by_category", {"category_name": "Science fiction"}),
        
        # 借阅记录查询
        ("查询借阅记录", "query_borrowing_records"),
        ("借书历史", "query_borrowing_records"),
        ("Borrowing records", "query_borrowing_records"),
        
        # 学生借阅查询
        ("学号为12345678的学生借阅情况", "query_student_borrowing", {"student_id": "12345678"}),
        ("学生12345678的借书记录", "query_student_borrowing", {"student_id": "12345678"}),
        ("Student 12345678 borrowing history", "query_student_borrowing", {"student_id": "12345678"}),
        
        # 统计报表查询
        ("统计热门图书", "query_statistics"),
        ("分析借阅趋势", "query_statistics"),
        ("Generate statistics report", "query_statistics"),
        
        # 逾期图书查询
        ("查询逾期图书", "query_overdue_books"),
        ("超期的书", "query_overdue_books"),
        ("Overdue books", "query_overdue_books"),
        
        # 时间范围查询
        ("最近30天的借阅记录", "query_borrowing_records", {"time_range": "last_30_days"}),
        ("本月的统计报表", "query_statistics", {"time_range": "this_month"}),
        ("上个月的逾期情况", "query_overdue_books", {"time_range": "last_month"}),
        ("Last 7 days borrowing records", "query_borrowing_records", {"time_range": "last_7_days"}),
        
        # 复杂查询
        ("查询刘慈欣写的科幻类图书在本月的借阅情况", "query_borrowing_records", {
            "author_name": "刘慈欣", 
            "category_name": "科幻", 
            "time_range": "this_month"
        }),
        
        # 日期查询
        ("2023年12月25日的借阅记录", "query_borrowing_records", {"date": "2023-12-25"}),
        ("2023-12-25的借书情况", "query_borrowing_records", {"date": "2023-12-25"}),
        
        # 未知查询
        ("今天天气怎么样", "unknown"),
        ("What's the weather like today?", "unknown"),
    ]
    
    for test_case in test_cases:
        if len(test_case) == 2:
            query, expected_intent = test_case
            test_nlu_parse(query, expected_intent)
        elif len(test_case) == 3:
            query, expected_intent, expected_entities = test_case
            test_nlu_parse(query, expected_intent, expected_entities)
    
    print(f"\n{'='*60}")
    print("🎉 NLU模块测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 