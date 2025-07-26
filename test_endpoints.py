import requests
import json
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Any
import os

# 基础URL配置
BASE_URL = "http://localhost:8000/api/v1"

# 测试数据
TEST_DATA = {
    "student": {
        "matric_number": "A1234567B",
        "name": "Test Student",
        "email": "test@example.com",
        "telegram_id": "123456789"
    }
}

def print_progress(message: str) -> None:
    """打印进度信息"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def print_response(response: requests.Response, endpoint: str) -> None:
    """打印响应结果"""
    print(f"\n测试端点: {endpoint}")
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"响应内容: {response.text}")
    print("-" * 50)

def test_student_endpoints() -> List[Dict[str, Any]]:
    """测试学生相关端点"""
    results = []
    print_progress("开始测试学生相关端点...")
    
    # 获取学生列表
    response = requests.get(f"{BASE_URL}/student/")
    print_response(response, "GET /student/")
    results.append({"endpoint": "GET /student/", "status": response.status_code})
    
    # 搜索学生
    response = requests.get(f"{BASE_URL}/student/search?query={TEST_DATA['student']['matric_number']}")
    print_response(response, "GET /student/search")
    results.append({"endpoint": "GET /student/search", "status": response.status_code})
    
    # 更新学生信息
    if response.status_code == 200 and response.json():
        student = response.json()[0]
        update_data = {"name": "Updated Test Student"}
        response = requests.patch(f"{BASE_URL}/student/{student['matric_number']}", json=update_data)
        print_response(response, "PATCH /student/{identifier}")
        results.append({"endpoint": "PATCH /student/{identifier}", "status": response.status_code})
    
    return results

def test_history_endpoints() -> List[Dict[str, Any]]:
    """测试历史记录相关端点"""
    results = []
    print_progress("开始测试历史记录相关端点...")
    
    # 获取借阅统计
    response = requests.get(f"{BASE_URL}/history/stats")
    print_response(response, "GET /history/stats")
    results.append({"endpoint": "GET /history/stats", "status": response.status_code})
    
    # 获取当前借阅
    response = requests.get(f"{BASE_URL}/history/active")
    print_response(response, "GET /history/active")
    results.append({"endpoint": "GET /history/active", "status": response.status_code})
    
    # 获取逾期记录
    response = requests.get(f"{BASE_URL}/history/overdue")
    print_response(response, "GET /history/overdue")
    results.append({"endpoint": "GET /history/overdue", "status": response.status_code})
    
    return results

def test_book_endpoints() -> List[Dict[str, Any]]:
    """测试图书相关端点"""
    results = []
    print_progress("开始测试图书相关端点...")
    
    # 获取图书列表
    response = requests.get(f"{BASE_URL}/book/?limit=20")
    print_response(response, "GET /book/")
    results.append({"endpoint": "GET /book/", "status": response.status_code})
    
    # 通过ISBN搜索
    response = requests.get(f"{BASE_URL}/book/search/isbn/9780747532743")
    print_response(response, "GET /book/search/isbn/{isbn}")
    results.append({"endpoint": "GET /book/search/isbn/{isbn}", "status": response.status_code})
    
    # 通过索书号搜索
    response = requests.get(f"{BASE_URL}/book/search/call-number/800_ROW")
    print_response(response, "GET /book/search/call-number/{call_number}")
    results.append({"endpoint": "GET /book/search/call-number/{call_number}", "status": response.status_code})
    
    # 通过标题搜索
    response = requests.get(f"{BASE_URL}/book/search/title/Harry")
    print_response(response, "GET /book/search/title/{title}")
    results.append({"endpoint": "GET /book/search/title/{title}", "status": response.status_code})
    
    # 通过作者搜索
    response = requests.get(f"{BASE_URL}/book/search/author/Rowling")
    print_response(response, "GET /book/search/author/{author_name}")
    results.append({"endpoint": "GET /book/search/author/{author_name}", "status": response.status_code})
    
    # 通过出版商搜索
    response = requests.get(f"{BASE_URL}/book/search/publisher/Scholastic")
    print_response(response, "GET /book/search/publisher/{publisher_name}")
    results.append({"endpoint": "GET /book/search/publisher/{publisher_name}", "status": response.status_code})
    
    # 通过分类搜索
    response = requests.get(f"{BASE_URL}/book/search/category/Literature")
    print_response(response, "GET /book/search/category/{category_name}")
    results.append({"endpoint": "GET /book/search/category/{category_name}", "status": response.status_code})
    
    return results

def test_book_copy_endpoints() -> List[Dict[str, Any]]:
    """测试图书副本相关端点"""
    results = []
    print_progress("开始测试图书副本相关端点...")
    
    # 获取图书副本列表
    response = requests.get(f"{BASE_URL}/book-copy/")
    print_response(response, "GET /book-copy/")
    results.append({"endpoint": "GET /book-copy/", "status": response.status_code})
    
    # 获取特定图书的借阅状态
    response = requests.get(f"{BASE_URL}/book-copy/title/Harry/status")
    print_response(response, "GET /book-copy/title/{title}/status")
    results.append({"endpoint": "GET /book-copy/title/{title}/status", "status": response.status_code})
    
    return results

def test_borrowing_endpoints() -> List[Dict[str, Any]]:
    """测试借阅相关端点"""
    results = []
    print_progress("开始测试借阅相关端点...")
    
    # 获取所有借阅记录
    response = requests.get(f"{BASE_URL}/borrowing/")
    print_response(response, "GET /borrowing/")
    results.append({"endpoint": "GET /borrowing/", "status": response.status_code})
    
    # 获取学生借阅记录
    response = requests.get(f"{BASE_URL}/borrowing/student/{TEST_DATA['student']['matric_number']}")
    print_response(response, "GET /borrowing/student/{identifier}")
    results.append({"endpoint": "GET /borrowing/student/{identifier}", "status": response.status_code})
    
    # 获取学生借阅历史
    response = requests.get(f"{BASE_URL}/borrowing/student/{TEST_DATA['student']['matric_number']}/history")
    print_response(response, "GET /borrowing/student/{identifier}/history")
    results.append({"endpoint": "GET /borrowing/student/{identifier}/history", "status": response.status_code})
    
    # 获取逾期记录
    response = requests.get(f"{BASE_URL}/borrowing/overdue")
    print_response(response, "GET /borrowing/overdue")
    results.append({"endpoint": "GET /borrowing/overdue", "status": response.status_code})
    
    # 获取即将到期记录
    response = requests.get(f"{BASE_URL}/borrowing/due-soon")
    print_response(response, "GET /borrowing/due-soon")
    results.append({"endpoint": "GET /borrowing/due-soon", "status": response.status_code})
    
    # 获取热门图书
    response = requests.get(f"{BASE_URL}/borrowing/popular")
    print_response(response, "GET /borrowing/popular")
    results.append({"endpoint": "GET /borrowing/popular", "status": response.status_code})
    
    # 获取借阅统计
    response = requests.get(f"{BASE_URL}/borrowing/stats")
    print_response(response, "GET /borrowing/stats")
    results.append({"endpoint": "GET /borrowing/stats", "status": response.status_code})
    
    # 获取当前借阅
    response = requests.get(f"{BASE_URL}/borrowing/active")
    print_response(response, "GET /borrowing/active")
    results.append({"endpoint": "GET /borrowing/active", "status": response.status_code})
    
    return results

def test_metadata_endpoints() -> List[Dict[str, Any]]:
    """测试元数据相关端点"""
    results = []
    print_progress("开始测试元数据相关端点...")
    # Authors
    response = requests.get(f"{BASE_URL}/metadata/authors/")
    print_response(response, "GET /metadata/authors/")
    results.append({"endpoint": "GET /metadata/authors/", "status": response.status_code})

    # 新增作者
    author_data = {"author_name": "测试作者AI"}
    response = requests.post(f"{BASE_URL}/metadata/authors/", json=author_data)
    print_response(response, "POST /metadata/authors/")
    results.append({"endpoint": "POST /metadata/authors/", "status": response.status_code})
    if response.status_code == 201:
        author_id = response.json().get("author_id") or response.json().get("id")
        # 查询作者详情
        if author_id:
            response = requests.get(f"{BASE_URL}/metadata/authors/{author_id}")
            print_response(response, "GET /metadata/authors/{id}")
            results.append({"endpoint": "GET /metadata/authors/{id}", "status": response.status_code})

    # Categories
    response = requests.get(f"{BASE_URL}/metadata/categories")
    print_response(response, "GET /metadata/categories")
    results.append({"endpoint": "GET /metadata/categories", "status": response.status_code})

    # 新增分类
    category_data = {"category_code": "999", "category_name": "测试分类AI"}
    response = requests.post(f"{BASE_URL}/metadata/categories", json=category_data)
    print_response(response, "POST /metadata/categories")
    results.append({"endpoint": "POST /metadata/categories", "status": response.status_code})
    if response.status_code == 201:
        category_id = response.json().get("category_id") or response.json().get("id")
        # 查询分类详情
        if category_id:
            response = requests.get(f"{BASE_URL}/metadata/categories/{category_id}")
            print_response(response, "GET /metadata/categories/{id}")
            results.append({"endpoint": "GET /metadata/categories/{id}", "status": response.status_code})
            # 查询子分类
            response = requests.get(f"{BASE_URL}/metadata/categories/{category_id}/subcategories")
            print_response(response, "GET /metadata/categories/{id}/subcategories")
            results.append({"endpoint": "GET /metadata/categories/{id}/subcategories", "status": response.status_code})

    # Publishers
    response = requests.get(f"{BASE_URL}/metadata/publishers")
    print_response(response, "GET /metadata/publishers")
    results.append({"endpoint": "GET /metadata/publishers", "status": response.status_code})
    # 新增出版社
    publisher_data = {"publisher_name": "测试出版社AI"}
    response = requests.post(f"{BASE_URL}/metadata/publishers", json=publisher_data)
    print_response(response, "POST /metadata/publishers")
    results.append({"endpoint": "POST /metadata/publishers", "status": response.status_code})

    # Languages
    response = requests.get(f"{BASE_URL}/metadata/languages")
    print_response(response, "GET /metadata/languages")
    results.append({"endpoint": "GET /metadata/languages", "status": response.status_code})

    return results

def write_results_to_file(results: List[Dict[str, Any]], filename: str = "endpoint_test_results.txt") -> None:
    """将测试结果写入文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("API端点测试结果\n")
        f.write("=" * 50 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 统计成功和失败的端点
        success_count = sum(1 for r in results if 200 <= r["status"] < 300)
        fail_count = len(results) - success_count
        
        f.write(f"总测试端点数: {len(results)}\n")
        f.write(f"成功端点数: {success_count}\n")
        f.write(f"失败端点数: {fail_count}\n\n")
        
        # 列出所有端点及其状态
        f.write("详细测试结果:\n")
        f.write("-" * 50 + "\n")
        for result in results:
            status = "成功" if 200 <= result["status"] < 300 else "失败"
            f.write(f"端点: {result['endpoint']}\n")
            f.write(f"状态: {status} (状态码: {result['status']})\n")
            f.write("-" * 30 + "\n")
        
        # 列出失败的端点
        if fail_count > 0:
            f.write("\n失败的端点列表:\n")
            f.write("-" * 50 + "\n")
            for result in results:
                if not (200 <= result["status"] < 300):
                    f.write(f"- {result['endpoint']} (状态码: {result['status']})\n")

def main():
    """主函数"""
    print_progress("开始测试端点...")
    
    # 测试所有端点
    student_results = test_student_endpoints()
    history_results = test_history_endpoints()
    book_results = test_book_endpoints()
    book_copy_results = test_book_copy_endpoints()
    borrowing_results = test_borrowing_endpoints()
    metadata_results = test_metadata_endpoints()
    
    # 合并所有结果
    all_results = (
        student_results + 
        history_results + 
        book_results + 
        book_copy_results + 
        borrowing_results +
        metadata_results
    )
    
    # 将结果写入文件
    write_results_to_file(all_results)
    print_progress(f"测试完成，结果已写入 endpoint_test_results.txt")

if __name__ == "__main__":
    main() 