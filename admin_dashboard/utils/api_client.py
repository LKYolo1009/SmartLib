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

# Configure logger
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
from config import ENDPOINTS, API_BASE_URL, CATEGORY_ID_MAPPING, LANGUAGE_CODE_MAPPING, ACQUISITION_TYPE_MAPPING, BOOK_CONDITION_MAPPING, BOOK_STATUS_MAPPING, BOOK_LOCATION_AREA_MAPPING

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
        
        # Ensure return shape stays faithful; unwrap only if explicit 'data' container is present
        if isinstance(data, list):
            logger.debug(f"Returning list data with {len(data)} items")
            return data
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], (list, dict)) and len(data.keys()) == 1:
                payload = data['data']
                kind = 'list' if isinstance(payload, list) else 'dict'
                logger.debug(f"Unwrapped dict container with {kind} data")
                return payload
            logger.debug("Returning dict data as-is")
            return data
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
        """Send a GET request"""
        url = f"{self.base_url}{endpoint}"
        return requests.get(url)
        
    def post(self, endpoint, json=None):
        """Send a POST request"""
        url = f"{self.base_url}{endpoint}"
        return requests.post(url, json=json)
        
    def put(self, endpoint, json=None):
        """Send a PUT request"""
        url = f"{self.base_url}{endpoint}"
        return requests.put(url, json=json)
        
    def delete(self, endpoint):
        """Send a DELETE request"""
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
    def get_kpi_metrics(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get KPI metrics.

        If a period is provided, aggregate period-aware metrics from existing endpoints:
        - books_borrowed: sum of borrowings in period
        - active_users: unique_readers from borrowing-trends in period
        - utilization_rate: average utilization in period
        - overdue_books: use backend KPI overdue or fallback to current overdue count
        - total_books: use backend KPI total_books
        - new_registrations: not tracked yet → 0
        """
        try:
            logger.debug("Fetching KPI baseline")
            kpi_baseline = fetch_api_data("kpi") or {}

            # If no period provided, return baseline KPI mapped to UI keys (or mock if unavailable)
            if not start_date or not end_date:
                if kpi_baseline:
                    return {
                        "total_books": kpi_baseline.get("total_books", 0),
                        "books_borrowed": kpi_baseline.get("active_borrows", 0),
                        "overdue_books": kpi_baseline.get("overdue_books", 0),
                        "active_users": kpi_baseline.get("total_students", 0),
                        "utilization_rate": kpi_baseline.get("return_rate", 0.0),
                        "new_registrations": 0
                    }
                logger.warning("KPI baseline missing; using mock")
            return {
                "total_books": 2500,
                "books_borrowed": 450,
                "overdue_books": 23,
                "active_users": 180,
                "utilization_rate": 85.2,
                "new_registrations": 12
            }

            # Period-aware: prefer backend KPI with dates
            params_dates = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            period_kpi = fetch_api_data("kpi", params_dates)
            if isinstance(period_kpi, dict) and period_kpi.get("total_books") is not None:
                return {
                    "total_books": period_kpi.get("total_books", 0),
                    "books_borrowed": period_kpi.get("active_borrows", 0),
                    "overdue_books": period_kpi.get("overdue_books", 0),
                    "active_users": period_kpi.get("total_students", 0),
                    "utilization_rate": period_kpi.get("return_rate", 0.0),
                    "new_registrations": 0
                }

            # Fallback: compute from other endpoints
            trend_full = APIClient.get_api_data("borrowing_trends", {**params_dates, "interval": "day"}) or {}
            unique_readers = int(trend_full.get("unique_readers", 0) or 0) if isinstance(trend_full, dict) else 0

            trend_series = APIClient.get_borrowing_trends(start_date, end_date)
            period_borrows = int(sum(max(0, int(item.get("borrowings", 0) or 0)) for item in trend_series)) if isinstance(trend_series, list) else 0

            util_df = APIClient.get_library_utilization(start_date, end_date)
            utilization_rate = float(util_df["utilization_rate"].mean()) if not util_df.empty else 0.0

            overdue_list = fetch_api_data("overdue") or []
            overdue_count = len(overdue_list) if isinstance(overdue_list, list) else int(kpi_baseline.get("overdue_books", 0) or 0)

            total_books = int(kpi_baseline.get("total_books", 0) or 0)

            result = {
                "total_books": total_books,
                "books_borrowed": period_borrows,
                "overdue_books": overdue_count,
                "active_users": unique_readers,
                "utilization_rate": utilization_rate,
                "new_registrations": 0
            }
            logger.debug(f"Period KPI computed (fallback): {result}")
            return result
        except Exception as e:
            logger.error(f"Error in get_kpi_metrics: {e}", exc_info=True)
            return {
                "total_books": kpi_baseline.get("total_books", 0) if 'kpi_baseline' in locals() else 0,
                "books_borrowed": 0,
                "overdue_books": kpi_baseline.get("overdue_books", 0) if 'kpi_baseline' in locals() else 0,
                "active_users": 0,
                "utilization_rate": 0.0,
                "new_registrations": 0
            }

    @staticmethod
    def get_borrowing_trends(start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get borrowing trends with normalization and mock fallback.

        Ensures returned records include 'date', 'borrowings', 'returns'. If API returns
        only totals or alternative keys, normalize them. If all values are zero or data
        missing, return an empty list to trigger friendly empty-state in charts.
        """
        try:
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            logger.debug(f"Fetching borrowing trends from {start_date} to {end_date}")
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            raw = fetch_api_data("borrowing_trends", params)

            # Normalize various possible shapes
            records: List[Dict] = []
            if isinstance(raw, dict):
                # Try common shapes
                daily = raw.get("daily") or raw.get("data") or raw.get("items")
                if isinstance(daily, list):
                    raw = daily
                else:
                    raw = []

            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    date_str = item.get("date") or item.get("day") or item.get("created_at")
                    bor = item.get("borrowings")
                    ret = item.get("returns")
                    # Alternate key names commonly used
                    if bor is None:
                        bor = item.get("borrow_count") or item.get("borrowed") or item.get("borrows") or 0
                    if ret is None:
                        ret = item.get("return_count") or item.get("returned") or 0
                    if date_str is None:
                        continue
                    try:
                        # Keep as YYYY-MM-DD string for chart; parsing done later
                        date_norm = pd.to_datetime(str(date_str)).strftime("%Y-%m-%d")
                    except Exception:
                        continue
                    try:
                        bor = int(bor)
                    except Exception:
                        bor = 0
                    try:
                        ret = int(ret)
                    except Exception:
                        ret = 0
                    records.append({"date": date_norm, "borrowings": bor, "returns": ret})

            if not records:
                logger.warning("Using mock borrowing trends data due to empty/invalid API data")
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                records = [{"date": d.strftime("%Y-%m-%d"), "borrowings": 15 + i % 10, "returns": 12 + i % 8}
                           for i, d in enumerate(dates)]

            # If sums are zero, return empty so chart shows friendly message
            total = sum(r.get("borrowings", 0) for r in records) + sum(r.get("returns", 0) for r in records)
            if total == 0:
                logger.info("Borrowing trends all zeros for selected range; returning empty for UI message")
                return []

            return records
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
            # Use date part only (no time component)
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            # Use date part only (no time component)
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
        data = fetch_api_data("overdue")  # use correct endpoint
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
        """Get library utilization with robust parsing and mock fallback.

        Accepts multiple API response shapes and normalizes to DataFrame(date, utilization_rate).
        utilization_rate is expressed in 0-100 percentage.
        """
        try:
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
            data = APIClient.get_api_data("library_utilization", params)
            logger.debug(f"Raw utilization data: {data}")
            
            # Normalize various shapes
            records: List[Dict] = []
            if isinstance(data, dict):
                # Preferred: { daily_utilization: { 'YYYY-MM-DD': value, ... } }
                daily = data.get("daily_utilization") or data.get("daily") or {}
                if isinstance(daily, dict):
                    for d, v in daily.items():
                        try:
                            date_norm = pd.to_datetime(str(d)).strftime("%Y-%m-%d")
                        except Exception:
                            continue
                        try:
                            val = float(v)
                        except Exception:
                            val = 0.0
                        # If looks like ratio (0-1), scale to percentage
                        if 0 <= val <= 1:
                            val *= 100.0
                        records.append({"date": date_norm, "utilization_rate": val})
                # Alternative: list under key
                elif isinstance(data.get("data"), list):
                    for item in data.get("data", []):
                        if not isinstance(item, dict):
                            continue
                        date_str = item.get("date") or item.get("day")
                        if not date_str:
                            continue
                        try:
                            date_norm = pd.to_datetime(str(date_str)).strftime("%Y-%m-%d")
                        except Exception:
                            continue
                        val = item.get("utilization_rate")
                        if val is None:
                            val = item.get("utilization")
                        if val is None:
                            # Try to infer from counts if provided
                            bor = item.get("borrowings") or item.get("borrow_count") or 0
                            total = item.get("total_books") or item.get("capacity") or 0
                            if total:
                                try:
                                    val = (float(bor) / float(total)) * 100.0
                                except Exception:
                                    val = 0.0
                            else:
                                val = 0.0
                        try:
                            val = float(val)
                        except Exception:
                            val = 0.0
                        if 0 <= val <= 1:
                            val *= 100.0
                        records.append({"date": date_norm, "utilization_rate": val})
            elif isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    date_str = item.get("date") or item.get("day")
                    if not date_str:
                        continue
                    try:
                        date_norm = pd.to_datetime(str(date_str)).strftime("%Y-%m-%d")
                    except Exception:
                        continue
                    val = item.get("utilization_rate")
                    if val is None:
                        val = item.get("utilization")
                    if val is None:
                        bor = item.get("borrowings") or item.get("borrow_count") or 0
                        total = item.get("total_books") or item.get("capacity") or 0
                        if total:
                            try:
                                val = (float(bor) / float(total)) * 100.0
                            except Exception:
                                val = 0.0
                        else:
                            val = 0.0
                    try:
                        val = float(val)
                    except Exception:
                        val = 0.0
                    if 0 <= val <= 1:
                        val *= 100.0
                    records.append({"date": date_norm, "utilization_rate": val})

            if not records:
                logger.warning("No utilization data received/parsed; returning empty frame for friendly UI message")
                return pd.DataFrame(columns=["date", "utilization_rate"])
            
            df = pd.DataFrame(records)
            # If all zeros, return empty to show friendly message upstream
            if df["utilization_rate"].fillna(0).sum() == 0:
                return pd.DataFrame(columns=["date", "utilization_rate"])
            return df
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
    
    @staticmethod
    def get_all_book_details():
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
                    "title": b.get("title", ""),
                    "isbn": b.get("isbn", ""),
                    "call_number": b.get("call_number", ""),
                    "author_name": b.get("author_name", ""),
                    "publisher_name": b.get("publisher_name", ""),
                    "publication_year": b.get("publication_year", 0),
                    "language_name": b.get("language_name", ""),
                    "category_name": b.get("category_name", ""),
                    "total_copies": b.get("total_copies", 0)
                }
                for b in books
            }

            # Enrich copies with required metadata
            result = []
            for c in copies:
                book_meta = book_map.get(c["book_id"], {
                    "title": "",
                    "isbn": "",
                    "call_number": "",
                    "author_name": "",
                    "publisher_name": "",
                    "publication_year": 0,
                    "language_name": "",
                    "category_name": "",
                    "total_copies": 0
                })
                result.append({
                    "id": c["copy_id"],  # Using copy_id as unique identifier
                    "title": book_meta["title"],
                    "isbn": book_meta["isbn"],
                    "call_number": book_meta["call_number"],
                    "author_name": book_meta["author_name"],
                    "publisher_name": book_meta["publisher_name"],
                    "publication_year": book_meta["publication_year"],
                    "language": book_meta["language_name"],
                    "category": book_meta["category_name"],
                    "total_copy": book_meta["total_copies"],
                    "acquisition_type": c.get("acquisition_type", ""),
                    "acquisition_date": c.get("acquisition_date", ""),
                    "price": c.get("price", 0.0),
                    "condition": c.get("condition", ""),
                    "status": c.get("status", ""),
                    "book_location": c.get("location_name", "")
                })

            return result
        except Exception as e:
            logger.error(f"Error in get_all_book_details: {e}", exc_info=True)
            st.error("❌ Failed to fetch book data from API.")
            return []
        

    # Function to add a new book and its copies
    @staticmethod
    def check_book_title_exists(title: str) -> bool:
        """Check if a book title already exists in the database"""
        try:
            url = ENDPOINTS["search_book_by_title"]
            # The endpoint expects the title as a path parameter
            search_url = f"{url}/{title}"
            response = requests.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                # If we get results, the title exists
                return len(data) > 0
            elif response.status_code == 404:
                # No results found, title doesn't exist
                return False
            else:
                # Other error status codes
                logger.error(f"Error checking book title: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error checking book title existence: {e}")
            return False

    @staticmethod
    def get_or_create_author_id(author_name: str) -> int:
        """Get existing author ID or create new author and return ID"""
        try:
            # First, search for existing author
            search_url = f"{ENDPOINTS['search_author_by_name']}/{author_name}"
            logger.debug(f"Searching for author with URL: {search_url}")
            response = requests.get(search_url)
            
            logger.debug(f"Search response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Search response data: {data}")
                if data and len(data) > 0:
                    # Author exists, return the first author's ID
                    author_id = data[0].get('author_id')
                    if author_id:
                        logger.info(f"Found existing author '{author_name}' with ID: {author_id}")
                        return author_id
            elif response.status_code == 404:
                logger.info(f"Author '{author_name}' not found in search, will try to create")
            else:
                logger.warning(f"Unexpected search response: {response.status_code} - {response.text}")
            
            # Author doesn't exist, create new one
            author_data = {"author_name": author_name}
            api_client = APIClient()
            # Extract just the path from the full URL
            create_endpoint = ENDPOINTS["create_author"].replace(API_BASE_URL, "")
            logger.debug(f"Creating author with endpoint: {create_endpoint}, data: {author_data}")
            response = api_client.post(create_endpoint, json=author_data)
            
            logger.debug(f"Create response status: {response.status_code}")
            logger.debug(f"Create response text: {response.text}")
            
            if response.status_code in [200, 201]:
                new_author = response.json()
                author_id = new_author.get('author_id')
                if author_id:
                    logger.info(f"Created new author '{author_name}' with ID: {author_id}")
                    return author_id
                else:
                    logger.error(f"Author creation response missing author_id: {new_author}")
                    return None
            elif response.status_code == 400:
                # Author already exists but search didn't find it
                logger.warning(f"Author '{author_name}' already exists but search didn't find it. This might indicate a search API issue.")
                # Try to get all authors and find the one we need
                return APIClient._find_author_by_name_fallback(author_name)
            else:
                logger.error(f"Failed to create author: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting/creating author: {e}")
            return None

    @staticmethod
    def _find_author_by_name_fallback(author_name: str) -> int:
        """Fallback method to find author by getting all authors and searching locally"""
        try:
            logger.info(f"Using fallback method to find author '{author_name}'")
            # Get all authors from the general authors endpoint
            response = requests.get(ENDPOINTS["author"])
            if response.status_code == 200:
                authors = response.json()
                logger.debug(f"Retrieved {len(authors)} authors from fallback endpoint")
                # Search for author by name
                for author in authors:
                    if author.get('author_name', '').lower() == author_name.lower():
                        author_id = author.get('author_id')
                        if author_id:
                            logger.info(f"Found author '{author_name}' with ID: {author_id} via fallback")
                            return author_id
                logger.warning(f"Author '{author_name}' not found even in fallback search")
                return None
            else:
                logger.error(f"Fallback author search failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error in fallback author search: {e}")
            return None

    @staticmethod
    def get_or_create_publisher_id(publisher_name: str) -> int:
        """Get existing publisher ID or create new publisher and return ID"""
        try:
            # First, search for existing publisher
            search_url = f"{ENDPOINTS['search_publisher_by_name']}/{publisher_name}"
            logger.debug(f"Searching for publisher with URL: {search_url}")
            response = requests.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Publisher exists, return the first publisher's ID
                    publisher_id = data[0].get('publisher_id')
                    if publisher_id:
                        logger.info(f"Found existing publisher '{publisher_name}' with ID: {publisher_id}")
                        return publisher_id
            elif response.status_code == 404:
                logger.info(f"Publisher '{publisher_name}' not found in search, will try to create")
            
            # Publisher doesn't exist, create new one
            publisher_data = {"publisher_name": publisher_name}
            api_client = APIClient()
            # Extract just the path from the full URL
            create_endpoint = ENDPOINTS["create_publisher"].replace(API_BASE_URL, "")
            response = api_client.post(create_endpoint, json=publisher_data)
            
            if response.status_code in [200, 201]:
                new_publisher = response.json()
                publisher_id = new_publisher.get('publisher_id')
                if publisher_id:
                    logger.info(f"Created new publisher '{publisher_name}' with ID: {publisher_id}")
                    return publisher_id
                else:
                    logger.error(f"Publisher creation response missing publisher_id: {new_publisher}")
                    return None
            elif response.status_code == 400:
                # Publisher already exists but search didn't find it
                logger.warning(f"Publisher '{publisher_name}' already exists but search didn't find it. This might indicate a search API issue.")
                # For now, we'll return None since we don't have a fallback endpoint for publishers
                return None
            else:
                logger.error(f"Failed to create publisher: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting/creating publisher: {e}")
            return None

    @staticmethod
    def get_or_create_location_id(location_name: str) -> int:
        """Get existing location ID or create new location and return ID"""
        try:
            # First, search for existing location
            search_url = f"{ENDPOINTS['search_location_by_name']}/{location_name}"
            logger.debug(f"Searching for location with URL: {search_url}")
            response = requests.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Location exists, return the first location's ID
                    location_id = data[0].get('location_id')
                    if location_id:
                        logger.info(f"Found existing location '{location_name}' with ID: {location_id}")
                        return location_id
            
            # Location doesn't exist, create new one
            location_data = {"location_name": location_name}
            api_client = APIClient()
            # Extract just the path from the full URL
            create_endpoint = ENDPOINTS["create_location"].replace(API_BASE_URL, "")
            response = api_client.post(create_endpoint, json=location_data)
            
            if response.status_code in [200, 201]:
                new_location = response.json()
                location_id = new_location.get('location_id')
                if location_id:
                    logger.info(f"Created new location '{location_name}' with ID: {location_id}")
                    return location_id
                else:
                    logger.error(f"Location creation response missing location_id: {new_location}")
                    return None
            else:
                logger.error(f"Failed to create location: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting/creating location: {e}")
            return None

    @staticmethod
    def add_new_book_details():
        """Add a new book and its specified number of copies"""
        try:
            # Extract form data from session state
            form_data = st.session_state.add_form
            
            # Get category ID and language code from mappings
            category_id = CATEGORY_ID_MAPPING.get(form_data['category'], 1)  # Default to 1 if not found
            language_code = LANGUAGE_CODE_MAPPING.get(form_data['language'], "EN")  # Default to EN if not found
            
            # Resolve author ID (search existing or create new)
            author_id = APIClient.get_or_create_author_id(form_data['author_name'])
            if author_id is None:
                st.error(f"Failed to resolve author ID for '{form_data['author_name']}'")
                return False
            
            # Resolve publisher ID (search existing or create new)
            publisher_id = APIClient.get_or_create_publisher_id(form_data['publisher_name'])
            if publisher_id is None:
                st.error(f"Failed to resolve publisher ID for '{form_data['publisher_name']}'")
                return False
            
            # Get location ID from mapping
            location_id = BOOK_LOCATION_AREA_MAPPING.get(form_data['location_area'])
            if location_id is None:
                st.error(f"Invalid location area: '{form_data['location_area']}'")
                return False
            
            book_data = {
                "author_id": author_id,
                "call_number": form_data['call_number'],
                "category_id": category_id,
                "initial_copies": form_data['total_copy'],  # Use user's input for initial copies
                "isbn": form_data['isbn'],
                "language_code": language_code,
                "publication_year": form_data['publication_year'],
                "publisher_id": publisher_id,
                "title": form_data['title']
            }

            # Create the book
            api_client = APIClient()
            # Extract just the path from the full URL
            create_endpoint = ENDPOINTS["create_book"].replace(API_BASE_URL, "")
            response = api_client.post(create_endpoint, json=book_data)
            if response.status_code != 201:
                st.error(f"Failed to create book: {response.text}")
                return False
            book = response.json()
            book_id = book.get("book_id")

            # The API automatically creates copies based on initial_copies
            if form_data['total_copy'] > 0:
                st.success(f"✅ Book and {form_data['total_copy']} copies created successfully")
            else:
                st.warning("⚠️ Book created with 0 copies. You may need to add copies manually.")
            
            return True
        except Exception as e:
            st.error(f"Error adding book and copies: {e}")
            return False

    def create_book_copy(self, copy_data: dict) -> bool:
        """Create a new book copy"""
        try:
            api_client = APIClient()
            # Extract just the path from the full URL
            create_endpoint = ENDPOINTS["create_book_copy"].replace(API_BASE_URL, "")
            response = api_client.post(create_endpoint, json=copy_data)
            
            if response.status_code != 201:
                st.error(f"Failed to create book copy: {response.text}")
                return False
            return True
        except Exception as e:
            st.error(f"Error creating book copy: {e}")
            return False
    
    def delete_book_copy(self, copy_id: int) -> bool:
        """Delete a book copy"""
        try:
            delete_endpoint = f"/api/v1/book_copies/{copy_id}"
            response = self.delete(delete_endpoint)
            
            if response.status_code not in [200, 204]:
                st.error(f"Failed to delete book copy: {response.text}")
                return False
            return True
        except Exception as e:
            st.error(f"Error deleting book copy: {e}")
            return False
    
    def delete_book(self, book_id: int) -> bool:
        """Delete a book"""
        try:
            delete_endpoint = f"/api/v1/book/{book_id}"
            response = self.delete(delete_endpoint)
            
            if response.status_code not in [200, 204]:
                st.error(f"Failed to delete book: {response.text}")
                return False
            return True
        except Exception as e:
            st.error(f"Error deleting book: {e}")
            return False

    def update_book_copy(self, copy_id: int, copy_data: dict) -> bool:
        """Update a book copy"""
        try:
            update_endpoint = f"/api/v1/book_copies/{copy_id}"
            response = self.put(update_endpoint, json=copy_data)
            
            if response.status_code not in [200, 201]:
                st.error(f"Failed to update book copy: {response.text}")
                return False
            return True
        except Exception as e:
            st.error(f"Error updating book copy: {e}")
            return False


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
    return APIClient(API_BASE_URL)