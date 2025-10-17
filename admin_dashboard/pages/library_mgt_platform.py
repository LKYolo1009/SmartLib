import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from utils.api_client import APIClient
from config import DASHBOARD_CONFIG, CATEGORY_ID_MAPPING, LANGUAGE_CODE_MAPPING, ACQUISITION_TYPE_MAPPING, BOOK_CONDITION_MAPPING, BOOK_STATUS_MAPPING, BOOK_LOCATION_AREA_MAPPING
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
    # Display book creation success message if exists
    if 'book_creation_success' in st.session_state:
        st.success(st.session_state.book_creation_success)
        # Clear the success message after showing it
        del st.session_state.book_creation_success
    
    # Display edit success message if exists
    if 'edit_success' in st.session_state:
        st.success(st.session_state.edit_success)
        # Clear the success message after showing it
        del st.session_state.edit_success
    
    # Search by and keywords with buttons and cache clear
    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1, 2, 1])
    with col1:
        search_field = st.selectbox("Search by", ["book title", "author name", "copy ID"], key="search_field", index=0)
        search_field = search_field.replace(" ", "_").lower()
    with col2:
        search_query = st.text_input("Keywords", key="search")
    with col3:
        st.write("")  # Add empty space to align button with input
        search_button = st.button("Search")
    with col4:
        st.write("")  # Add empty space to align button with input
        if st.button("Add New Book"):
            st.session_state.page = "add"
            st.rerun()
    with col5:
        st.write("")  # Add empty space to align button with input
        if st.button("Add Book Copy for Existing Book"):
            st.session_state.page = "add_copy"
            st.rerun()
    with col6:
        st.write("")  # Add empty space to align button with input
        if st.button("🔄 Refresh", help="Clear cache and reload all data"):
            st.cache_data.clear()
            st.rerun()

    # Pagination
    page = st.session_state.get('page_number', 1)
    df, total_pages = get_books(search_query if search_button else "", page, per_page=30, search_field=search_field)

    # Display books in a table
    if not df.empty:
        # Sort books by book copy ID to group same books together
        # First, ensure 'id' column is numeric for proper sorting
        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        
        # Sort by book title first (to group same books together), then by book copy ID
        df = df.sort_values(['title', 'id'], ascending=[True, True])
        
        # Ensure all required columns are present
        required_columns = [
            'id','title', 'isbn', 'category', 'author_name', 'call_number', 'publisher_name',
            'publication_year', 'language', 'total_copy', 'acquisition_type',
            'acquisition_date', 'price', 'condition', 'status', 'book_location'
        ]
        # Add missing columns with empty values
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Create a copy of the dataframe for display with renamed columns
        display_df = df[required_columns].copy()
        
        # Rename columns to be more user-friendly
        column_rename_map = {
            'id': 'Book Copy ID',
            'title': 'Title',
            'isbn': 'ISBN',
            'category': 'Category',
            'author_name': 'Author Name',
            'call_number': 'Call Number',
            'publisher_name': 'Publisher Name',
            'publication_year': 'Publication Year',
            'language': 'Language',
            'total_copy': 'Total Copy',
            'acquisition_type': 'Acquisition Type',
            'acquisition_date': 'Acquisition Date',
            'price': 'Price',
            'condition': 'Condition',
            'status': 'Status',
            'book_location': 'Book Location'
        }
        
        display_df = display_df.rename(columns=column_rename_map)
        
        # Create a custom table with delete buttons
        st.markdown("### All Book Copies in the Database")
        
        # Table header - Title column gets 2x width
        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15, col16, col17, col18 = st.columns([1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        with col1:
            st.write("**Book Copy ID**")
        with col2:
            st.write("**Title**")
        with col3:
            st.write("**ISBN**")
        with col4:
            st.write("**Category**")
        with col5:
            st.write("**Author Name**")
        with col6:
            st.write("**Call Number**")
        with col7:
            st.write("**Publisher Name**")
        with col8:
            st.write("**Publication Year**")
        with col9:
            st.write("**Language**")
        with col10:
            st.write("**Total Copy**")
        with col11:
            st.write("**Acquisition Type**")
        with col12:
            st.write("**Acquisition Date**")
        with col13:
            st.write("**Price**")
        with col14:
            st.write("**Condition**")
        with col15:
            st.write("**Status**")
        with col16:
            st.write("**Book Location**")
        with col17:
            st.write("**Actions**")
        with col18:
            st.write("")  # Empty column for spacing
        
        st.markdown("---")
        
        # Display each row with delete button - Title column gets 2x width
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15, col16, col17, col18 = st.columns([1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
            
            with col1:
                st.write(str(row['id']))
            with col2:
                st.write(row['title'][:40] + "..." if len(str(row['title'])) > 40 else row['title'])
            with col3:
                st.write(row['isbn'])
            with col4:
                st.write(row['category'])
            with col5:
                st.write(row['author_name'][:15] + "..." if len(str(row['author_name'])) > 15 else row['author_name'])
            with col6:
                st.write(row['call_number'])
            with col7:
                st.write(row['publisher_name'][:15] + "..." if len(str(row['publisher_name'])) > 15 else row['publisher_name'])
            with col8:
                st.write(str(row['publication_year']))
            with col9:
                st.write(row['language'])
            with col10:
                st.write(str(row['total_copy']))
            with col11:
                st.write(row['acquisition_type'])
            with col12:
                st.write(str(row['acquisition_date'])[:10] if row['acquisition_date'] else "")
            with col13:
                st.write(f"${row['price']:.2f}" if row['price'] else "$0.00")
            with col14:
                st.write(row['condition'])
            with col15:
                st.write(row['status'])
            with col16:
                st.write(row['book_location'][:15] + "..." if len(str(row['book_location'])) > 15 else row['book_location'])
            with col17:
                col17_1, col17_2 = st.columns(2)
                with col17_1:
                    # Edit button with white background styling
                    st.markdown("""
                    <style>
                    div[data-testid="stButton"] button[kind="secondary"] {
                        background-color: white !important;
                        color: #1f77b4 !important;
                        border: 2px solid #1f77b4 !important;
                        border-radius: 4px !important;
                        font-weight: bold !important;
                    }
                    div[data-testid="stButton"] button[kind="secondary"]:hover {
                        background-color: #f0f8ff !important;
                        border-color: #0d6efd !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    if st.button("✏️", key=f"edit_{row['id']}", type="secondary", help="Edit book copy"):
                        # Store edit information in session state
                        st.session_state.edit_copy_id = row['id']
                        st.session_state.edit_book_title = row['title']
                        st.session_state.edit_condition = row['condition']
                        st.session_state.edit_status = row['status']
                        st.session_state.edit_book_location = row['book_location']
                        st.session_state.page = "edit_copy"
                        st.rerun()
                with col17_2:
                    # Delete button with red background styling
                    st.markdown("""
                    <style>
                    div[data-testid="stButton"] button[kind="primary"] {
                        background-color: #dc3545 !important;
                        color: white !important;
                        border: 2px solid #dc3545 !important;
                        border-radius: 4px !important;
                        font-weight: bold !important;
                    }
                    div[data-testid="stButton"] button[kind="primary"]:hover {
                        background-color: #c82333 !important;
                        border-color: #bd2130 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️", key=f"delete_{row['id']}", type="primary", help="Delete book copy"):
                        # Store delete information in session state
                        st.session_state.delete_copy_id = row['id']
                        st.session_state.delete_book_title = row['title']
                        st.session_state.delete_total_copies = row['total_copy']
                        st.session_state.delete_book_id = row.get('book_id')
                        st.session_state.show_delete_confirm = True
                        st.rerun()
            with col18:
                st.write("")  # Empty column for spacing

        # Delete confirmation modal using Streamlit
        if st.session_state.get('show_delete_confirm', False):
            copy_id = st.session_state.get('delete_copy_id')
            book_title = st.session_state.get('delete_book_title')
            total_copies = st.session_state.get('delete_total_copies')
            book_id = st.session_state.get('delete_book_id')
            
            # Create a modal-like container
            st.markdown("---")
            st.markdown("### 🗑️ Delete Confirmation")
            
            if total_copies <= 1:
                # Critical warning for last copy - all in one box
                st.error(f"""⚠️ **CRITICAL WARNING** ⚠️

You are about to delete the last copy of **{book_title}**.

After this operation:
• Book **{book_title}** will have NO remaining copies
• The entire book will be PERMANENTLY REMOVED from the database
• This action CANNOT be undone""")
            else:
                # Regular confirmation for multiple copies - all in one box
                st.info(f"""Are you sure you want to delete this book copy?

Book: **{book_title}**
Remaining copies after deletion: {total_copies - 1}""")
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("❌ CANCEL", key="cancel_modal", type="secondary"):
                    st.session_state.show_delete_confirm = False
                    st.rerun()
            
            with col2:
                if st.button("✅ CONFIRM DELETE", key="confirm_modal", type="primary"):
                    # Delete book copy
                    api_client = APIClient()
                    if api_client.delete_book_copy(copy_id):
                        # Delete book if this was the last copy
                        if total_copies <= 1 and book_id:
                            api_client.delete_book(book_id)
                        st.success("✅ Book copy deleted successfully!" + (" Book also removed from database." if total_copies <= 1 else ""))
                        st.cache_data.clear()
                        # Clear session state
                        st.session_state.show_delete_confirm = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete book copy.")
            
            with col3:
                st.write("")  # Empty column for spacing
            
            st.markdown("---")

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
        st.session_state.add_form = {'title': '', 'isbn': '', 'category': list(CATEGORY_ID_MAPPING.keys())[0], 
                                     'author_name': '', 'call_number': '', 'publisher_name': '', 'publication_year': 0, 
                                     'language': list(LANGUAGE_CODE_MAPPING.keys())[0], 'total_copy': 0, 'acquisition_type': list(ACQUISITION_TYPE_MAPPING.keys())[0], 'acquisition_date': datetime.now().date(), 
                                     'price': 0.0, 'condition': list(BOOK_CONDITION_MAPPING.keys())[0], 'status': list(BOOK_STATUS_MAPPING.keys())[0], 'location_area': list(BOOK_LOCATION_AREA_MAPPING.keys())[0], 'book_location_notes': ''}
    
    with st.form("add_book_form"):
        st.session_state.add_form['title'] = st.text_input("Book Title", value=st.session_state.add_form['title'])
        st.session_state.add_form['isbn'] = st.text_input("ISBN", value=st.session_state.add_form['isbn'])
        
        # Category dropdown with pre-defined list
        categories = list(CATEGORY_ID_MAPPING.keys())
        current_category = st.session_state.add_form['category']
        if current_category not in categories:
            current_category = categories[0]  # Default to first category if current not found
        category_index = categories.index(current_category)
        st.session_state.add_form['category'] = st.selectbox("Category", categories, index=category_index)
        
        st.session_state.add_form['author_name'] = st.text_input("Author Name", value=st.session_state.add_form['author_name'])
        
        # Call number field with generate button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.session_state.add_form['call_number'] = st.text_input("Call Number", value=st.session_state.add_form['call_number'], disabled=True)
        with col2:
            if st.form_submit_button("Generate", type="secondary"):
                # Generate call number when button is clicked
                if st.session_state.add_form['author_name']:
                    last_name = st.session_state.add_form['author_name'].split()[-1].upper()
                    first_three = last_name[:3] if len(last_name) >= 3 else last_name.ljust(3, 'X')  # Pad with 'X' if less than 3 chars
                    # Get category ID from mapping and format as 3-digit string
                    category_id = CATEGORY_ID_MAPPING[st.session_state.add_form['category']]
                    category_code = f"{category_id:03d}"  # Format as 3-digit string (001, 002, etc.)
                    st.session_state.add_form['call_number'] = f"{category_code}_{first_three}"
                    st.rerun()
                else:
                    st.warning("Please enter an author name first.")
        
        st.session_state.add_form['publisher_name'] = st.text_input("Publisher Name", value=st.session_state.add_form['publisher_name'])
        st.session_state.add_form['publication_year'] = st.number_input("Publication Year", min_value=0, max_value=datetime.now().year, value=st.session_state.add_form['publication_year'])
        # Language dropdown with pre-defined options
        languages = list(LANGUAGE_CODE_MAPPING.keys())
        current_language = st.session_state.add_form['language']
        if current_language not in languages:
            current_language = languages[0]  # Default to first language if current not found
        language_index = languages.index(current_language)
        st.session_state.add_form['language'] = st.selectbox("Language", languages, index=language_index)
        st.session_state.add_form['total_copy'] = st.number_input("Total Copies", min_value=0, value=st.session_state.add_form['total_copy'])
        
        # Acquisition type dropdown with predefined options
        acquisition_types = list(ACQUISITION_TYPE_MAPPING.keys())
        current_acquisition_type = st.session_state.add_form.get('acquisition_type', acquisition_types[0])
        if current_acquisition_type not in acquisition_types:
            current_acquisition_type = acquisition_types[0]
        acquisition_index = acquisition_types.index(current_acquisition_type)
        st.session_state.add_form['acquisition_type'] = st.selectbox("Acquisition Type", acquisition_types, index=acquisition_index)
        st.session_state.add_form['acquisition_date'] = st.date_input("Acquisition Date", value=st.session_state.add_form['acquisition_date'])
        st.session_state.add_form['price'] = st.number_input("Price", min_value=0.0, format="%.2f", value=st.session_state.add_form['price'])
        # Condition dropdown with predefined options
        conditions = list(BOOK_CONDITION_MAPPING.keys())
        current_condition = st.session_state.add_form.get('condition', conditions[0])
        if current_condition not in conditions:
            current_condition = conditions[0]
        condition_index = conditions.index(current_condition)
        st.session_state.add_form['condition'] = st.selectbox("Condition", conditions, index=condition_index)
        
        # Status dropdown with predefined options
        status_options = list(BOOK_STATUS_MAPPING.keys())
        current_status = st.session_state.add_form.get('status', status_options[0])
        if current_status not in status_options:
            current_status = status_options[0]
        status_index = status_options.index(current_status)
        st.session_state.add_form['status'] = st.selectbox("Status", status_options, index=status_index)
        
        # Book Location Area dropdown with predefined options
        location_areas = list(BOOK_LOCATION_AREA_MAPPING.keys())
        current_location_area = st.session_state.add_form.get('location_area', location_areas[0])
        if current_location_area not in location_areas:
            current_location_area = location_areas[0]
        location_area_index = location_areas.index(current_location_area)
        st.session_state.add_form['location_area'] = st.selectbox("Book Location Area", location_areas, index=location_area_index)
        
        st.session_state.add_form['book_location_notes'] = st.text_input("Book Location Notes", value=st.session_state.add_form['book_location_notes'])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Create new book"):
                # Step 1: Check if book title already exists
                book_title = st.session_state.add_form['title'].strip()
                author_name = st.session_state.add_form['author_name'].strip()
                publisher_name = st.session_state.add_form['publisher_name'].strip()
                location_area = st.session_state.add_form['location_area']
                
                if not book_title:
                    st.error("Book title is required!")
                elif not author_name:
                    st.error("Author name is required!")
                elif not publisher_name:
                    st.error("Publisher name is required!")
                elif not location_area:
                    st.error("Book Location Area is required!")
                else:
                    if APIClient.check_book_title_exists(book_title):
                        st.error("This book title already exists in DB, please use the 'Add new book copy for existing book' option instead.")
                    else:
                        # Title doesn't exist, proceed with book creation
                        st.info("🔍 Resolving author, publisher, and location information...")
                if APIClient.add_new_book_details():  # Call the static method without arguments
                            # Get the number of copies created
                            total_copies = st.session_state.add_form.get('total_copy', 0)
                            if total_copies == 1:
                                success_message = "✅ Book created successfully with 1 book copy!"
                            else:
                                success_message = f"✅ Book created successfully with {total_copies} book copies!"
                            
                            # Set success message in session state
                            st.session_state.book_creation_success = success_message
                            # Clear cache to ensure new data is loaded on main page
                            st.cache_data.clear()
                            st.session_state.page = "main"
                            st.rerun()
        with col2:
            if st.form_submit_button("Back to Main Page"):
                st.session_state.page = "main"
                st.rerun()
    

# Add book copy page
def add_book_copy_page():
    st.title("Add New Book Copy for Existing Book")
    
    
    # Get all books for dropdown
    try:
        # Use the books API directly instead of get_all_book_details
        books_response = requests.get("http://localhost:8000/api/v1/book/?limit=9999")
        books_response.raise_for_status()
        books_data = books_response.json()
        
        if not books_data:
            st.error("No books found in the database. Please add a book first.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Back to Main Page"):
                    st.session_state.page = "main"
                    st.rerun()
            with col2:
                if st.button("Add New Book Instead"):
                    st.session_state.page = "add"
                    st.rerun()
            return
        
        # Create book options for dropdown
        book_options = {}
        for book in books_data:
            book_id = book.get('book_id')
            title = book.get('title', 'Unknown Title')
            author = book.get('author_name', 'Unknown Author')
            
            # Only include books with valid book_id
            if book_id is not None:
                book_options[f"{title} by {author} (ID: {book_id})"] = book_id
        
        # Display success message if exists
        if 'book_copy_success' in st.session_state:
            st.success(st.session_state.book_copy_success)
            # Clear the success message after showing it
            del st.session_state.book_copy_success
        
        with st.form("add_copy_form"):
            st.subheader("Book Selection")
            
            # Single book selection with searchable dropdown (no default selection)
            book_display_options = list(book_options.keys())
            # Add empty option at the beginning
            book_display_options_with_empty = ["-- Select a book --"] + book_display_options
            
            selected_book_display = st.selectbox(
                "Select Book (type to search):",
                options=book_display_options_with_empty,
                index=0,  # Default to empty selection
                help="Type to search for a book by title or author name"
            )
            
            # Get book ID only if a real book is selected (not the empty option)
            if selected_book_display and selected_book_display != "-- Select a book --":
                selected_book_id = book_options.get(selected_book_display)
            else:
                selected_book_id = None
            
            st.markdown("---")
            st.subheader("Copy Details")
            
            # Acquisition type dropdown
            acquisition_types = list(ACQUISITION_TYPE_MAPPING.keys())
            acquisition_type = st.selectbox(
                "Acquisition Type", 
                acquisition_types, 
                index=0
            )
            
            # Acquisition date
            acquisition_date = st.date_input(
                "Acquisition Date", 
                value=datetime.now().date()
            )
            
            # Price
            price = st.number_input(
                "Price", 
                min_value=0.0, 
                format="%.2f", 
                value=0.0
            )
            
            # Condition dropdown
            conditions = list(BOOK_CONDITION_MAPPING.keys())
            condition = st.selectbox(
                "Condition", 
                conditions, 
                index=0
            )
            
            # Status dropdown
            status_options = list(BOOK_STATUS_MAPPING.keys())
            status = st.selectbox(
                "Status", 
                status_options, 
                index=0
            )
            
            # Location area dropdown
            location_areas = list(BOOK_LOCATION_AREA_MAPPING.keys())
            location_area = st.selectbox(
                "Book Location Area", 
                location_areas, 
                index=0
            )
            
            # Location details (free text)
            location_details = st.text_input(
                "Location Details", 
                placeholder="Additional location information (optional)"
            )
            
            # Form submission buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Create Book Copy", type="primary"):
                    if not selected_book_id:
                        st.error("Please select a book first!")
                    else:
                        # Create book copy
                        copy_data = {
                            'book_id': selected_book_id,
                            'acquisition_type': ACQUISITION_TYPE_MAPPING[acquisition_type],
                            'acquisition_date': acquisition_date.isoformat(),
                            'price': price,
                            'condition': BOOK_CONDITION_MAPPING[condition],
                            'status': BOOK_STATUS_MAPPING[status],
                            'location_id': BOOK_LOCATION_AREA_MAPPING[location_area],
                            'notes': location_details
                        }
                        
                        try:
                            api_client = APIClient()
                            result = api_client.create_book_copy(copy_data)
                            
                            if result:
                                # Set success message in session state
                                st.session_state.book_copy_success = "✅ Book copy created successfully!"
                                # Clear cache to ensure new data is loaded
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ Failed to create book copy. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error creating book copy: {str(e)}")
            
            with col2:
                if st.form_submit_button("Back to Main Page"):
                    st.session_state.page = "main"
                    st.rerun()
            
            with col3:
                if st.form_submit_button("Add New Book Instead"):
                    st.session_state.page = "add"
                    st.rerun()
            
        
        # Form is properly closed here
        pass
    
    except Exception as e:
        st.error(f"Error loading books: {str(e)}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back to Main Page"):
                st.session_state.page = "main"
                st.rerun()
        with col2:
            if st.button("Add New Book Instead"):
                st.session_state.page = "add"
                st.rerun()

def edit_book_copy_page():
    """Edit book copy page - only allows editing condition and book location"""
    st.title("Edit Book Copy")
    
    # Get edit information from session state
    copy_id = st.session_state.get('edit_copy_id')
    book_title = st.session_state.get('edit_book_title')
    current_condition = st.session_state.get('edit_condition')
    current_status = st.session_state.get('edit_status')
    current_location = st.session_state.get('edit_book_location')
    
    if not copy_id:
        st.error("No book copy selected for editing.")
        if st.button("Back to Main Page"):
            st.session_state.page = "main"
            st.rerun()
        return
    
    # Display book information (read-only)
    st.markdown("### Book Information (Read-Only)")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Book Title", value=book_title, disabled=True)
    with col2:
        st.text_input("Book Copy ID", value=copy_id, disabled=True)
    
    st.markdown("---")
    
    # Edit form
    with st.form("edit_book_copy_form"):
        st.markdown("### Editable Fields")
        
        # Condition dropdown
        condition_options = list(BOOK_CONDITION_MAPPING.keys())
        current_condition_index = condition_options.index(current_condition) if current_condition in condition_options else 0
        new_condition = st.selectbox("Condition", condition_options, index=current_condition_index)
        
        # Status dropdown
        status_options = list(BOOK_STATUS_MAPPING.keys())
        current_status_index = status_options.index(current_status) if current_status in status_options else 0
        new_status = st.selectbox("Status", status_options, index=current_status_index)
        
        # Book location dropdown
        location_options = list(BOOK_LOCATION_AREA_MAPPING.keys())
        current_location_index = location_options.index(current_location) if current_location in location_options else 0
        new_location = st.selectbox("Book Location Area", location_options, index=current_location_index)
        
        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.form_submit_button("Update Book Copy", type="primary"):
                # Prepare update data
                update_data = {
                    "condition": BOOK_CONDITION_MAPPING[new_condition],
                    "status": BOOK_STATUS_MAPPING[new_status],
                    "location_id": BOOK_LOCATION_AREA_MAPPING[new_location]
                }
                
                # Update book copy
                api_client = APIClient()
                if api_client.update_book_copy(copy_id, update_data):
                    st.success("✅ Book copy updated successfully!")
                    # Clear cache to refresh data
                    st.cache_data.clear()
                    # Store success message
                    st.session_state.edit_success = f"Book copy for '{book_title}' updated successfully!"
                    # Return to main page
                    st.session_state.page = "main"
                    st.rerun()
                else:
                    st.error("❌ Failed to update book copy.")
    
    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Main Page"):
            st.session_state.page = "main"
            st.rerun()
    with col2:
        if st.button("Cancel Edit"):
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
            'title': '', 'isbn': '', 'category': list(CATEGORY_ID_MAPPING.keys())[0], 
            'author_name': '', 'call_number': '', 'publisher_name': '', 'publication_year': 0, 
            'language': list(LANGUAGE_CODE_MAPPING.keys())[0], 'total_copy': 0, 'acquisition_type': list(ACQUISITION_TYPE_MAPPING.keys())[0], 'acquisition_date': datetime.now().date(), 
            'price': 0.0, 'condition': list(BOOK_CONDITION_MAPPING.keys())[0], 'status': list(BOOK_STATUS_MAPPING.keys())[0], 'location_area': list(BOOK_LOCATION_AREA_MAPPING.keys())[0], 'book_location_notes': ''
        }
    
    with st.form("edit_book_form"):
        st.session_state.edit_form['title'] = st.text_input("Book Title", value=st.session_state.edit_form['title'])
        st.session_state.edit_form['isbn'] = st.text_input("ISBN", value=st.session_state.edit_form['isbn'])
        
        # Category dropdown with pre-defined list
        categories = list(CATEGORY_ID_MAPPING.keys())
        current_category = st.session_state.edit_form['category']
        if current_category not in categories:
            current_category = categories[0]  # Default to first category if current not found
        category_index = categories.index(current_category)
        st.session_state.edit_form['category'] = st.selectbox("Category", categories, index=category_index)
        
        st.session_state.edit_form['author_name'] = st.text_input("Author Name", value=st.session_state.edit_form['author_name'])
        
        # Auto-generate call number in real-time with first 3 characters of last name
        if st.session_state.edit_form['author_name']:
            last_name = st.session_state.edit_form['author_name'].split()[-1].upper()
            first_three = last_name[:3] if len(last_name) >= 3 else last_name.ljust(3, 'X')  # Pad with 'X' if less than 3 chars
            # Get category ID from mapping and format as 3-digit string
            category_id = CATEGORY_ID_MAPPING[st.session_state.edit_form['category']]
            category_code = f"{category_id:03d}"  # Format as 3-digit string (001, 002, etc.)
            st.session_state.edit_form['call_number'] = f"{category_code}_{first_three}"
        else:
            st.session_state.edit_form['call_number'] = book.get('call_number', '') if book else ""
        
        st.text_input("Call Number", value=st.session_state.edit_form['call_number'], disabled=True)
        
        st.session_state.edit_form['publisher_name'] = st.text_input("Publisher Name", value=st.session_state.edit_form['publisher_name'])
        st.session_state.edit_form['publication_year'] = st.number_input("Publication Year", min_value=0, 
                                        max_value=datetime.now().year, 
                                        value=st.session_state.edit_form['publication_year'])
        # Language dropdown with pre-defined options
        languages = list(LANGUAGE_CODE_MAPPING.keys())
        current_language = st.session_state.edit_form['language']
        if current_language not in languages:
            current_language = languages[0]  # Default to first language if current not found
        language_index = languages.index(current_language)
        st.session_state.edit_form['language'] = st.selectbox("Language", languages, index=language_index)
        st.session_state.edit_form['total_copy'] = st.number_input("Total Copies", min_value=0, value=st.session_state.edit_form['total_copy'])
        # Acquisition type dropdown with predefined options
        acquisition_types = list(ACQUISITION_TYPE_MAPPING.keys())
        current_acquisition_type = st.session_state.edit_form.get('acquisition_type', acquisition_types[0])
        if current_acquisition_type not in acquisition_types:
            current_acquisition_type = acquisition_types[0]
        acquisition_index = acquisition_types.index(current_acquisition_type)
        st.session_state.edit_form['acquisition_type'] = st.selectbox("Acquisition Type", acquisition_types, index=acquisition_index)
        
        st.session_state.edit_form['acquisition_date'] = st.date_input("Acquisition Date", 
                                       value=st.session_state.edit_form['acquisition_date'])
        st.session_state.edit_form['price'] = st.number_input("Price", min_value=0.0, format="%.2f", value=st.session_state.edit_form['price'])
        
        # Condition dropdown with predefined options
        conditions = list(BOOK_CONDITION_MAPPING.keys())
        current_condition = st.session_state.edit_form.get('condition', conditions[0])
        if current_condition not in conditions:
            current_condition = conditions[0]
        condition_index = conditions.index(current_condition)
        st.session_state.edit_form['condition'] = st.selectbox("Condition", conditions, index=condition_index)
        
        # Status dropdown with predefined options
        status_options = list(BOOK_STATUS_MAPPING.keys())
        current_status = st.session_state.edit_form.get('status', status_options[0])
        if current_status not in status_options:
            current_status = status_options[0]
        status_index = status_options.index(current_status)
        st.session_state.edit_form['status'] = st.selectbox("Status", status_options, index=status_index)
        
        # Book Location Area dropdown with predefined options
        location_areas = list(BOOK_LOCATION_AREA_MAPPING.keys())
        current_location_area = st.session_state.edit_form.get('location_area', location_areas[0])
        if current_location_area not in location_areas:
            current_location_area = location_areas[0]
        location_area_index = location_areas.index(current_location_area)
        st.session_state.edit_form['location_area'] = st.selectbox("Book Location Area", location_areas, index=location_area_index)
        
        st.session_state.edit_form['book_location_notes'] = st.text_input("Book Location Notes", value=st.session_state.edit_form.get('book_location_notes', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Create new book"):
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
            if st.form_submit_button("Back to Main Page"):
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
    elif st.session_state.page == "add_copy":
        add_book_copy_page()
    elif st.session_state.page == "edit_copy":
        edit_book_copy_page()
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
    