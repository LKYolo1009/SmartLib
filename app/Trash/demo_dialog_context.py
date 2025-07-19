#!/usr/bin/env python3
"""
对话上下文管理器演示脚本
展示多轮对话的上下文管理和智能补全功能
"""

import requests
import json
import uuid

def demo_multi_turn_conversation():
    """演示多轮对话功能"""
    print("🚀 SmartLib 多轮对话演示")
    print("=" * 60)
    print("本演示将展示基于Redis的对话上下文管理功能")
    print("包括上下文存储、查询增强和多轮对话补全")
    print("=" * 60)
    
    # 生成测试用户ID和会话ID
    user_id = f"demo_user_{uuid.uuid4().hex[:8]}"
    session_id = f"demo_session_{uuid.uuid4().hex[:8]}"
    
    print(f"演示用户ID: {user_id}")
    print(f"演示会话ID: {session_id}")
    print("=" * 60)
    
    # 演示场景1: 图书查询和对比
    print("\n📚 演示场景1: 图书查询和对比")
    print("-" * 50)
    
    conversation_1 = [
        ("查询《三体》的库存", "第一轮：查询特定图书"),
        ("对比《流浪地球》", "第二轮：对比查询（自动补全为'对比《三体》和《流浪地球》'）"),
        ("还有《球状闪电》", "第三轮：延续查询（自动补全为'还有《球状闪电》，还有《三体》'）"),
        ("最近30天的借阅情况", "第四轮：时间范围查询（自动补全为'最近30天的借阅情况，时间范围是this_month'）")
    ]
    
    for i, (query, description) in enumerate(conversation_1, 1):
        print(f"\n🔄 轮次 {i}: {description}")
        print(f"👤 用户: {query}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/dialog/enhance",
                json={
                    "query": query,
                    "user_id": user_id,
                    "session_id": session_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 系统: {result['enhanced_query']}")
                
                if result['context_used']:
                    print(f"📝 使用的上下文: {json.dumps(result['context_used'], ensure_ascii=False, indent=2)}")
                
                # 显示NLU解析结果
                nlu_result = result['nlu_result']
                print(f"🎯 识别意图: {nlu_result['intent']}")
                print(f"🎯 置信度: {nlu_result['confidence']:.2f}")
                print(f"🏷️  提取实体: {json.dumps(nlu_result['entities'], ensure_ascii=False, indent=2)}")
            else:
                print(f"❌ 处理失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 处理异常: {e}")
    
    # 演示场景2: 作者查询和延续
    print("\n\n👨‍💻 演示场景2: 作者查询和延续")
    print("-" * 50)
    
    # 先保存作者上下文
    author_context = {
        "current_author": "刘慈欣",
        "current_category": "科幻"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/dialog/context",
            json={
                "user_id": user_id,
                "context": author_context,
                "session_id": session_id
            }
        )
        print("✅ 作者上下文已保存")
    except Exception as e:
        print(f"❌ 保存上下文失败: {e}")
    
    conversation_2 = [
        ("刘慈欣写的书", "第一轮：查询作者作品"),
        ("对比《球状闪电》", "第二轮：对比查询（自动补全为'对比《球状闪电》'）"),
        ("还有《超新星纪元》", "第三轮：延续查询"),
        ("本月的借阅情况", "第四轮：时间范围查询")
    ]
    
    for i, (query, description) in enumerate(conversation_2, 1):
        print(f"\n🔄 轮次 {i}: {description}")
        print(f"👤 用户: {query}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/dialog/enhance",
                json={
                    "query": query,
                    "user_id": user_id,
                    "session_id": session_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 系统: {result['enhanced_query']}")
                
                if result['context_used']:
                    print(f"📝 使用的上下文: {json.dumps(result['context_used'], ensure_ascii=False, indent=2)}")
                
                # 显示NLU解析结果
                nlu_result = result['nlu_result']
                print(f"🎯 识别意图: {nlu_result['intent']}")
                print(f"🎯 置信度: {nlu_result['confidence']:.2f}")
            else:
                print(f"❌ 处理失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 处理异常: {e}")
    
    # 演示场景3: 查看上下文历史
    print("\n\n📚 演示场景3: 查看上下文历史")
    print("-" * 50)
    
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/dialog/context/history",
            params={"user_id": user_id, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 历史记录获取成功")
            print(f"📊 历史记录数量: {len(result['history'])}")
            
            for i, history_item in enumerate(result['history'], 1):
                print(f"\n📝 记录 {i}:")
                print(f"   时间戳: {history_item['timestamp']}")
                print(f"   上下文: {json.dumps(history_item['context'], ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 历史记录获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 历史记录获取异常: {e}")
    
    # 演示场景4: 英文对话
    print("\n\n🌍 演示场景4: 英文对话")
    print("-" * 50)
    
    english_conversation = [
        ("Find books by Liu Cixin", "First round: Find author's books"),
        ("Compare with 'The Three-Body Problem'", "Second round: Compare books"),
        ("Also 'The Wandering Earth'", "Third round: Continue with more books"),
        ("Last 7 days borrowing records", "Fourth round: Time range query")
    ]
    
    for i, (query, description) in enumerate(english_conversation, 1):
        print(f"\n🔄 Round {i}: {description}")
        print(f"👤 User: {query}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/dialog/enhance",
                json={
                    "query": query,
                    "user_id": user_id,
                    "session_id": session_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🤖 System: {result['enhanced_query']}")
                
                if result['context_used']:
                    print(f"📝 Context used: {json.dumps(result['context_used'], ensure_ascii=False, indent=2)}")
                
                # 显示NLU解析结果
                nlu_result = result['nlu_result']
                print(f"🎯 Intent: {nlu_result['intent']}")
                print(f"🎯 Confidence: {nlu_result['confidence']:.2f}")
            else:
                print(f"❌ Processing failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Processing error: {e}")
    
    # 演示场景5: 清除上下文
    print("\n\n🗑️  演示场景5: 清除上下文")
    print("-" * 50)
    
    try:
        response = requests.delete(
            "http://localhost:8000/api/v1/dialog/context",
            params={"user_id": user_id, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 上下文清除成功: {result['message']}")
        else:
            print(f"❌ 上下文清除失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 上下文清除异常: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 多轮对话演示完成!")
    print("=" * 60)
    print("\n💡 功能总结:")
    print("- ✅ 基于Redis的上下文存储")
    print("- ✅ 智能查询补全和增强")
    print("- ✅ 多轮对话支持")
    print("- ✅ 中英文双语支持")
    print("- ✅ 上下文历史记录")
    print("- ✅ 自动上下文提取和更新")
    print("\n🔗 相关链接:")
    print("- API文档: http://localhost:8000/docs")
    print("- 对话上下文测试: python test_dialog_context.py")

def demo_redis_status():
    """演示Redis状态检查"""
    print("\n📊 Redis状态检查")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8000/api/v1/dialog/status")
        if response.status_code == 200:
            status = response.json()
            print(f"🔗 Redis连接状态: {'✅ 已连接' if status['redis_connected'] else '❌ 未连接'}")
            print(f"⏰ 上下文TTL: {status['context_ttl']}秒")
            print(f"📚 最大历史记录: {status['max_context_history']}条")
            
            if not status['redis_connected']:
                print("⚠️  注意: Redis未连接，上下文将存储在内存中")
        else:
            print(f"❌ 状态检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 状态检查异常: {e}")

if __name__ == "__main__":
    # 检查Redis状态
    demo_redis_status()
    
    # 运行多轮对话演示
    demo_multi_turn_conversation() 