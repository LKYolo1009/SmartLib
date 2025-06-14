"""
API client utilities for the admin dashboard
"""

import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import streamlit as st
import pytz
from typing import Dict, List, Optional
import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ENDPOINTS, API_BASE_URL

@st.cache_data(ttl=300)
def fetch_api_data(endpoint: str, params: dict = None) -> dict:
    """Fetch data from API with error handling"""
    try:
        url = ENDPOINTS.get(endpoint)
        if not url:
            logger.error(f"Unknown endpoint: {endpoint}")
            raise ValueError(f"Unknown endpoint: {endpoint}")
        
        logger.debug(f"Fetching data from {url} with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Received data: {data}")
        
        # 确保返回的数据格式正确
        if isinstance(data, list):
            logger.debug(f"Returning list data with {len(data)} items")
            return data
        elif isinstance(data, dict):
            result = data.get('data', [])
            logger.debug(f"Returning dict data with {len(result)} items")
            return result
        logger.warning(f"Unexpected data format: {type(data)}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API Connection Error: {str(e)}")
        st.error(f"API Connection Error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Data Processing Error: {str(e)}", exc_info=True)
        st.error(f"Data Processing Error: {str(e)}")
        return []

class APIClient:
    def __init__(self, base_url=None):
        """Initialize API client with optional base URL"""
        self.base_url = (base_url or API_BASE_URL).rstrip('/')
    
    # HTTP Methods for instance usage
    def get(self, endpoint):
        """发送GET请求"""
        url = f"{self.base_url}{endpoint}"
        return requests.get(url)
        
    def post(self, endpoint, data=None):
        """发送POST请求"""
        url = f"{self.base_url}{endpoint}"
        return requests.post(url, json=data)
        
    def put(self, endpoint, data=None):
        """发送PUT请求"""
        url = f"{self.base_url}{endpoint}"
        return requests.put(url, json=data)
        
    def delete(self, endpoint):
        """发送DELETE请求"""
        url = f"{self.base_url}{endpoint}"
        return requests.delete(url)

    # Static methods for library management system
    @staticmethod
    def get_api_data(endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Generic API call function"""
        try:
            url = ENDPOINTS.get(endpoint)
            if not url:
                raise ValueError(f"Unknown endpoint: {endpoint}")
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API call error: {str(e)}")
            return {}

    @staticmethod
    def get_kpi_metrics() -> Dict:
        """Get KPI metrics with mock data fallback"""
        logger.debug("Fetching KPI metrics")
        data = fetch_api_data("kpi")
        if not data:
            logger.warning("Using mock KPI data")
            return {
                "total_books": 2500,
                "books_borrowed": 450,
                "overdue_books": 23,
                "active_users": 180,
                "utilization_rate": 85.2,
                "new_registrations": 12
            }
        return data

    @staticmethod
    def get_borrowing_trends(start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get borrowing trends with mock data fallback"""
        try:
            # 确保日期时间对象有时区信息
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            logger.debug(f"Fetching borrowing trends from {start_date} to {end_date}")
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            data = fetch_api_data("borrowing_trends", params)
            if not data:
                logger.warning("Using mock borrowing trends data")
                # Mock data
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                return [{"date": date.strftime("%Y-%m-%d"), "borrowings": 15 + i % 10, "returns": 12 + i % 8} 
                       for i, date in enumerate(dates)]
            return data
        except Exception as e:
            logger.error(f"Error in get_borrowing_trends: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def get_category_stats() -> List[Dict]:
        """Get category statistics with mock data fallback"""
        data = fetch_api_data("categories")
        if data is None:
            return [
                {"category": "Fiction", "count": 450},
                {"category": "Technology", "count": 320},
                {"category": "History", "count": 280},
                {"category": "Arts", "count": 220},
                {"category": "Others", "count": 180}
            ]
        return data


    @staticmethod
    def get_popular_books(limit: int = 10, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get popular books with mock data fallback"""
        logger.debug(f"Fetching popular books with limit {limit}, start_date {start_date}, end_date {end_date}")
        params = {
            "limit": limit
        }
        if start_date:
            # 只保留日期部分，不包含时间
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            # 只保留日期部分，不包含时间
            params["end_date"] = end_date.strftime("%Y-%m-%d")
            
        data = fetch_api_data("popular_books", params)
        if not data:
            logger.warning("Using mock popular books data")
            return [
                {"title": f"Popular Book {i+1}", "author": f"Author {i+1}", "borrow_count": 25-i*2}
                for i in range(limit)
            ]
        return data

    @staticmethod
    def get_student_activity(limit: int = 10, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get student activity with mock data fallback"""
        logger.debug(f"Fetching student activity with limit {limit}, start_date {start_date}, end_date {end_date}")
        params = {
            "limit": limit
        }
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        data = fetch_api_data("student_activity", params)
        if not data:
            logger.warning("Using mock student activity data")
            return [
                {"student_name": f"Student {i+1}", "student_id": f"S{2024000+i}", "borrow_count": 15-i}
                for i in range(limit)
            ]
        return data

    @staticmethod
    def get_overdue_books() -> List[Dict]:
        """Get overdue books with mock data fallback"""
        data = fetch_api_data("overdue")
        if data is None:
            return [
                {
                    "title": f"Overdue Book {i+1}",
                    "student_name": f"Student {i+1}",
                    "days_overdue": 5 + i*2,
                    "due_date": (datetime.now() - timedelta(days=5+i*2)).strftime("%Y-%m-%d")
                }
                for i in range(5)
            ]
        return data

    @staticmethod
    def get_overdue_analysis() -> List[Dict]:
        """Get overdue analysis with mock data fallback"""
        logger.debug("Fetching overdue analysis")
        data = fetch_api_data("overdue")  # 使用正确的端点
        if not data:
            logger.warning("Using mock overdue analysis data")
            return [
                {"days_overdue": "1-3 days", "count": 8},
                {"days_overdue": "4-7 days", "count": 12},
                {"days_overdue": "8-14 days", "count": 6},
                {"days_overdue": "15+ days", "count": 3}
            ]
        return data

    @staticmethod
    def get_library_utilization(start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get library utilization with mock data fallback"""
        try:
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            # 直接使用 get_api_data 而不是 fetch_api_data
            data = APIClient.get_api_data("library_utilization", params)
            logger.debug(f"Raw utilization data: {data}")
            
            if not data:
                logger.warning("No utilization data received from API")
                return pd.DataFrame(columns=["date", "utilization_rate"])
            
            # 处理每日利用率数据
            daily_data = []
            for date, count in data.get("daily_utilization", {}).items():
                daily_data.append({
                    "date": date,
                    "utilization_rate": count
                })
            
            if daily_data:
                return pd.DataFrame(daily_data)
            else:
                logger.warning("No daily utilization data found in response")
                return pd.DataFrame(columns=["date", "utilization_rate"])
            
        except Exception as e:
            logger.error(f"Error in get_library_utilization: {str(e)}", exc_info=True)
            return pd.DataFrame(columns=["date", "utilization_rate"])

    @staticmethod
    def get_daily_stats(start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get daily statistics"""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        return APIClient.get_api_data("daily", params)

    @staticmethod
    def get_category_trends(start_date: datetime, end_date: datetime) -> Dict:
        """Get category trends"""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        return APIClient.get_api_data("category_trends", params)

    @staticmethod
    def get_default_date_range() -> tuple:
        """Get default date range (last 90 days)"""
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=90)
        return start_date, end_date

    @staticmethod
    def convert_to_dataframe(data: List[Dict]) -> pd.DataFrame:
        """Convert API response to DataFrame"""
        return pd.DataFrame(data)

    @staticmethod
    def get_book_copy_labels():
        """Fetch book copy data and enrich with book metadata"""
        try:
            copies_url = ENDPOINTS["copies"]
            books_url = ENDPOINTS["books"]

            # Fetch data
            copies_response = requests.get(copies_url)
            books_response = requests.get(books_url)
            copies_response.raise_for_status()
            books_response.raise_for_status()

            copies = copies_response.json()
            books = books_response.json()

            # Build book_id → metadata map
            book_map = {
                b["book_id"]: {
                    "isbn": b.get("isbn", ""),
                    "call_number": b.get("call_number", "")
                }
                for b in books
            }

            # Enrich copies with title, call number, and ISBN
            result = []
            for c in copies:
                book_meta = book_map.get(c["book_id"], {"isbn": "", "call_number": ""})
                result.append({
                    "qr_code": c["qr_code"],
                    "title": c["book_title"],
                    "call_number": book_meta["call_number"],
                    "isbn": book_meta["isbn"]
                })

            return result
        except Exception as e:
            logger.error(f"Error in get_book_copy_labels: {e}", exc_info=True)
            st.error("❌ Failed to fetch book label data from API.")
            return []


# Standalone functions for backward compatibility
def get_daily_stats(days: int = 90) -> pd.DataFrame:
    """Get daily statistics"""
    data = fetch_api_data("daily_stats", {"days": days})
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_category_stats() -> pd.DataFrame:
    """Get category statistics"""
    data = fetch_api_data("category_stats")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_overdue_books() -> pd.DataFrame:
    """Get overdue books list"""
    data = fetch_api_data("overdue_books")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_student_stats() -> pd.DataFrame:
    """Get student statistics"""
    data = fetch_api_data("student_stats")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_popular_books() -> pd.DataFrame:
    """Get popular books ranking"""
    data = fetch_api_data("popular_books")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_borrowing_trends() -> pd.DataFrame:
    """Get borrowing trends"""
    data = fetch_api_data("borrowing_trends")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_student_activity() -> pd.DataFrame:
    """Get student activity statistics"""
    data = fetch_api_data("student_activity")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_library_utilization() -> pd.DataFrame:
    """Get library utilization statistics"""
    data = fetch_api_data("library_utilization")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_overdue_analysis() -> pd.DataFrame:
    """Get overdue analysis"""
    data = fetch_api_data("overdue_analysis")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_category_trends() -> pd.DataFrame:
    """Get category trends"""
    data = fetch_api_data("category_trends")
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def get_api_client():
    """获取API客户端实例"""
    return APIClient(API_BASE_URL)