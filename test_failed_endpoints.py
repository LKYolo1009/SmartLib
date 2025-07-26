import requests
import json
from datetime import datetime
import traceback

# 只测失败的端点
BASE_URL = "http://localhost:8000"

# 测试数据
TEST_DATA = {
    "student": {
        "matric_number": "A1234567B",
        "telegram_id": "123456789"
    },
    "book_title": "Harry"
}

FAILED_ENDPOINTS = [
    {
        "desc": "GET /history/stats",
        "url": f"{BASE_URL}/api/v1/history/stats",
        "method": "get"
    },
    {
        "desc": "GET /history/active",
        "url": f"{BASE_URL}/api/v1/history/active",
        "method": "get"
    },
    {
        "desc": "GET /history/overdue",
        "url": f"{BASE_URL}/api/v1/history/overdue",
        "method": "get"
    },
    {
        "desc": "GET /book_copies/ (应为book_copies)",
        "url": f"{BASE_URL}/api/v1/book_copies/",
        "method": "get"
    },
    {
        "desc": "GET /book_copies/title/{title}/status (应为book_copies)",
        "url": f"{BASE_URL}/api/v1/book_copies/title/{TEST_DATA['book_title']}/status",
        "method": "get"
    },
    {
        "desc": "GET /borrowing/student/{identifier}",
        "url": f"{BASE_URL}/api/v1/borrowing/student/{TEST_DATA['student']['matric_number']}",
        "method": "get"
    },
    {
        "desc": "GET /borrowing/student/{identifier}/history",
        "url": f"{BASE_URL}/api/v1/borrowing/student/{TEST_DATA['student']['matric_number']}/history",
        "method": "get"
    },
    {
        "desc": "GET /borrowing/stats",
        "url": f"{BASE_URL}/api/v1/borrowing/stats",
        "method": "get"
    },
]

def print_and_collect(response, endpoint_desc, url):
    """打印并收集详细响应信息"""
    info = {
        "endpoint": endpoint_desc,
        "url": url,
        "status_code": None,
        "headers": None,
        "response_text": None,
        "response_json": None,
        "traceback": None
    }
    try:
        info["status_code"] = response.status_code
        info["headers"] = dict(response.headers)
        try:
            info["response_json"] = response.json()
        except Exception:
            info["response_text"] = response.text
    except Exception as e:
        info["traceback"] = traceback.format_exc()
    return info

def test_failed_endpoints():
    results = []
    for ep in FAILED_ENDPOINTS:
        try:
            resp = requests.request(ep["method"], ep["url"], timeout=10)
            info = print_and_collect(resp, ep["desc"], ep["url"])
        except Exception as e:
            info = {
                "endpoint": ep["desc"],
                "url": ep["url"],
                "status_code": None,
                "headers": None,
                "response_text": None,
                "response_json": None,
                "traceback": traceback.format_exc()
            }
        results.append(info)
    return results

def write_debug_results(results, filename="failed_endpoint_debug_results.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"失败端点详细调试结果\n{'='*60}\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for r in results:
            f.write(f"端点: {r['endpoint']}\n")
            f.write(f"URL: {r['url']}\n")
            f.write(f"状态码: {r['status_code']}\n")
            f.write(f"Headers: {json.dumps(r['headers'], ensure_ascii=False, indent=2)}\n")
            if r['response_json'] is not None:
                f.write(f"响应JSON: {json.dumps(r['response_json'], ensure_ascii=False, indent=2)}\n")
            if r['response_text'] is not None:
                f.write(f"响应文本: {r['response_text']}\n")
            if r['traceback']:
                f.write(f"Traceback:\n{r['traceback']}\n")
            f.write("-"*40+"\n")

def main():
    print("开始测试失败端点...")
    results = test_failed_endpoints()
    write_debug_results(results)
    print("测试完成，详细结果已写入 failed_endpoint_debug_results.txt")

if __name__ == "__main__":
    main() 