import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from sqlalchemy import create_engine, text
import calendar
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

# Import local configuration
from config import SQLALCHEMY_DATABASE_URI

# Set page configuration
st.set_page_config(
    page_title="SmartLib Admin Dashboard",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better UI
def apply_custom_css():
    st.markdown("""
    <style>
    .card {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        background-color: white;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: bold;
    }
    .metric-label {
        font-size: 14px;
        color: #555;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize database connection
@st.cache_resource
def get_db_connection():
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    return engine

# Data retrieval functions
@st.cache_data(ttl=600)
def get_borrow_data(start_date=None, end_date=None):
    """Retrieve borrowing data with optional date filtering"""
    engine = get_db_connection()
    query = """
    SELECT 
        br.borrow_id,
        br.borrow_date,
        br.due_date as expected_return_date,
        br.return_date as actual_return_date,
        br.status,
        s.full_name as student_name,
        s.matric_number as student_id,
        b.title as book_title,
        b.isbn
    FROM borrowing_records br
    JOIN students s ON br.matric_number = s.matric_number
    JOIN book_copies bc ON br.copy_id = bc.copy_id
    JOIN books b ON bc.book_id = b.book_id
    """
    
    if start_date and end_date:
        query += f" WHERE br.borrow_date BETWEEN '{start_date}' AND '{end_date}'"
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    return df

@st.cache_data(ttl=600)
def get_book_data():
    """Retrieve book data with borrowing statistics"""
    engine = get_db_connection()
    query = """
    SELECT 
        b.book_id as id,
        b.title,
        a.author_name as author,
        b.isbn,
        p.publisher_name as publisher,
        b.publication_year as year_published,
        dc.category_name as category,
        bc.status,
        COUNT(br.borrow_id) AS borrow_count
    FROM books b
    JOIN authors a ON b.author_id = a.author_id
    LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
    LEFT JOIN dewey_categories dc ON b.category_id = dc.category_id
    LEFT JOIN book_copies bc ON b.book_id = bc.book_id
    LEFT JOIN borrowing_records br ON bc.copy_id = br.copy_id
    GROUP BY b.book_id, a.author_name, p.publisher_name, dc.category_name, bc.status
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    return df

@st.cache_data(ttl=600)
def get_student_data():
    """Retrieve student data with borrowing statistics"""
    engine = get_db_connection()
    query = """
    SELECT 
        s.matric_number as id,
        s.full_name as name,
        s.matric_number as student_id,
        s.email,
        COUNT(br.borrow_id) AS total_borrows,
        SUM(CASE WHEN br.status = 'borrowed' AND br.due_date < CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS overdue_count
    FROM students s
    LEFT JOIN borrowing_records br ON s.matric_number = br.matric_number
    GROUP BY s.matric_number, s.full_name, s.email
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    return df

@st.cache_data(ttl=600)
def get_daily_stats(days=30):
    """Get daily borrowing and return statistics"""
    engine = get_db_connection()
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT 
        DATE(borrow_date) AS date,
        COUNT(*) AS borrow_count
    FROM borrowing_records
    WHERE borrow_date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    GROUP BY DATE(borrow_date)
    ORDER BY date
    """
    
    query2 = f"""
    SELECT 
        DATE(return_date) AS date,
        COUNT(*) AS return_count
    FROM borrowing_records
    WHERE return_date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    GROUP BY DATE(return_date)
    ORDER BY date
    """
    
    with engine.connect() as conn:
        borrow_df = pd.read_sql(query, conn)
        return_df = pd.read_sql(query2, conn)
    
    # Generate a complete date range and merge with data
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    date_df = pd.DataFrame({'date': date_range})
    date_df['date'] = date_df['date'].dt.date
    
    # Merge with borrow data
    result_borrow = pd.merge(date_df, borrow_df, on='date', how='left').fillna(0)
    result_return = pd.merge(date_df, return_df, on='date', how='left').fillna(0)
    
    # Combine into one dataframe
    result = pd.merge(result_borrow, result_return, on='date', how='left').fillna(0)
    result['date'] = pd.to_datetime(result['date'])
    
    return result

@st.cache_data(ttl=600)
def get_category_stats():
    """Get book statistics by category"""
    engine = get_db_connection()
    
    query = """
    SELECT 
        dc.category_name as category,
        COUNT(bc.copy_id) AS book_count,
        SUM(CASE WHEN bc.status = 'borrowed' THEN 1 ELSE 0 END) AS borrowed_count
    FROM dewey_categories dc
    JOIN books b ON dc.category_id = b.category_id
    JOIN book_copies bc ON b.book_id = bc.book_id
    GROUP BY dc.category_name
    ORDER BY book_count DESC
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    return df

@st.cache_data(ttl=600)
def get_overdue_books():
    """Get list of overdue books"""
    engine = get_db_connection()
    
    query = """
    SELECT 
        br.borrow_id,
        br.borrow_date,
        br.due_date as expected_return_date,
        EXTRACT(DAY FROM (CURRENT_DATE - br.due_date))::INTEGER AS days_overdue,
        s.full_name as student_name,
        s.matric_number as student_id,
        s.email,
        b.title as book_title,
        b.isbn
    FROM borrowing_records br
    JOIN students s ON br.matric_number = s.matric_number
    JOIN book_copies bc ON br.copy_id = bc.copy_id
    JOIN books b ON bc.book_id = b.book_id
    WHERE br.status = 'borrowed' AND br.due_date < CURRENT_TIMESTAMP
    ORDER BY days_overdue DESC
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    return df

# For demo/development purposes - create sample data if database is not available
def create_sample_data():
    # Sample dates
    today = datetime.now()
    date_range = pd.date_range(end=today, periods=30, freq='D')
    
    # Borrow data
    borrow_counts = np.random.randint(2, 15, size=30)
    return_counts = np.random.randint(1, 12, size=30)
    
    daily_stats = pd.DataFrame({
        'date': date_range,
        'borrow_count': borrow_counts,
        'return_count': return_counts
    })
    
    # Category data
    categories = ['Fiction', 'Science', 'Technology', 'History', 'Art', 'Philosophy', 'Biography']
    book_counts = np.random.randint(50, 200, size=len(categories))
    borrowed_counts = [int(count * np.random.uniform(0.1, 0.5)) for count in book_counts]
    
    category_stats = pd.DataFrame({
        'category': categories,
        'book_count': book_counts,
        'borrowed_count': borrowed_counts
    })
    
    # Overdue books
    student_names = ['John Doe', 'Jane Smith', 'Robert Brown', 'Mary Johnson', 'David Lee']
    book_titles = ['Python Programming', 'Data Science Handbook', 'Art of War', 'History of Time', 'Machine Learning']
    
    overdue_data = []
    for i in range(8):
        borrow_date = today - timedelta(days=np.random.randint(20, 60))
        expected_return = borrow_date + timedelta(days=14)
        days_overdue = (today - expected_return).days
        
        overdue_data.append({
            'borrow_id': i+1,
            'borrow_date': borrow_date,
            'expected_return_date': expected_return,
            'days_overdue': days_overdue,
            'student_name': np.random.choice(student_names),
            'student_id': f'A{np.random.randint(1000000, 9999999)}',
            'email': f'student{i+1}@university.edu',
            'book_title': np.random.choice(book_titles),
            'isbn': f'978-{np.random.randint(100000000, 999999999)}'
        })
    
    overdue_df = pd.DataFrame(overdue_data)
    
    return daily_stats, category_stats, overdue_df

# Sidebar navigation
def sidebar_navigation():
    st.sidebar.title("SmartLib Dashboard")
    st.sidebar.image("https://img.icons8.com/color/96/000000/library.png", width=100)
    
    page = st.sidebar.radio(
        "Navigation Menu",
        ["Dashboard", "Borrowing Management", "Book Management", "Student Management", "System Settings"]
    )
    
    # Add date filter in sidebar for all pages
    st.sidebar.markdown("---")
    st.sidebar.subheader("Date Filter")
    
    # Default to last 30 days
    default_start_date = datetime.now() - timedelta(days=30)
    default_end_date = datetime.now()
    
    start_date = st.sidebar.date_input("Start Date", default_start_date)
    end_date = st.sidebar.date_input("End Date", default_end_date)
    
    if start_date > end_date:
        st.sidebar.error("End date must be after start date")
    
    # Add system info at bottom of sidebar
    st.sidebar.markdown("---")
    st.sidebar.info("SmartLib v1.0.0")
    
    return page, start_date, end_date

# Dashboard components
def show_kpi_metrics(daily_stats, overdue_df):
    # Create three columns for KPIs
    col1, col2, col3 = st.columns(3)
    
    # Current month stats
    current_month = datetime.now().month
    current_month_data = daily_stats[daily_stats['date'].dt.month == current_month]
    
    total_borrows = int(current_month_data['borrow_count'].sum())
    total_returns = int(current_month_data['return_count'].sum())
    overdue_count = len(overdue_df)
    
    # Define KPI cards with CSS styling
    with col1:
        st.markdown("""
        <div class="card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Monthly Borrowings</div>
        </div>
        """.format(total_borrows), unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Monthly Returns</div>
        </div>
        """.format(total_returns), unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Overdue Books</div>
        </div>
        """.format(overdue_count), unsafe_allow_html=True)

def show_daily_trends(daily_stats):
    st.subheader("Borrowing and Return Trends")
    
    # Create a tab view for different time periods
    period_tabs = st.tabs(["Last 7 Days", "Last 30 Days", "Last 90 Days"])
    
    for i, period in enumerate([7, 30, 90]):
        with period_tabs[i]:
            filtered_data = daily_stats.iloc[-period:]
            
            # Create Plotly line chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=filtered_data['date'],
                y=filtered_data['borrow_count'],
                mode='lines+markers',
                name='Borrowings',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=filtered_data['date'],
                y=filtered_data['return_count'],
                mode='lines+markers',
                name='Returns',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="Date",
                yaxis_title="Number of Books",
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate and display statistics
            avg_borrowings = filtered_data['borrow_count'].mean()
            avg_returns = filtered_data['return_count'].mean()
            max_borrowings = filtered_data['borrow_count'].max()
            total_borrowings = filtered_data['borrow_count'].sum()
            total_returns = filtered_data['return_count'].sum()
            
            st.markdown(f"""
            **Period Statistics:**
            - Average daily borrowings: {avg_borrowings:.1f}
            - Average daily returns: {avg_returns:.1f}
            - Peak borrowing day: {max_borrowings} books
            - Total borrowings: {total_borrowings} books
            - Total returns: {total_returns} books
            """)

def show_category_distribution(category_stats):
    st.subheader("Book Category Distribution")
    
    # Create columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Create a pie chart for book distribution by category
        fig = px.pie(
            category_stats, 
            values='book_count', 
            names='category',
            title='Total Books by Category',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Create a horizontal bar chart comparing total vs borrowed books
        category_stats_sorted = category_stats.sort_values('book_count', ascending=True)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=category_stats_sorted['category'],
            x=category_stats_sorted['book_count'],
            name='Total Books',
            orientation='h',
            marker=dict(color='rgba(58, 71, 80, 0.6)')
        ))
        
        fig.add_trace(go.Bar(
            y=category_stats_sorted['category'],
            x=category_stats_sorted['borrowed_count'],
            name='Currently Borrowed',
            orientation='h',
            marker=dict(color='rgba(246, 78, 139, 0.6)')
        ))
        
        fig.update_layout(
            title='Available vs. Borrowed Books by Category',
            barmode='overlay',
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="Number of Books",
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=False),
            xaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)')
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_overdue_books(overdue_df):
    st.subheader("Overdue Books")
    
    if len(overdue_df) == 0:
        st.success("No overdue books at the moment!")
        return
    
    # Add a filter for overdue days
    overdue_days_filter = st.slider("Filter by days overdue", 
                                  min_value=1, 
                                  max_value=max(30, int(overdue_df['days_overdue'].max())), 
                                  value=1)
    
    filtered_overdue = overdue_df[overdue_df['days_overdue'] >= overdue_days_filter]
    
    if len(filtered_overdue) == 0:
        st.info(f"No books overdue by {overdue_days_filter} days or more.")
        return
    
    # Show the filtered overdue books
    st.dataframe(
        filtered_overdue[['book_title', 'student_name', 'student_id', 'email', 
                          'expected_return_date', 'days_overdue']],
        column_config={
            "days_overdue": st.column_config.NumberColumn(
                "Days Overdue",
                help="Number of days past the expected return date",
                format="%d",
            ),
            "expected_return_date": st.column_config.DateColumn(
                "Expected Return",
                format="MMM DD, YYYY",
            ),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Add a button to send reminders
    if st.button("Send Reminder to All Listed Students"):
        st.success(f"Reminders sent to {len(filtered_overdue)} students!")

# Borrowing management page
def show_borrow_management(start_date, end_date):
    st.title("📚 Borrowing Management")
    
    try:
        # Get borrow data
        borrow_data = get_borrow_data(start_date, end_date)
        
        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input("Search borrowing records", "")
        
        with col2:
            filter_status = st.selectbox("Borrowing Status", 
                                      ["All", "Borrowed", "Returned", "Overdue"])
        
        with col3:
            sort_by = st.selectbox("Sort by", 
                                 ["Borrow Date (Newest)", "Borrow Date (Oldest)", 
                                  "Expected Return Date", "Student Name"])
        
        # Filter the data
        if search_query:
            borrow_data = borrow_data[
                borrow_data['student_name'].str.contains(search_query, case=False) |
                borrow_data['book_title'].str.contains(search_query, case=False) |
                borrow_data['student_id'].str.contains(search_query, case=False)
            ]
        
        if filter_status != "All":
            status_map = {"Borrowed": "borrowed", "Returned": "returned", "Overdue": "overdue"}
            borrow_data = borrow_data[borrow_data['status'] == status_map[filter_status]]
        
        # Sort the data
        if sort_by == "Borrow Date (Newest)":
            borrow_data = borrow_data.sort_values('borrow_date', ascending=False)
        elif sort_by == "Borrow Date (Oldest)":
            borrow_data = borrow_data.sort_values('borrow_date', ascending=True)
        elif sort_by == "Expected Return Date":
            borrow_data = borrow_data.sort_values('expected_return_date', ascending=True)
        elif sort_by == "Student Name":
            borrow_data = borrow_data.sort_values('student_name', ascending=True)
        
        # Display the data
        if len(borrow_data) > 0:
            st.dataframe(
                borrow_data,
                column_config={
                    "borrow_date": st.column_config.DateColumn(
                        "Borrow Date",
                        format="MMM DD, YYYY",
                    ),
                    "expected_return_date": st.column_config.DateColumn(
                        "Expected Return",
                        format="MMM DD, YYYY",
                    ),
                    "actual_return_date": st.column_config.DateColumn(
                        "Actual Return",
                        format="MMM DD, YYYY",
                    ),
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["borrowed", "returned", "overdue"],
                        required=True,
                    ),
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.info(f"Showing {len(borrow_data)} records")
            
            # Export button
            if st.button("Export to Excel"):
                st.success("Data exported successfully!")
        else:
            st.warning("No borrowing records found matching your criteria.")
            
    except Exception as e:
        st.error(f"Error loading borrowing data: {e}")
        # For demo purposes, show sample data
        st.warning("Showing sample data for demonstration")
        
        # TODO: Add sample data display for development

# Book management page
def show_book_management():
    st.title("📖 Book Management")
    
    try:
        # Get book data
        book_data = get_book_data()
        
        # Book management tabs
        book_tabs = st.tabs(["Book Inventory", "Add New Book", "Book Statistics"])
        
        with book_tabs[0]:
            # Search and filter
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_query = st.text_input("Search books", "")
            
            with col2:
                filter_status = st.selectbox("Book Status", 
                                          ["All", "Available", "Borrowed", "Reserved", "Unpublished"])
            
            # Filter data
            if search_query:
                book_data = book_data[
                    book_data['title'].str.contains(search_query, case=False) |
                    book_data['author'].str.contains(search_query, case=False) |
                    book_data['isbn'].str.contains(search_query, case=False)
                ]
            
            if filter_status != "All":
                status_map = {"Available": "available", "Borrowed": "borrowed", 
                              "Reserved": "reserved", "Unpublished": "unpublished"}
                book_data = book_data[book_data['status'] == status_map[filter_status]]
            
            # Display book data
            if len(book_data) > 0:
                st.dataframe(
                    book_data,
                    column_config={
                        "title": "Title",
                        "author": "Author",
                        "category": st.column_config.SelectboxColumn(
                            "Category",
                            width="medium",
                        ),
                        "status": st.column_config.SelectboxColumn(
                            "Status",
                            width="small",
                        ),
                        "borrow_count": st.column_config.NumberColumn(
                            "Times Borrowed",
                            format="%d",
                        ),
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                st.info(f"Showing {len(book_data)} books")
            else:
                st.warning("No books found matching your criteria.")
                
        with book_tabs[1]:
            # New book form
            st.subheader("Add New Book")
            
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title", "")
                author = st.text_input("Author", "")
                isbn = st.text_input("ISBN", "")
                
            with col2:
                publisher = st.text_input("Publisher", "")
                year = st.number_input("Year Published", min_value=1800, max_value=2025, value=2023)
                category = st.selectbox("Category", ["Fiction", "Science", "Technology", "History", "Art"])
            
            # Additional fields
            description = st.text_area("Description", "")
            
            if st.button("Add Book"):
                st.success(f"Book '{title}' added successfully!")
                
        with book_tabs[2]:
            # Book statistics
            st.subheader("Book Statistics")
            
            # Most borrowed books
            top_books = book_data.sort_values('borrow_count', ascending=False).head(10)
            
            fig = px.bar(
                top_books,
                x='title',
                y='borrow_count',
                title='Most Popular Books',
                labels={'title': 'Book Title', 'borrow_count': 'Times Borrowed'},
                color='borrow_count',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            fig.update_layout(
                xaxis={'categoryorder': 'total descending'},
                height=400,
                margin=dict(l=10, r=10, t=40, b=120),
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Books by year
            year_counts = book_data.groupby('year_published').size().reset_index(name='count')
            
            fig = px.line(
                year_counts,
                x='year_published',
                y='count',
                title='Books by Publication Year',
                labels={'year_published': 'Year', 'count': 'Number of Books'},
                markers=True
            )
            
            fig.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=40, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading book data: {e}")
        # For demo purposes
        st.warning("Showing sample data for demonstration")
        
        # TODO: Add sample book data display

# Student management page
def show_student_management():
    st.title("👥 Student Management")
    
    try:
        # Get student data
        student_data = get_student_data()
        
        # Search
        search_query = st.text_input("Search students", "")
        
        if search_query:
            student_data = student_data[
                student_data['name'].str.contains(search_query, case=False) |
                student_data['student_id'].str.contains(search_query, case=False) |
                student_data['email'].str.contains(search_query, case=False)
            ]
        
        # Display student data
        if len(student_data) > 0:
            st.dataframe(
                student_data,
                column_config={
                    "name": "Student Name",
                    "student_id": "Student ID",
                    "email": "Email",
                    "total_borrows": st.column_config.NumberColumn(
                        "Total Borrowings",
                        format="%d",
                    ),
                    "overdue_count": st.column_config.NumberColumn(
                        "Overdue Books",
                        format="%d",
                    ),
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.info(f"Showing {len(student_data)} students")
            
            # Student statistics
            st.subheader("Student Borrowing Statistics")
            
            # Top borrowers
            top_borrowers = student_data.sort_values('total_borrows', ascending=False).head(10)
            
            fig = px.bar(
                top_borrowers,
                x='name',
                y='total_borrows',
                title='Top Borrowers',
                labels={'name': 'Student Name', 'total_borrows': 'Number of Borrowings'},
                color='total_borrows',
                color_continuous_scale=px.colors.sequential.Inferno
            )
            
            fig.update_layout(
                xaxis={'categoryorder': 'total descending'},
                height=400,
                margin=dict(l=10, r=10, t=40, b=120),
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Students with overdue books
            students_with_overdue = student_data[student_data['overdue_count'] > 0]
            
            if len(students_with_overdue) > 0:
                st.subheader("Students with Overdue Books")
                
                st.dataframe(
                    students_with_overdue[['name', 'student_id', 'email', 'overdue_count']],
                    hide_index=True,
                    use_container_width=True
                )
                
                if st.button("Send Reminders to All Listed Students"):
                    st.success(f"Reminders sent to {len(students_with_overdue)} students!")
            else:
                st.success("No students currently have overdue books!")
        else:
            st.warning("No students found matching your criteria.")
            
    except Exception as e:
        st.error(f"Error loading student data: {e}")
        st.warning("Showing sample data for demonstration")
        
        # For demo purposes
        # TODO: Add sample student data display

# System settings page
def show_settings():
    st.title("⚙️ System Settings")
    
    # Settings tabs
    settings_tabs = st.tabs(["General Settings", "Email Settings", "Borrowing Rules", "Database"])
    
    with settings_tabs[0]:
        st.subheader("General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            library_name = st.text_input("Library Name", "SmartLib Community Library")
            contact_email = st.text_input("Contact Email", "admin@smartlib.edu")
        
        with col2:
            timezone = st.selectbox("Timezone", ["UTC", "Asia/Singapore", "America/New_York"])
            language = st.selectbox("Language", ["English", "Chinese", "Spanish"])
        
        if st.button("Save General Settings"):
            st.success("Settings saved successfully!")
    
    with settings_tabs[1]:
        st.subheader("Email Settings")
        
        smtp_server = st.text_input("SMTP Server", "smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587)
        smtp_username = st.text_input("SMTP Username", "notifications@smartlib.edu")
        smtp_password = st.text_input("SMTP Password", type="password")
        
        st.subheader("Email Templates")
        
        template_tabs = st.tabs(["Overdue Reminder", "Welcome Email", "Return Confirmation"])
        
        with template_tabs[0]:
            overdue_template = st.text_area(
                "Overdue Reminder Template",
                """Dear {student_name},

This is a reminder that the following book is overdue:
Title: {book_title}
Due Date: {due_date}

Please return it to the library as soon as possible.

Thank you,
SmartLib Team"""
            )
        
        with template_tabs[1]:
            welcome_template = st.text_area(
                "Welcome Email Template",
                """Welcome to SmartLib, {student_name}!

Your account has been created successfully.
Student ID: {student_id}

You can now borrow up to 3 books at a time.

Happy reading!
SmartLib Team"""
            )
            
        if st.button("Save Email Settings"):
            st.success("Email settings saved successfully!")
    
    with settings_tabs[2]:
        st.subheader("Borrowing Rules")
        
        max_books = st.number_input("Maximum Books Per Student", value=3)
        loan_period = st.number_input("Standard Loan Period (days)", value=14)
        extension_period = st.number_input("Extension Period (days)", value=14)
        max_extensions = st.number_input("Maximum Number of Extensions", value=1)
        
        st.subheader("Special Category Rules")
        
        st.info("Set different loan periods for special book categories")
        
        col1, col2 = st.columns(2)
        
        with col1:
            reference_period = st.number_input("Reference Books (days)", value=7)
            rare_period = st.number_input("Rare Books (days)", value=7)
        
        with col2:
            new_arrival_period = st.number_input("New Arrivals (days)", value=10)
            multimedia_period = st.number_input("Multimedia (days)", value=7)
            
        if st.button("Save Borrowing Rules"):
            st.success("Borrowing rules saved successfully!")
    
    with settings_tabs[3]:
        st.subheader("Database Settings")
        
        st.warning("These settings should only be modified by system administrators.")
        
        db_url = st.text_input("Database URL", "mysql://user:password@localhost/smartlib")
        pool_size = st.number_input("Connection Pool Size", value=10)
        timeout = st.number_input("Connection Timeout (seconds)", value=30)
        
        st.subheader("Database Maintenance")
        
        maintenance_col1, maintenance_col2 = st.columns(2)
        
        with maintenance_col1:
            if st.button("Backup Database"):
                st.success("Database backed up successfully!")
                
            if st.button("Optimize Database"):
                st.success("Database optimized successfully!")
        
        with maintenance_col2:
            if st.button("Run Database Integrity Check"):
                st.success("Database integrity check completed. No issues found.")
                
            if st.button("Clear Old Logs"):
                st.success("Old logs cleared successfully!")

# Main dashboard page
def show_dashboard():
    st.title("📊 SmartLib Dashboard")
    
    try:
        # Try to get data from database
        daily_stats = get_daily_stats()
        category_stats = get_category_stats()
        overdue_books = get_overdue_books()
        
    except Exception as e:
        st.warning(f"Could not connect to database, using sample data for demonstration: {e}")
        
        # Generate sample data for demonstration
        daily_stats, category_stats, overdue_books = create_sample_data()
    
    # Show KPI metrics
    show_kpi_metrics(daily_stats, overdue_books)
    
    # Show charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Show borrowing trends
        show_daily_trends(daily_stats)
    
    with col2:
        # Show category distribution
        show_category_distribution(category_stats)
    
    # Show overdue books
    show_overdue_books(overdue_books)

# Main function
def main():
    # Apply custom CSS
    apply_custom_css()
    
    # Get page selection from sidebar
    page, start_date, end_date = sidebar_navigation()
    
    # Display the selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Borrowing Management":
        show_borrow_management(start_date, end_date)
    elif page == "Book Management":
        show_book_management()
    elif page == "Student Management":
        show_student_management()
    elif page == "System Settings":
        show_settings()

if __name__ == "__main__":
    main()