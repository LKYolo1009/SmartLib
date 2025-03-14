from sqlalchemy.dialects.postgresql import ENUM

# Define all your ENUM types
book_status = ENUM('available', 'borrowed', 'missing', 'unpublished', 'disposed', 
                  name='book_status', create_type=True)
book_condition = ENUM('new', 'good', 'fair', 'poor', 'damaged', 
                     name='book_condition', create_type=True)
acquisition_type = ENUM('purchased', 'donated', 
                       name='acquisition_type', create_type=True)
student_status = ENUM('active', 'inactive', 'suspended', 
                     name='student_status', create_type=True)
borrow_status = ENUM('borrowed', 'returned', 'overdue', 'lost', 
                    name='borrow_status', create_type=True)