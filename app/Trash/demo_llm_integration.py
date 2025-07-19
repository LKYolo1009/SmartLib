#!/usr/bin/env python3
"""
LLM增强功能完整演示脚本
展示Llama3.2集成后的智能查询能力
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any, List
from datetime import datetime

class LLMQueryDemo:
    """LLM查询演示类"""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.session = requests.Session()
        
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_section(self, title: str):
        """打印节标题"""
        print(f"\n{'-'*50}")
        print(f"  {title}")
        print(f"{'-'*50}")
    
    def check_llm_status(self) -> Dict[str, Any]:
        """检查LLM服务状态"""
        try:
            response = self.session.get(f"{self.api_base}/api/v1/llm-query/llm-status")
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def llm_query(self, query: str, detailed: bool = False) -> Dict[str, Any]:
        """执行LLM增强查询"""
        payload = {
            "query": query,
            "use_llm": True,
            "detailed_response": detailed
        }
        
        start_time = time.time()
        try:
            response = self.session.post(
                f"{self.api_base}/api/v1/llm-query/ask",
                json=payload,
                timeout=120
            )
            result = response.json()
            result["_response_time"] = time.time() - start_time
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "_response_time": time.time() - start_time
            }
    
    def complex_query(self, query: str) -> Dict[str, Any]:
        """执行复杂查询"""
        payload = {"query": query}
        
        try:
            response = self.session.post(
                f"{self.api_base}/api/v1/llm-query/complex-query",
                json=payload,
                timeout=120
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def batch_query(self, queries: List[str]) -> Dict[str, Any]:
        """执行批量查询"""
        payload = {"queries": queries}
        
        try:
            response = self.session.post(
                f"{self.api_base}/api/v1/llm-query/batch-process",
                json=payload,
                timeout=300
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def demonstrate_basic_queries(self):
        """演示基本LLM增强查询"""
        self.print_header("LLM增强基本查询演示")
        
        basic_queries = [
            {
                "query": "帮我找找鲁迅写的小说作品，最好是比较有名的那种",
                "description": "复杂作者查询 + 语义理解"
            },
            {
                "query": "有没有适合初学者的Python编程书籍？",
                "description": "条件筛选 + 语义匹配"
            },
            {
                "query": "张三这个月借了哪些书？都是什么类型的？",
                "description": "学生查询 + 时间范围 + 分类信息"
            },
            {
                "query": "最近哪些图书比较热门？统计一下借阅情况",
                "description": "统计分析 + 时间感知"
            }
        ]
        
        for i, item in enumerate(basic_queries, 1):
            self.print_section(f"演示 {i}: {item['description']}")
            print(f"用户输入: \"{item['query']}\"")
            
            result = self.llm_query(item['query'], detailed=True)
            
            print(f"处理方法: {result.get('processing_method', 'unknown')}")
            print(f"响应时间: {result.get('_response_time', 0):.2f}s")
            print(f"识别意图: {result.get('intent', 'unknown')}")
            print(f"置信度: {result.get('nlu_confidence', 0):.2f}")
            
            if result.get('status') == 'success':
                print(f"自然语言响应: {result.get('natural_response', '')}")
                print(f"结果数量: {result.get('result_count', 0)}")
                
                if result.get('suggestions'):
                    print("智能建议:")
                    for suggestion in result['suggestions'][:3]:
                        print(f"  • {suggestion}")
            else:
                print(f"处理状态: {result.get('status')}")
                if result.get('error_message'):
                    print(f"错误信息: {result['error_message']}")
            
            time.sleep(1)  # 避免请求过于频繁
    
    def demonstrate_complex_queries(self):
        """演示复杂查询功能"""
        self.print_header("复杂查询分析演示")
        
        complex_queries = [
            {
                "query": "统计本月借阅量最高的科技类图书，同时显示这些书的作者信息和当前库存状态",
                "description": "多表关联 + 统计分析 + 条件筛选"
            },
            {
                "query": "查询今年新增的图书中，哪些还没有被任何学生借阅过，按类别分组显示",
                "description": "时间筛选 + 反向查询 + 分组统计"
            },
            {
                "query": "分析一下计算机专业学生的借阅偏好，看看他们最喜欢借什么类型的书",
                "description": "用户画像分析 + 偏好统计"
            }
        ]
        
        for i, item in enumerate(complex_queries, 1):
            self.print_section(f"复杂查询 {i}: {item['description']}")
            print(f"用户输入: \"{item['query']}\"")
            
            result = self.complex_query(item['query'])
            
            print(f"意图理解: {result.get('interpreted_intent', '未知')}")
            print(f"置信度: {result.get('confidence', 0):.2f}")
            
            if result.get('status') == 'success':
                print(f"查询解释: {result.get('explanation', '')}")
                print(f"结果数量: {result.get('result_count', 0)}")
                
                if result.get('sql_query'):
                    sql_preview = result['sql_query'][:150] + "..." if len(result['sql_query']) > 150 else result['sql_query']
                    print(f"生成SQL: {sql_preview}")
                
                if result.get('assumptions'):
                    print("查询假设:")
                    for assumption in result['assumptions']:
                        print(f"  • {assumption}")
                        
            else:
                print(f"处理状态: {result.get('status')}")
                if result.get('error'):
                    print(f"错误信息: {result['error']}")
            
            time.sleep(2)
    
    def demonstrate_batch_processing(self):
        """演示批量处理功能"""
        self.print_header("批量查询处理演示")
        
        batch_queries = [
            "查找《三国演义》",
            "鲁迅的作品有哪些？",
            "计算机类别的书籍",
            "最热门的5本书",
            "有哪些逾期的书？"
        ]
        
        print("批量查询列表:")
        for i, query in enumerate(batch_queries, 1):
            print(f"  {i}. {query}")
        
        print("\n开始批量处理...")
        start_time = time.time()
        
        result = self.batch_query(batch_queries)
        
        processing_time = time.time() - start_time
        print(f"批量处理完成，耗时: {processing_time:.2f}s")
        print(f"处理状态: {result.get('status')}")
        print(f"处理数量: {result.get('processed_count', 0)}")
        
        if result.get('results'):
            success_count = sum(1 for r in result['results'] if r.get('result', {}).get('status') == 'success')
            print(f"成功处理: {success_count}/{len(result['results'])}")
            
            print("\n批量结果摘要:")
            for i, item in enumerate(result['results'], 1):
                query = item['query']
                status = item.get('result', {}).get('status', 'unknown')
                
                if status == 'success':
                    result_count = item['result'].get('result_count', 0)
                    natural_response = item['result'].get('natural_response', '')[:50] + "..."
                    print(f"  {i}. {query} -> ✅ {result_count}条结果")
                    print(f"     {natural_response}")
                else:
                    error = item.get('error', 'unknown error')
                    print(f"  {i}. {query} -> ❌ {error}")
    
    def demonstrate_comparison(self):
        """演示LLM vs 规则系统对比"""
        self.print_header("LLM增强 vs 规则系统对比")
        
        comparison_queries = [
            "找找那些适合计算机专业学生看的编程入门书籍",
            "这个月学生们最爱借的都是什么类型的书？",
            "有没有那种讲人工智能基础知识的书，不要太难的"
        ]
        
        for i, query in enumerate(comparison_queries, 1):
            self.print_section(f"对比查询 {i}")
            print(f"查询: \"{query}\"")
            
            # LLM增强查询
            print("\n🤖 LLM增强处理:")
            llm_result = self.llm_query(query)
            print(f"  状态: {llm_result.get('status')}")
            print(f"  意图: {llm_result.get('intent', 'unknown')}")
            print(f"  置信度: {llm_result.get('nlu_confidence', 0):.2f}")
            print(f"  响应: {llm_result.get('natural_response', 'N/A')}")
            
            # 规则系统查询（模拟）
            print("\n📋 规则系统处理:")
            rule_result = self.llm_query(query.replace("适合", "").replace("入门", "").replace("基础知识", ""))
            print(f"  状态: {rule_result.get('status')}")
            print(f"  意图: {rule_result.get('intent', 'unknown')}")
            print(f"  响应: 基础关键词匹配查询")
            
            time.sleep(1)
    
    def demonstrate_capabilities(self):
        """演示系统能力"""
        self.print_header("系统能力展示")
        
        try:
            response = self.session.get(f"{self.api_base}/api/v1/llm-query/capabilities")
            capabilities = response.json()
            
            print("🚀 LLM增强功能:")
            for feature in capabilities.get('enhanced_features', []):
                print(f"  • {feature['name']}: {feature['description']}")
                if feature.get('examples'):
                    print(f"    示例: {feature['examples'][0]}")
            
            print(f"\n📊 支持的查询类型:")
            for query_type in capabilities.get('supported_query_types', []):
                print(f"  • {query_type}")
            
            print(f"\n⚡ 性能特性:")
            for perf_feature in capabilities.get('performance_features', []):
                print(f"  • {perf_feature}")
            
            print(f"\n⚠️ 使用限制:")
            for limitation in capabilities.get('limitations', []):
                print(f"  • {limitation}")
                
        except Exception as e:
            print(f"获取能力信息失败: {e}")
    
    def run_demo(self):
        """运行完整演示"""
        print("🎯 SmartLib LLM增强功能完整演示")
        print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查服务状态
        self.print_header("服务状态检查")
        status = self.check_llm_status()
        print(f"LLM服务状态: {status.get('status')}")
        
        if status.get('status') == 'healthy':
            print("✅ 所有服务正常运行")
            
            # 运行各种演示
            self.demonstrate_basic_queries()
            self.demonstrate_complex_queries()
            self.demonstrate_batch_processing()
            self.demonstrate_comparison()
            self.demonstrate_capabilities()
            
            # 演示总结
            self.print_header("演示总结")
            print("🎉 LLM增强功能演示完成!")
            print("\n主要优势:")
            print("  • 理解复杂、模糊的自然语言查询")
            print("  • 智能生成优化的SQL查询")
            print("  • 提供自然语言的结果解释")
            print("  • 支持上下文感知的查询处理")
            print("  • 具备降级保护机制")
            
            print(f"\n部署说明:")
            print("  1. 确保Ollama服务运行在 localhost:11434")
            print("  2. 确保已安装并下载 llama3.2 模型")
            print("  3. 启动SmartLib API服务")
            print("  4. 使用 /api/v1/llm-query/ask 接口进行查询")
            
        else:
            print("❌ LLM服务不可用")
            if status.get('error'):
                print(f"错误信息: {status['error']}")
            print("\n请检查:")
            print("  1. Ollama是否已启动: ollama serve")
            print("  2. Llama3.2是否已安装: ollama pull llama3.2")
            print("  3. 网络连接是否正常")

def main():
    """主函数"""
    demo = LLMQueryDemo()
    
    try:
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        print("请检查服务是否正常运行")

if __name__ == "__main__":
    main()
