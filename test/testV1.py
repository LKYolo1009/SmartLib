import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
today = datetime.now().strftime("%Y-%m-%d")
due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
extended_date = (datetime.now() + timedelta(days=28)).strftime("%Y-%m-%d")

# Helper functions
def print_response(response, operation):
    print(f"\n--- {operation} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# Test 1: Basic connectivity
def test_root():
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Testing Root Endpoint")
    return response.status_code == 200

# Test 2: Student Management
def test_student_operations():
    # Create a student
    student_data = {
        "name": "Test Student",
        "student_id": f"S{int(time.time())}",  # Generate unique ID based on timestamp
        "email": f"student{int(time.time())}@example.com"
    }
    
    response = requests.post(f"{BASE_URL}/student/", json=student_data)
    print_response(response, "Create Student")
    
    if response.status_code != 200 and response.status_code != 201:
        return False
    
    # Get the student
    response = requests.get(f"{BASE_URL}/student/{student_data['student_id']}")
    print_response(response, "Get Student")
    
    if response.status_code != 200:
        return False
    
    # Update student status
    status_data = {"status": "inactive"}
    response = requests.put(
        f"{BASE_URL}/student/{student_data['student_id']}/status", 
        json=status_data
    )
    print_response(response, "Update Student Status")
    
    return response.status_code == 200

# Test 3: Book Management
def test_book_operations():
    # Create a book copy
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": f"ISBN-{int(time.time())}",  # Generate unique ISBN
        "call_number": f"CN-{int(time.time())}",  # Generate unique call number
        "status": "available"
    }
    
    response = requests.post(f"{BASE_URL}/book_copy/", json=book_data)
    print_response(response, "Create Book Copy")
    
    if response.status_code != 200 and response.status_code != 201:
        return False
    
    # Get the book copy ID from response
    book_copy_id = response.json().get("id")
    if not book_copy_id:
        print("Failed to get book copy ID")
        return False
    
    # Get the book by ID
    response = requests.get(f"{BASE_URL}/book_copy/{book_copy_id}")
    print_response(response, "Get Book Copy")
    
    if response.status_code != 200:
        return False
    
    # Get book by call number
    response = requests.get(f"{BASE_URL}/book_copy/call-number/{book_data['call_number']}")
    print_response(response, "Get Book By Call Number")
    
    return response.status_code == 200, book_copy_id, book_data['call_number']

# Test 4: Borrowing Workflow
def test_borrowing_workflow(student_id, book_copy_id):
    # Borrow a book
    borrow_data = {
        "student_id": student_id,
        "copy_id": book_copy_id,
        "borrow_date": today,
        "due_date": due_date
    }
    
    response = requests.post(f"{BASE_URL}/borrowing/", json=borrow_data)
    print_response(response, "Borrow Book")
    
    if response.status_code != 200 and response.status_code != 201:
        return False
    
    # Get the borrow ID from response
    borrow_id = response.json().get("id")
    if not borrow_id:
        print("Failed to get borrow ID")
        return False
    
    # Get student borrowings
    response = requests.get(f"{BASE_URL}/borrowing/student/{student_id}")
    print_response(response, "Get Student Borrowings")
    
    if response.status_code != 200:
        return False
    
    # Extend borrowing
    extend_data = {"new_due_date": extended_date}
    response = requests.put(f"{BASE_URL}/borrowing/extend/{borrow_id}", json=extend_data)
    print_response(response, "Extend Borrowing")
    
    if response.status_code != 200:
        return False
    
    # Return book
    return_data = {"return_date": today}
    response = requests.put(f"{BASE_URL}/borrowing/return/{borrow_id}", json=return_data)
    print_response(response, "Return Book")
    
    return response.status_code == 200

# Test 5: Edge Cases
def test_edge_cases(student_id, book_copy_id, call_number):
    # Try to borrow an already borrowed book
    book_status = {"status": "borrowed"}
    requests.put(f"{BASE_URL}/book_copy/{book_copy_id}/status", json=book_status)
    
    borrow_data = {
        "student_id": student_id,
        "copy_id": book_copy_id,
        "borrow_date": today,
        "due_date": due_date
    }
    
    response = requests.post(f"{BASE_URL}/borrowing/", json=borrow_data)
    print_response(response, "Try to Borrow Already Borrowed Book")
    
    # Create 3 more books and try to borrow more than 3 books total
    # This assumes the student already has 3 books borrowed
    book_data = {
        "title": "Extra Book",
        "author": "Test Author",
        "isbn": f"ISBN-{int(time.time())}",
        "call_number": f"CN-{int(time.time())}",
        "status": "available"
    }
    
    book_response = requests.post(f"{BASE_URL}/book_copy/", json=book_data)
    if book_response.status_code == 200 or book_response.status_code == 201:
        extra_book_id = book_response.json().get("id")
        
        # Try to borrow a 4th book
        borrow_data = {
            "student_id": student_id,
            "copy_id": extra_book_id,
            "borrow_date": today,
            "due_date": due_date
        }
        
        response = requests.post(f"{BASE_URL}/borrowing/", json=borrow_data)
        print_response(response, "Try to Borrow More Than 3 Books")

    # Check for overdue books
    response = requests.get(f"{BASE_URL}/borrowing/overdue")
    print_response(response, "Check Overdue Books")
    
    return True  # Just a placeholder, we're just checking behavior here

# Run all tests
def run_all_tests():
    print("\n==== STARTING API TESTS ====\n")
    
    if not test_root():
        print("Root endpoint test failed, aborting.")
        return
    
    student_success = test_student_operations()
    if not student_success:
        print("Student operations test failed, aborting.")
        return
    
    # Get the student ID from the timestamp used earlier
    student_id = f"S{int(time.time() - 1)}"  # Approximate the ID we used
    
    book_success, book_copy_id, call_number = test_book_operations()
    if not book_success:
        print("Book operations test failed, aborting.")
        return
    
    borrow_success = test_borrowing_workflow(student_id, book_copy_id)
    if not borrow_success:
        print("Borrowing workflow test failed, aborting.")
        return
    
    edge_success = test_edge_cases(student_id, book_copy_id, call_number)
    
    print("\n==== ALL TESTS COMPLETED ====\n")

if __name__ == "__main__":
    run_all_tests()