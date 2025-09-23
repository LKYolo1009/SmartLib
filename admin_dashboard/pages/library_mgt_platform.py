import streamlit as st
import pandas as pd
from datetime import datetime
from utils.api_client import APIClient
from config import DASHBOARD_CONFIG
from functools import wraps


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

# Main header
st.markdown("""
<div class="main-header">
    <h1> 📖 Library Management Platform</h1>
    <p>Tembusu Library Admin Platform for Book Management</p>
</div>
""", unsafe_allow_html=True)

# Custom cache key function to include search_field
def get_cache_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = f"{func.__name__}_{kwargs.get('search_field', 'default')}_{kwargs.get('page', 1)}_{kwargs.get('per_page', 30)}_{kwargs.get('search_query', '')}"
        return func(*args, **kwargs)
    return wrapper

# Function to fetch books from API with pagination and search
@st.cache_data(ttl=600, show_spinner="Loading books...")
@get_cache_key
def get_books(search_query="", page=1, per_page=30, search_field=None):
    
    if search_field is None:
        raise ValueError("search_field must be provided")  # Should never happen with UI
    try:
        # Fetch all books using the provided get_book_details function
        data = APIClient.get_all_book_details()
        df = pd.DataFrame(data)
        
        if df.empty:
            return df, 0

        # Apply search filter (client-side) based on selected field
        if search_query:
            search_query = search_query.lower()
            valid_fields = {"copy_id", "book_title", "author_name"}
            if search_field not in valid_fields:
                st.warning(f"Invalid search field: {search_field}. Defaulting to 'book_title'.")
                search_field = "book_title"
            if search_field == "copy_id":
                # System behavior: Performs an exact match on the 'id' column
                df = df[df['id'].astype(str).str.lower() == search_query]
            elif search_field == "book_title":
                # System behavior: Performs a fuzzy search on the 'title' column
                df = df[df['title'].str.lower().str.contains(search_query, na=False)]
            elif search_field == "author_name":
                # System behavior: Performs a fuzzy search on the 'author_name' column
                df = df[df['author_name'].str.lower().str.contains(search_query, na=False)]

        # Pagination
        total_books = len(df)
        total_pages = (total_books + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_df = df.iloc[start_idx:end_idx]

        return paginated_df, total_pages
    except Exception as e:
        st.error(f"Error loading book data: {e}")
        return pd.DataFrame(), 0

# Function to add a book
def add_book(book_data):
    try:
        # Call the static method without passing book_data, as it uses st.session_state.add_form
        if APIClient.add_new_book_details():
            st.success("Book added successfully")
            return True
        return False
    except Exception as e:
        st.error(f"Error adding book: {e}")
        return False

# Function to update a book (placeholder - implement based on your API)
def update_book(book_id, book_data):
    try:
        response = APIClient.update_book(book_id, book_data)  # Adjust to your API endpoint
        st.success("Book updated successfully")
        return True
    except Exception as e:
        st.error(f"Error updating book: {e}")
        return False

# Function to delete a book (placeholder - implement based on your API)
def delete_book(book_id):
    try:
        response = APIClient.delete_book(book_id)  # Adjust to your API endpoint
        st.success("Book deleted successfully")
        return True
    except Exception as e:
        st.error(f"Error deleting book: {e}")
        return False

# Function to get book by ID (placeholder - implement based on your API)
def get_book_by_id(book_id):
    try:
        book = APIClient.get_book_by_id(book_id)  # Adjust to your API endpoint
        return book
    except Exception as e:
        st.error(f"Error fetching book: {e}")
        return None

# Main page
def main_page():
    
    # Search by and keywords with buttons and cache clear
    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
    with col1:
        search_field = st.selectbox("Search by", ["book title", "author name", "copy ID"], key="search_field", index=0)
        search_field = search_field.replace(" ", "_").lower()
    with col2:
        search_query = st.text_input("Keywords", key="search")
    with col3:
        search_button = st.button("Search")
    with col4:
        if st.button("Add New Book"):
            st.session_state.page = "add"
            st.rerun()


    # Pagination
    page = st.session_state.get('page_number', 1)
    df, total_pages = get_books(search_query if search_button else "", page, per_page=30, search_field=search_field)

    # Display books in a table
    if not df.empty:
        # Ensure all required columns are present
        required_columns = [
            'id','title', 'isbn', 'category', 'author_name', 'call_number', 'publisher_name',
            'publication_year', 'language', 'total_copy', 'acquisition_type',
            'acquisition_date', 'price', 'condition', 'book_location'
        ]
        # Add missing columns with empty values
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Add action buttons
        df['Actions'] = df['id'].apply(
            lambda x: f'<button onclick="window.location.href=\'?page=edit&id={x}\'">Edit</button> '
                     f'<button onclick="if(confirm(\'Are you sure you want to delete this book?\')) window.location.href=\'?page=delete&id={x}\'">Delete</button>'
        )
        
        st.markdown(df[required_columns + ['Actions']].to_html(escape=False, index=False), unsafe_allow_html=True)

        # Pagination controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if page > 1:
                if st.button("Previous"):
                    st.session_state.page_number = page - 1
                    st.rerun()
        with col2:
            st.write(f"Page {page} of {total_pages}")
        with col3:
            if page < total_pages:
                if st.button("Next"):
                    st.session_state.page_number = page + 1
                    st.rerun()
    else:
        st.warning("No books found.")

# Add book page
def add_book_page():
    st.title("Add New Book")
    
    # Initialize session state for dynamic updates
    if 'add_form' not in st.session_state:
        st.session_state.add_form = {'title': '', 'isbn': '', 'category': 'Class 000 - Computer science, information, and general works', 
                                     'author_name': '', 'call_number': '', 'publisher_name': '', 'publication_year': 0, 
                                     'language': '', 'total_copy': 0, 'acquisition_type': '', 'acquisition_date': datetime.now().date(), 
                                     'price': 0.0, 'condition': '', 'book_location': ''}
    
    with st.form("add_book_form"):
        st.session_state.add_form['title'] = st.text_input("Book Title", value=st.session_state.add_form['title'])
        st.session_state.add_form['isbn'] = st.text_input("ISBN", value=st.session_state.add_form['isbn'])
        
        # Category dropdown with pre-defined list
        categories = [
            "Class 000 - Computer science, information, and general works",
            "Class 100 - Philosophy and psychology",
            "Class 200 - Religion",
            "Class 300 - Social sciences",
            "Class 400 - Language",
            "Class 500 - Science",
            "Class 600 - Technology",
            "Class 700 - Arts and recreation",
            "Class 800 - Literature",
            "Class 900 - History and geography"
        ]
        st.session_state.add_form['category'] = st.selectbox("Category", categories, index=categories.index(st.session_state.add_form['category']))
        
        st.session_state.add_form['author_name'] = st.text_input("Author Name", value=st.session_state.add_form['author_name'])
        
        # Auto-generate call number in real-time with first 3 characters of last name
        if st.session_state.add_form['author_name']:
            last_name = st.session_state.add_form['author_name'].split()[-1].upper()
            first_three = last_name[:3] if len(last_name) >= 3 else last_name.ljust(3, 'X')  # Pad with 'X' if less than 3 chars
            category_class = {
                "Class 000 - Computer science, information, and general works": "000",
                "Class 100 - Philosophy and psychology": "100",
                "Class 200 - Religion": "200",
                "Class 300 - Social sciences": "300",
                "Class 400 - Language": "400",
                "Class 500 - Science": "500",
                "Class 600 - Technology": "600",
                "Class 700 - Arts and recreation": "700",
                "Class 800 - Literature": "800",
                "Class 900 - History and geography": "900"
            }
            st.session_state.add_form['call_number'] = f"{category_class[st.session_state.add_form['category']]}_{first_three}"
        else:
            st.session_state.add_form['call_number'] = ""
        
        st.text_input("Call Number", value=st.session_state.add_form['call_number'], disabled=True)
        
        st.session_state.add_form['publisher_name'] = st.text_input("Publisher Name", value=st.session_state.add_form['publisher_name'])
        st.session_state.add_form['publication_year'] = st.number_input("Publication Year", min_value=0, max_value=datetime.now().year, value=st.session_state.add_form['publication_year'])
        st.session_state.add_form['language'] = st.text_input("Language", value=st.session_state.add_form['language'])
        st.session_state.add_form['total_copy'] = st.number_input("Total Copies", min_value=0, value=st.session_state.add_form['total_copy'])
        st.session_state.add_form['acquisition_type'] = st.text_input("Acquisition Type", value=st.session_state.add_form['acquisition_type'])
        st.session_state.add_form['acquisition_date'] = st.date_input("Acquisition Date", value=st.session_state.add_form['acquisition_date'])
        st.session_state.add_form['price'] = st.number_input("Price", min_value=0.0, format="%.2f", value=st.session_state.add_form['price'])
        st.session_state.add_form['condition'] = st.text_input("Condition", value=st.session_state.add_form['condition'])
        st.session_state.add_form['book_location'] = st.text_input("Book Location", value=st.session_state.add_form['book_location'])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save"):
                if APIClient.add_new_book_details():  # Call the static method without arguments
                    st.session_state.page = "main"
                    st.rerun()
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.page = "main"
                st.rerun()

# Edit book page
def edit_book_page(book_id):
    book = get_book_by_id(book_id)
    if not book:
        st.error("Book not found")
        return
    
    st.title("Edit Book")
    
    # Initialize session state for dynamic updates
    if 'edit_form' not in st.session_state:
        st.session_state.edit_form = book if book else {
            'title': '', 'isbn': '', 'category': 'Class 000 - Computer science, information, and general works', 
            'author_name': '', 'call_number': '', 'publisher_name': '', 'publication_year': 0, 
            'language': '', 'total_copy': 0, 'acquisition_type': '', 'acquisition_date': datetime.now().date(), 
            'price': 0.0, 'condition': '', 'book_location': ''
        }
    
    with st.form("edit_book_form"):
        st.session_state.edit_form['title'] = st.text_input("Book Title", value=st.session_state.edit_form['title'])
        st.session_state.edit_form['isbn'] = st.text_input("ISBN", value=st.session_state.edit_form['isbn'])
        
        # Category dropdown with pre-defined list
        categories = [
            "Class 000 - Computer science, information, and general works",
            "Class 100 - Philosophy and psychology",
            "Class 200 - Religion",
            "Class 300 - Social sciences",
            "Class 400 - Language",
            "Class 500 - Science",
            "Class 600 - Technology",
            "Class 700 - Arts and recreation",
            "Class 800 - Literature",
            "Class 900 - History and geography"
        ]
        st.session_state.edit_form['category'] = st.selectbox("Category", categories, index=categories.index(st.session_state.edit_form['category']))
        
        st.session_state.edit_form['author_name'] = st.text_input("Author Name", value=st.session_state.edit_form['author_name'])
        
        # Auto-generate call number in real-time with first 3 characters of last name
        if st.session_state.edit_form['author_name']:
            last_name = st.session_state.edit_form['author_name'].split()[-1].upper()
            first_three = last_name[:3] if len(last_name) >= 3 else last_name.ljust(3, 'X')  # Pad with 'X' if less than 3 chars
            category_class = {
                "Class 000 - Computer science, information, and general works": "000",
                "Class 100 - Philosophy and psychology": "100",
                "Class 200 - Religion": "200",
                "Class 300 - Social sciences": "300",
                "Class 400 - Language": "400",
                "Class 500 - Science": "500",
                "Class 600 - Technology": "600",
                "Class 700 - Arts and recreation": "700",
                "Class 800 - Literature": "800",
                "Class 900 - History and geography": "900"
            }
            st.session_state.edit_form['call_number'] = f"{category_class[st.session_state.edit_form['category']]}_{first_three}"
        else:
            st.session_state.edit_form['call_number'] = book.get('call_number', '') if book else ""
        
        st.text_input("Call Number", value=st.session_state.edit_form['call_number'], disabled=True)
        
        st.session_state.edit_form['publisher_name'] = st.text_input("Publisher Name", value=st.session_state.edit_form['publisher_name'])
        st.session_state.edit_form['publication_year'] = st.number_input("Publication Year", min_value=0, 
                                        max_value=datetime.now().year, 
                                        value=st.session_state.edit_form['publication_year'])
        st.session_state.edit_form['language'] = st.text_input("Language", value=st.session_state.edit_form['language'])
        st.session_state.edit_form['total_copy'] = st.number_input("Total Copies", min_value=0, value=st.session_state.edit_form['total_copy'])
        st.session_state.edit_form['acquisition_type'] = st.text_input("Acquisition Type", value=st.session_state.edit_form['acquisition_type'])
        st.session_state.edit_form['acquisition_date'] = st.date_input("Acquisition Date", 
                                       value=st.session_state.edit_form['acquisition_date'])
        st.session_state.edit_form['price'] = st.number_input("Price", min_value=0.0, format="%.2f", value=st.session_state.edit_form['price'])
        st.session_state.edit_form['condition'] = st.text_input("Condition", value=st.session_state.edit_form['condition'])
        st.session_state.edit_form['book_location'] = st.text_input("Book Location", value=st.session_state.edit_form['book_location'])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save"):
                book_data = {
                    "title": st.session_state.edit_form['title'],
                    "isbn": st.session_state.edit_form['isbn'],
                    "category": st.session_state.edit_form['category'],
                    "author_name": st.session_state.edit_form['author_name'],
                    "call_number": st.session_state.edit_form['call_number'],
                    "publisher_name": st.session_state.edit_form['publisher_name'],
                    "publication_year": st.session_state.edit_form['publication_year'],
                    "language": st.session_state.edit_form['language'],
                    "total_copy": st.session_state.edit_form['total_copy'],
                    "acquisition_type": st.session_state.edit_form['acquisition_type'],
                    "acquisition_date": str(st.session_state.edit_form['acquisition_date']),
                    "price": st.session_state.edit_form['price'],
                    "condition": st.session_state.edit_form['condition'],
                    "book_location": st.session_state.edit_form['book_location']
                }
                if update_book(book_id, book_data):
                    st.session_state.page = "main"
                    st.rerun()
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.page = "main"
                st.rerun()

# Main app logic
def main():
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    
    if st.session_state.page == "main":
        main_page()
    elif st.session_state.page == "add":
        add_book_page()
    elif st.session_state.page == "edit":
        book_id = st.query_params.get("id", [None])[0]
        if book_id:
            edit_book_page(book_id)
    elif st.session_state.page == "delete":
        book_id = st.query_params.get("id", [None])[0]
        if book_id:
            if delete_book(book_id):
                st.session_state.page = "main"
                st.rerun()

if __name__ == "__main__":
    main()
    