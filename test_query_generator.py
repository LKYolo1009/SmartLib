#!/usr/bin/env python3
"""
查询生成器测试脚本
测试NLU到API查询的转换功能
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def test_query_generation(query, expected_endpoint=None, expected_requires_clarification=False):
    """测试查询生成功能"""
    print(f"\n{'='*60}")
    print(f"测试查询: {query}")
    print(f"{'='*60}")
    
    try:
        # 发送查询生成请求
        response = requests.post(
            f"{BASE_URL}/api/v1/query/test",
            params={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ 查询生成成功!")
            print(f"📋 原始查询: {result['original_query']}")
            
            # NLU结果
            nlu_result = result['nlu_result']
            print(f"🎯 NLU意图: {nlu_result['intent']}")
            print(f"🎯 NLU置信度: {nlu_result['confidence']:.2f}")
            print(f"🏷️  NLU实体: {json.dumps(nlu_result['entities'], ensure_ascii=False, indent=2)}")
            
            # 生成的查询
            generated_query = result['generated_query']
            print(f"\n🔧 生成的查询:")
            print(f"   API端点: {generated_query['api_endpoint']}")
            print(f"   HTTP方法: {generated_query['method']}")
            print(f"   参数: {json.dumps(generated_query['parameters'], ensure_ascii=False, indent=2)}")
            print(f"   需要澄清: {generated_query['requires_clarification']}")
            
            if generated_query['clarification_message']:
                print(f"   澄清消息: {generated_query['clarification_message']}")
            
            if generated_query['sql_query']:
                print(f"   SQL查询: {generated_query['sql_query']}")
            
            # 验证预期结果
            if expected_endpoint and generated_query['api_endpoint'] != expected_endpoint:
                print(f"⚠️  端点不匹配: 期望 {expected_endpoint}, 实际 {generated_query['api_endpoint']}")
            
            if expected_requires_clarification != generated_query['requires_clarification']:
                print(f"⚠️  澄清需求不匹配: 期望 {expected_requires_clarification}, 实际 {generated_query['requires_clarification']}")
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def test_available_endpoints():
    """测试获取可用端点"""
    print(f"\n{'='*60}")
    print("测试获取可用端点")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/query/endpoints")
        if response.status_code == 200:
            result = response.json()
            print("✅ 可用端点映射:")
            print("意图映射:")
            for intent, config in result['intent_mappings'].items():
                print(f"  - {intent}: {config['endpoint']} ({config['method']})")
            print("特殊意图:")
            for intent, config in result['special_intents'].items():
                print(f"  - {intent}: {config['endpoint']} ({config['method']})")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始查询生成器测试")
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 测试获取可用端点
    test_available_endpoints()
    
    # 测试各种查询场景
    test_cases = [
        # 基础查询 - 不需要澄清
        ("查询图书库存", "/api/v1/book_copies", False),
        ("How many books are in stock?", "/api/v1/book_copies", False),
        
        # 按书名查询 - 不需要澄清
        ("查找《三体》这本书", "/api/v1/book_copies", False),
        ("Find the book 'The Three-Body Problem'", "/api/v1/book_copies", False),
        
        # 按作者查询 - 不需要澄清
        ("刘慈欣写的书", "/api/v1/book", False),
        ("Books by Liu Cixin", "/api/v1/book", False),
        
        # 按类别查询 - 不需要澄清
        ("科幻类图书", "/api/v1/book", False),
        ("Science fiction books", "/api/v1/book", False),
        
        # 借阅记录查询 - 不需要澄清
        ("查询借阅记录", "/api/v1/borrowing", False),
        ("Borrowing records", "/api/v1/borrowing", False),
        
        # 学生借阅查询 - 需要澄清（缺少学生ID）
        ("查询学生借阅情况", "", True),
        ("Student borrowing history", "", True),
        
        # 统计报表查询 - 不需要澄清
        ("统计热门图书", "/api/v1/statistics", False),
        ("Generate statistics report", "/api/v1/statistics", False),
        
        # 逾期图书查询 - 不需要澄清
        ("查询逾期图书", "/api/v1/statistics/overdue", False),
        ("Overdue books", "/api/v1/statistics/overdue", False),
        
        # 时间范围查询 - 不需要澄清
        ("最近30天的借阅记录", "/api/v1/borrowing", False),
        ("Last 7 days borrowing records", "/api/v1/borrowing", False),
        ("本月的统计报表", "/api/v1/statistics", False),
        ("上个月的逾期情况", "/api/v1/statistics/overdue", False),
        
        # 复杂查询 - 不需要澄清
        ("查询刘慈欣写的科幻类图书在本月的借阅情况", "/api/v1/borrowing", False),
        ("Find science fiction books by Liu Cixin borrowed this month", "/api/v1/borrowing", False),
        
        # 日期查询 - 不需要澄清
        ("2023年12月25日的借阅记录", "/api/v1/borrowing", False),
        ("Borrowing records on 2023-12-25", "/api/v1/borrowing", False),
        
        # 需要澄清的查询
        ("查找书", "", True),  # 缺少书名
        ("作者的书", "", True),  # 缺少作者名
        ("类别的书", "", True),  # 缺少类别名
        ("学号为的学生借阅情况", "", True),  # 缺少学生ID
        
        # 未知查询
        ("今天天气怎么样", "", True),
        ("What's the weather like today?", "", True),
    ]
    
    for test_case in test_cases:
        if len(test_case) == 3:
            query, expected_endpoint, expected_requires_clarification = test_case
            test_query_generation(query, expected_endpoint, expected_requires_clarification)
        else:
            query = test_case[0]
            test_query_generation(query)
    
    print(f"\n{'='*60}")
    print("🎉 查询生成器测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 