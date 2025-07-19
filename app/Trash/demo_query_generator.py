#!/usr/bin/env python3
"""
查询生成器演示脚本
展示从自然语言到API查询的完整转换流程
"""

import requests
import json
import hanlp
import logging
import re

# HanLP模型初始化
hanlp_ner = hanlp.load(hanlp.pretrained.ner.MSRA_NER_BERT_BASE_ZH)
hanlp_cls = hanlp.load(hanlp.pretrained.classification.SENTA_BERT_BASE_ZH)

# 日志配置
logging.basicConfig(
    filename='nlu_inference.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def demo_complete_flow(query, server_url="http://localhost:8000"):
    """演示完整的NLU到查询生成流程"""
    print(f"\n🔍 原始查询: {query}")
    print("=" * 60)
    
    try:
        # 第一步：NLU解析
        print("📝 步骤1: NLU自然语言理解")
        print("-" * 30)
        
        nlu_response = requests.post(
            f"{server_url}/api/v1/nlu/parse",
            json={"query": query},
            timeout=10
        )
        
        if nlu_response.status_code != 200:
            print(f"❌ NLU解析失败: {nlu_response.status_code}")
            print(f"错误信息: {nlu_response.text}")
            return
        
        nlu_result = nlu_response.json()
        print(f"✅ 意图识别: {nlu_result['intent']}")
        print(f"✅ 置信度: {nlu_result['confidence']:.2f}")
        print(f"✅ 实体提取: {json.dumps(nlu_result['entities'], ensure_ascii=False, indent=2)}")
        
        # 第二步：查询生成
        print(f"\n🔧 步骤2: 查询生成")
        print("-" * 30)
        
        query_response = requests.post(
            f"{server_url}/api/v1/query/generate",
            json={"nlu_result": nlu_result},
            timeout=10
        )
        
        if query_response.status_code != 200:
            print(f"❌ 查询生成失败: {query_response.status_code}")
            print(f"错误信息: {query_response.text}")
            return
        
        query_result = query_response.json()
        
        if query_result['requires_clarification']:
            print(f"❓ 需要澄清: {query_result['clarification_message']}")
            print("💡 建议: 请提供更多信息以完成查询")
            return
        
        print(f"✅ API端点: {query_result['api_endpoint']}")
        print(f"✅ HTTP方法: {query_result['method']}")
        print(f"✅ 查询参数: {json.dumps(query_result['parameters'], ensure_ascii=False, indent=2)}")
        
        if query_result['sql_query']:
            print(f"✅ SQL查询: {query_result['sql_query']}")
        
        # 第三步：构建完整URL（可选）
        print(f"\n🌐 步骤3: 完整API调用")
        print("-" * 30)
        
        if query_result['parameters']:
            # 构建查询字符串
            query_string = "&".join([f"{k}={v}" for k, v in query_result['parameters'].items()])
            full_url = f"{server_url}{query_result['api_endpoint']}?{query_string}"
        else:
            full_url = f"{server_url}{query_result['api_endpoint']}"
        
        print(f"✅ 完整URL: {full_url}")
        print(f"✅ 调用方式: {query_result['method']} {full_url}")
        
        # 第四步：实际API调用（可选）
        print(f"\n🚀 步骤4: 执行API调用")
        print("-" * 30)
        
        try:
            if query_result['method'] == 'GET':
                api_response = requests.get(full_url, timeout=10)
            else:
                print("⚠️  当前只演示GET请求，其他方法需要特殊处理")
                return
            
            if api_response.status_code == 200:
                api_result = api_response.json()
                print(f"✅ API调用成功!")
                print(f"✅ 返回数据条数: {len(api_result) if isinstance(api_result, list) else 'N/A'}")
                print(f"✅ 数据预览: {json.dumps(api_result[:2] if isinstance(api_result, list) and len(api_result) > 2 else api_result, ensure_ascii=False, indent=2)}")
            else:
                print(f"⚠️  API调用返回状态码: {api_response.status_code}")
                print(f"⚠️  响应内容: {api_response.text[:200]}...")
                
        except Exception as e:
            print(f"⚠️  API调用异常: {e}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保FastAPI服务器正在运行")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def main():
    """主演示函数"""
    print("🚀 SmartLib 查询生成器完整流程演示")
    print("=" * 60)
    print("本演示将展示从自然语言到API调用的完整转换流程")
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
        
        # 统计报表
        "统计热门图书",
        "Generate statistics report",
        
        # 逾期图书
        "查询逾期图书",
        "Overdue books",
        
        # 时间范围查询
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
        
        # 需要澄清的查询
        "查找书",  # 缺少书名
        "作者的书",  # 缺少作者名
        "查询学生借阅情况",  # 缺少学生ID
    ]
    
    # 执行演示查询
    for i, query in enumerate(demo_queries, 1):
        print(f"\n📝 演示 {i}/{len(demo_queries)}")
        demo_complete_flow(query)
        
        # 在查询之间添加短暂延迟
        if i < len(demo_queries):
            input("\n按回车键继续下一个演示...")
    
    print("\n" + "=" * 60)
    print("🎉 查询生成器完整流程演示完成!")
    print("=" * 60)
    print("\n💡 总结:")
    print("- NLU模块负责理解用户意图和提取实体")
    print("- 查询生成器将NLU结果转换为具体的API调用")
    print("- 系统能够自动处理时间范围、实体验证等复杂逻辑")
    print("- 对于不完整的查询，系统会要求用户澄清")
    print("\n🔗 相关链接:")
    print("- API文档: http://localhost:8000/docs")
    print("- NLU测试: python test_nlu.py")
    print("- 查询生成器测试: python test_query_generator.py")

if __name__ == "__main__":
    main() 