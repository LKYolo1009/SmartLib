import os
from dotenv import load_dotenv

# Load environment variables
# load_dotenv()
# Don't use load_dotenv in Docker unless you need a local .env for dev

# API Configuration
API_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

# API Endpoints
ENDPOINTS = {
    "kpi": f"{API_BASE_URL}/api/v1/statistics/kpi",
    "borrowing_trends": f"{API_BASE_URL}/api/v1/statistics/borrowing-trends",
    "categories": f"{API_BASE_URL}/api/v1/statistics/categories",
    "popular_books": f"{API_BASE_URL}/api/v1/statistics/popular-books",
    "student_activity": f"{API_BASE_URL}/api/v1/statistics/student-activity",
    "overdue": f"{API_BASE_URL}/api/v1/statistics/overdue",
    "library_utilization": f"{API_BASE_URL}/api/v1/statistics/library-utilization",
    "category_trends": f"{API_BASE_URL}/api/v1/statistics/category-trends",
    "daily": f"{API_BASE_URL}/api/v1/statistics/daily",
    "copies": f"{API_BASE_URL}/api/v1/book_copies/?limit=9999",
    "books": f"{API_BASE_URL}/api/v1/book/?limit=9999",
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    "title": "Smart Library Admin Dashboard",
    "theme": {
        "primary_color": "#1f77b4",
        "secondary_color": "#ff7f0e",
        "success_color": "#2ca02c",
        "warning_color": "#ffbb33",
        "danger_color": "#ff4444"
    }
}

# Cache Configuration
CACHE_CONFIG = {
    "ttl": 300  # 5 minutes
}

# Chart Configuration
CHART_CONFIG = {
    "template": "plotly_white",
    "height": 400,
    "colors": {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "success": "#2ca02c",
        "warning": "#ffbb33",
        "danger": "#ff4444"
    }
} 