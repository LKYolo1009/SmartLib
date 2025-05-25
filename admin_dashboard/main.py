import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.api_client import APIClient
from components.charts import (
    create_kpi_card,
    create_borrowing_trend_chart,
    create_category_pie_chart,
    create_popular_books_chart,
    create_student_activity_chart,
    create_overdue_analysis_chart,
    create_utilization_chart
)
from config import DASHBOARD_CONFIG, CACHE_CONFIG

# Page configuration
st.set_page_config(
    page_title=DASHBOARD_CONFIG["title"],
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stMetric > label {
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .section-header {
        border-left: 4px solid #667eea;
        padding-left: 1rem;
        margin: 2rem 0 1rem 0;
    }
    .error-message {
        padding: 1rem;
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .success-message {
        padding: 1rem;
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_data():
    """Get all dashboard data in one go to reduce API calls"""
    try:
        # Get all data
        kpi_data = APIClient.get_kpi_metrics()
        popular_books = APIClient.get_popular_books(limit=10)
        category_stats = APIClient.get_category_stats()
        student_activity = APIClient.get_student_activity(limit=10)
        overdue_analysis = APIClient.get_overdue_analysis()
        overdue_books = APIClient.get_overdue_books()
        
        return {
            'kpi_data': kpi_data,
            'popular_books': popular_books,
            'category_stats': category_stats,
            'student_activity': student_activity,
            'overdue_analysis': overdue_analysis,
            'overdue_books': overdue_books,
            'success': True
        }
    except Exception as e:
        st.error(f"Failed to load dashboard data: {str(e)}")
        return {'success': False, 'error': str(e)}

# Sidebar
with st.sidebar:
    st.title("🎛️ Dashboard Controls")
    
    # Date range selector
    st.subheader("📅 Date Range")
    date_range = st.selectbox(
        "Select Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
    )
    
    if date_range == "Custom Range":
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
    else:
        days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
        days = days_map[date_range]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # Data status indicator
    st.markdown("---")
    with st.spinner("Checking data status..."):
        cached_data = get_cached_data()
        if cached_data['success']:
            st.success("✅ Data loaded successfully")
        else:
            st.error("❌ Data loading failed")
    
    st.markdown("**Last Updated**: " + datetime.now().strftime("%H:%M:%S"))

# Main header
st.markdown("""
<div class="main-header">
    <h1>📚 Library Management Dashboard</h1>
    <p>Smart Library Operations Analytics Platform</p>
</div>
""", unsafe_allow_html=True)

# Load cached data
cached_data = get_cached_data()

if not cached_data['success']:
    st.error("Failed to load dashboard data. Please try refreshing the page.")
    st.stop()

# Extract data from cache
kpi_data = cached_data['kpi_data']
popular_books = cached_data['popular_books']
category_stats = cached_data['category_stats']
student_activity = cached_data['student_activity']
overdue_analysis = cached_data['overdue_analysis']
overdue_books = cached_data['overdue_books']

# KPI Metrics
st.markdown('<h2 class="section-header">📊 Key Performance Indicators</h2>', unsafe_allow_html=True)

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("📚 Total Books", f"{kpi_data.get('total_books', 0):,}")

with col2:
    st.metric("📖 Books Borrowed", f"{kpi_data.get('books_borrowed', 0):,}")

with col3:
    overdue_count = kpi_data.get('overdue_books', 0)
    st.metric("⚠️ Overdue Books", f"{overdue_count:,}", 
              delta=None if overdue_count == 0 else "Attention Required")

with col4:
    st.metric("👥 Active Users", f"{kpi_data.get('active_users', 0):,}")

with col5:
    utilization_rate = kpi_data.get('utilization_rate', 0)
    st.metric("📈 Utilization Rate", f"{utilization_rate:.1f}%",
              delta=f"{utilization_rate - 75:.1f}%" if utilization_rate > 0 else None)

with col6:
    st.metric("🆕 New Registrations", f"{kpi_data.get('new_registrations', 0):,}")

# Main Charts Section
st.markdown('<h2 class="section-header">📈 Trend Analysis</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    try:
        borrowing_trends = APIClient.get_borrowing_trends(start_date, end_date)
        st.plotly_chart(create_borrowing_trend_chart(borrowing_trends), use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load borrowing trends: {str(e)}")

with col2:
    st.plotly_chart(create_category_pie_chart(category_stats), use_container_width=True)

# Popular Books and Student Activity
st.markdown('<h2 class="section-header">🔥 Popular Rankings</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(create_popular_books_chart(popular_books), use_container_width=True)

with col2:
    st.plotly_chart(create_student_activity_chart(student_activity), use_container_width=True)

# Analysis Section
st.markdown('<h2 class="section-header">📋 Detailed Analysis</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(create_overdue_analysis_chart(overdue_analysis), use_container_width=True)

with col2:
    try:
        utilization_data = APIClient.get_library_utilization(start_date, end_date)
        st.plotly_chart(create_utilization_chart(utilization_data), use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load utilization data: {str(e)}")

# Detailed Tables
st.markdown('<h2 class="section-header">📋 Detailed Information</h2>', unsafe_allow_html=True)

# Overdue Books Table
with st.expander("⚠️ Overdue Books Details", expanded=False):
    if overdue_books:
        # Convert to DataFrame if it's a list
        if isinstance(overdue_books, list):
            overdue_df = pd.DataFrame(overdue_books)
        else:
            overdue_df = overdue_books
            
        if not overdue_df.empty:
            st.dataframe(
                overdue_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "title": "Book Title",
                    "student_name": "Student Name",
                    "days_overdue": st.column_config.NumberColumn(
                        "Days Overdue",
                        format="%d days"
                    ),
                    "due_date": "Due Date"
                }
            )
        else:
            st.info("✅ No overdue books found!")
    else:
        st.info("✅ No overdue books found!")

# Popular Books Table
with st.expander("📚 Popular Books Details", expanded=False):
    if popular_books:
        # Convert to DataFrame if it's a list
        if isinstance(popular_books, list):
            popular_df = pd.DataFrame(popular_books)
        else:
            popular_df = popular_books
            
        if not popular_df.empty:
            st.dataframe(
                popular_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "title": "Book Title",
                    "author": "Author",
                    "borrow_count": st.column_config.NumberColumn(
                        "Borrow Count",
                        format="%d times"
                    )
                }
            )
        else:
            st.info("No popular books data available")
    else:
        st.info("No popular books data available")

# Data Quality Summary
with st.expander("📊 Data Quality Summary", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Popular Books Records", len(popular_books) if popular_books else 0)
    
    with col2:
        st.metric("👥 Student Activity Records", len(student_activity) if student_activity else 0)
    
    with col3:
        st.metric("⚠️ Overdue Records", len(overdue_books) if overdue_books else 0)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>📚 Library Management System | Data-Driven Smart Management</div>",
    unsafe_allow_html=True
)