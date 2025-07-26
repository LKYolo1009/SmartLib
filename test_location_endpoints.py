#!/usr/bin/env python3
"""
测试新的位置QR码端点
"""

import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000"

def test_location_endpoints():
    """测试位置相关的端点"""
    
    print("=== 测试位置QR码端点 ===")
    
    # 1. 获取所有位置列表
    print("\n1. 获取所有位置列表:")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/book_copies/locations/list")
        if response.status_code == 200:
            locations = response.json()
            print(f"找到 {len(locations)} 个位置:")
            for location in locations:
                print(f"  - {location}")
        else:
            print(f"错误: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 获取所有图书副本
    print("\n2. 获取图书副本列表:")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/book_copies/", params={"limit": 5})
        if response.status_code == 200:
            copies = response.json()
            print(f"找到 {len(copies)} 个副本:")
            for copy in copies:
                print(f"  - 副本ID: {copy['copy_id']}, 标题: {copy.get('book_title', 'N/A')}, 位置: {copy.get('location_name', 'N/A')}")
                
                # 3. 测试获取副本位置QR码
                if copy.get('location_id'):
                    print(f"    测试获取位置QR码...")
                    qr_response = requests.get(f"{BASE_URL}/api/v1/book_copies/{copy['copy_id']}/location-qr")
                    if qr_response.status_code == 200:
                        location_info = qr_response.json()
                        print(f"    位置: {location_info['location_name']}")
                        print(f"    位置QR码: {location_info['qr_code']}")
                    else:
                        print(f"    获取位置QR码失败: {qr_response.status_code}")
        else:
            print(f"错误: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 4. 测试通过位置名称获取副本
    print("\n3. 测试通过位置名称获取副本:")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/book_copies/location/主书架A区", params={"limit": 3})
        if response.status_code == 200:
            copies = response.json()
            print(f"在主书架A区找到 {len(copies)} 个副本")
        else:
            print(f"错误: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_location_endpoints() 