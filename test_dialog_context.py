#!/usr/bin/env python3
"""
对话上下文管理器测试脚本
测试Redis-based对话上下文管理功能
"""

import requests
import json
import time
import uuid

# API基础URL
BASE_URL = "http://localhost:8000"

def test_dialog_context_flow():
    """测试完整的对话上下文流程"""
    print("🚀 开始对话上下文管理器测试")
    print("=" * 60)
    
    # 生成测试用户ID和会话ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    print(f"测试用户ID: {user_id}")
    print(f"测试会话ID: {session_id}")
    print("=" * 60)
    
    # # 测试1: 检查Redis连接状态
    # print("\n📊 测试1: 检查Redis连接状态")
    # print("-" * 40)
    # try:
    #     response = requests.get(f"{BASE_URL}/api/v1/dialog/status")
    #     if response.status_code == 200:
    #         status = response.json()
    #         print(f"✅ Redis连接状态: {status['redis_connected']}")
    #         print(f"✅ 上下文TTL: {status['context_ttl']}秒")
    #         print(f"✅ 最大历史记录: {status['max_context_history']}条")
    #     else:
    #         print(f"❌ 状态检查失败: {response.status_code}")
    # except Exception as e:
    #     print(f"❌ 状态检查异常: {e}")
    
    # 测试2: 保存初始上下文
    print("\n💾 测试2: 保存初始上下文")
    print("-" * 40)
    initial_context = {
        "current_book": "三体",
        "current_author": "刘慈欣",
        "current_category": "科幻",
        "time_range": "this_month"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/dialog/context",
            json={
                "user_id": user_id,
                "context": initial_context,
                "session_id": session_id
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 上下文保存成功")
            print(f"   用户ID: {result['user_id']}")
            print(f"   上下文: {json.dumps(result['context'], ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 上下文保存失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 上下文保存异常: {e}")
    
    # 测试3: 获取上下文
    print("\n📖 测试3: 获取上下文")
    print("-" * 40)
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/dialog/context",
            params={"user_id": user_id, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result:
                print(f"✅ 上下文获取成功")
                print(f"   用户ID: {result['user_id']}")
                print(f"   上下文: {json.dumps(result['context'], ensure_ascii=False, indent=2)}")
                print(f"   时间戳: {result['timestamp']}")
            else:
                print("⚠️  没有找到上下文")
        else:
            print(f"❌ 上下文获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 上下文获取异常: {e}")
    
    # 测试4: 查询增强 - 图书对比
    print("\n🔄 测试4: 查询增强 - 图书对比")
    print("-" * 40)
    test_queries = [
        "对比《流浪地球》",
        "比较《球状闪电》",
        "vs《超新星纪元》",
        "还有《乡村教师》",
        "最近30天的借阅情况"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   子测试 {i}: {query}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/dialog/enhance",
                json={
                    "query": query,
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 原始查询: {result['original_query']}")
                print(f"   ✅ 增强查询: {result['enhanced_query']}")
                print(f"   ✅ 使用的上下文: {json.dumps(result['context_used'], ensure_ascii=False, indent=2)}")
                
                # 显示NLU结果
                nlu_result = result['nlu_result']
                print(f"   🎯 NLU意图: {nlu_result['intent']}")
                print(f"   🎯 NLU置信度: {nlu_result['confidence']:.2f}")
                print(f"   🏷️  NLU实体: {json.dumps(nlu_result['entities'], ensure_ascii=False, indent=2)}")
            else:
                print(f"   ❌ 查询增强失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 查询增强异常: {e}")
    
    # 测试5: 获取上下文历史
    print("\n📚 测试5: 获取上下文历史")
    print("-" * 40)
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/dialog/context/history",
            params={"user_id": user_id, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 历史记录获取成功")
            print(f"   用户ID: {result['user_id']}")
            print(f"   历史记录数量: {len(result['history'])}")
            
            for i, history_item in enumerate(result['history'], 1):
                print(f"   记录 {i}:")
                print(f"     时间戳: {history_item['timestamp']}")
                print(f"     上下文: {json.dumps(history_item['context'], ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 历史记录获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 历史记录获取异常: {e}")
    
    # 测试6: 多轮对话模拟
    print("\n💬 测试6: 多轮对话模拟")
    print("-" * 40)
    
    conversation_flow = [
        ("查询《三体》的库存", "第一轮：查询特定图书"),
        ("对比《流浪地球》", "第二轮：对比查询"),
        ("还有《球状闪电》", "第三轮：延续查询"),
        ("最近30天的借阅情况", "第四轮：时间范围查询")
    ]
    
    for i, (query, description) in enumerate(conversation_flow, 1):
        print(f"\n   轮次 {i}: {description}")
        print(f"   用户查询: {query}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/dialog/enhance",
                json={
                    "query": query,
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 增强查询: {result['enhanced_query']}")
                print(f"   ✅ 使用的上下文: {json.dumps(result['context_used'], ensure_ascii=False, indent=2)}")
                
                # 显示NLU结果
                nlu_result = result['nlu_result']
                print(f"   🎯 识别意图: {nlu_result['intent']}")
                print(f"   🎯 置信度: {nlu_result['confidence']:.2f}")
            else:
                print(f"   ❌ 处理失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 处理异常: {e}")
    
    # 测试7: 清除上下文
    print("\n🗑️  测试7: 清除上下文")
    print("-" * 40)
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v1/dialog/context",
            params={"user_id": user_id, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 上下文清除成功: {result['message']}")
        else:
            print(f"❌ 上下文清除失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 上下文清除异常: {e}")
    
    # 测试8: 验证清除结果
    print("\n🔍 测试8: 验证清除结果")
    print("-" * 40)
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/dialog/context",
            params={"user_id": user_id, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result is None:
                print("✅ 上下文已成功清除")
            else:
                print("⚠️  上下文仍然存在")
        else:
            print(f"❌ 验证失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 验证异常: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 对话上下文管理器测试完成")
    print("=" * 60)

def test_redis_fallback():
    """测试Redis不可用时的降级处理"""
    print("\n🔄 测试Redis降级处理")
    print("-" * 40)
    print("注意：此测试需要Redis服务器不可用才能验证降级功能")
    print("如果Redis可用，此测试将正常执行")
    
    user_id = f"fallback_test_{uuid.uuid4().hex[:8]}"
    
    try:
        # 尝试保存上下文
        response = requests.post(
            f"{BASE_URL}/api/v1/dialog/context",
            json={
                "user_id": user_id,
                "context": {"test": "fallback"}
            }
        )
        
        if response.status_code == 200:
            print("✅ 上下文保存成功（Redis可用）")
        elif response.status_code == 500:
            print("✅ 降级处理正常（Redis不可用）")
        else:
            print(f"⚠️  意外状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 降级测试异常: {e}")

if __name__ == "__main__":
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 运行主要测试
    test_dialog_context_flow()
    
    # 运行降级测试
    test_redis_fallback() 