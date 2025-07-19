#!/usr/bin/env python3
"""
NLU模块演示脚本
展示自然语言理解功能的使用方法
"""

import requests
import json

def demo_nlu_query(query, server_url="http://localhost:8000"):
    """演示NLU查询"""
    print(f"\n🔍 查询: {query}")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{server_url}/api/v1/nlu/parse",
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 解析成功!")
            print(f"📋 意图: {result['intent']}")
            print(f"🎯 置信度: {result['confidence']:.2f}")
            
            if result['entities']:
                print(f"🏷️  实体:")
                for entity_type, value in result['entities'].items():
                    print(f"   - {entity_type}: {value}")
            else:
                print("🏷️  实体: 无")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保FastAPI服务器正在运行")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def main():
    """主演示函数"""
    print("🚀 SmartLib NLU模块演示")
    print("=" * 60)
    print("本演示将展示自然语言理解功能的各种查询场景")
    print("请确保FastAPI服务器正在运行 (uvicorn app.main:app --reload)")
    print("=" * 60)
    
    # 演示查询列表
    demo_queries = [
        # 基础查询
        "查询图书库存",
        "How many books are in stock?",
        
        # 按书名查询
        "查找《三体》这本书",
        "Find the book 'The Three-Body Problem'",
        
        # 按作者查询
        "刘慈欣写的书",
        "Books by Liu Cixin",
        
        # 按类别查询
        "科幻类图书",
        "Science fiction books",
        
        # 借阅记录
        "查询借阅记录",
        "Borrowing records",
        
        # 学生借阅
        "学号为12345678的学生借阅情况",
        "Student 12345678 borrowing history",
        
        # 统计报表
        "统计热门图书",
        "Generate statistics report",
        
        # 逾期图书
        "查询逾期图书",
        "Overdue books",
        
        # 时间范围
        "最近30天的借阅记录",
        "Last 7 days borrowing records",
        "本月的统计报表",
        "上个月的逾期情况",
        
        # 复杂查询
        "查询刘慈欣写的科幻类图书在本月的借阅情况",
        "Find science fiction books by Liu Cixin borrowed this month",
        
        # 日期查询
        "2023年12月25日的借阅记录",
        "Borrowing records on 2023-12-25",
        
        # 未知查询
        "今天天气怎么样",
        "What's the weather like today?"
    ]
    
    # 执行演示查询
    for i, query in enumerate(demo_queries, 1):
        print(f"\n📝 演示 {i}/{len(demo_queries)}")
        demo_nlu_query(query)
        
        # 在查询之间添加短暂延迟
        if i < len(demo_queries):
            input("\n按回车键继续下一个演示...")
    
    print("\n" + "=" * 60)
    print("🎉 NLU模块演示完成!")
    print("=" * 60)
    print("\n💡 提示:")
    print("- 您可以尝试自己的查询")
    print("- 访问 http://localhost:8000/docs 查看完整API文档")
    print("- 运行 python test_nlu.py 进行完整测试")

if __name__ == "__main__":
    main() 