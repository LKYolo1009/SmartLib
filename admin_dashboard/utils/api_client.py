"""
API client utilities for the admin dashboard
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import pytz
from typing import Dict, List, Optional
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ENDPOINTS, API_BASE_URL

@st.cache_data(ttl=300)
def fetch_api_data(endpoint: str, params: dict = None) -> dict:
    """Fetch data from API with error handling"""
    try:
        url = ENDPOINTS.get(endpoint)
        if not url:
            raise ValueError(f"Unknown endpoint: {endpoint}")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Data Processing Error: {str(e)}")
        return None

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
        data = fetch_api_data("kpi")
        if data is None:
            # Mock data for demo
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
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        data = fetch_api_data("borrowing_trends", params)
        if data is None:
            # Mock data
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            return [{"date": date.strftime("%Y-%m-%d"), "borrowings": 15 + i % 10, "returns": 12 + i % 8} 
                   for i, date in enumerate(dates)]
        return data.get("data", [])

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
    def get_popular_books(limit: int = 10) -> List[Dict]:
        """Get popular books with mock data fallback"""
        params = {"limit": limit}
        data = fetch_api_data("popular_books", params)
        if data is None:
            return [
                {"title": f"Popular Book {i+1}", "author": f"Author {i+1}", "borrow_count": 25-i*2}
                for i in range(limit)
            ]
        return data

    @staticmethod
    def get_student_activity(limit: int = 10) -> List[Dict]:
        """Get student activity with mock data fallback"""
        params = {"limit": limit}
        data = fetch_api_data("student_activity", params)
        if data is None:
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
        data = fetch_api_data("overdue_analysis")
        if data is None:
            return [
                {"days_overdue": "1-3 days", "count": 8},
                {"days_overdue": "4-7 days", "count": 12},
                {"days_overdue": "8-14 days", "count": 6},
                {"days_overdue": "15+ days", "count": 3}
            ]
        return data.get("data", [])

    @staticmethod
    def get_library_utilization(start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get library utilization with mock data fallback"""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        data = fetch_api_data("library_utilization", params)
        if data is None:
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            return [{"date": date.strftime("%Y-%m-%d"), "utilization_rate": 75 + (i % 20)} 
                   for i, date in enumerate(dates)]
        return data.get("data", [])

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