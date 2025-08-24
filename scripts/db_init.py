from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta, timezone

# Add project root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Now we can import from app
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_database():
    """Clean all data and schema from the database"""
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # SQL script to completely clean the database
        cleanup_script = r"""
        -- 1. Drop all tables if they exist (in reverse order to respect foreign keys)
        DROP TABLE IF EXISTS borrowing_records CASCADE;
        DROP TABLE IF EXISTS book_copies CASCADE;
        DROP TABLE IF EXISTS books CASCADE;
        DROP TABLE IF EXISTS authors CASCADE;
        DROP TABLE IF EXISTS publishers CASCADE;
        DROP TABLE IF EXISTS dewey_categories CASCADE;
        DROP TABLE IF EXISTS languages CASCADE;
        DROP TABLE IF EXISTS students CASCADE;

        -- 2. Drop all enum types if they exist
        DROP TYPE IF EXISTS book_status CASCADE;
        DROP TYPE IF EXISTS book_condition CASCADE;
        DROP TYPE IF EXISTS acquisition_type CASCADE;
        DROP TYPE IF EXISTS borrow_status CASCADE;
        DROP TYPE IF EXISTS student_status CASCADE;

        COMMIT;
        """

        # Execute the cleanup script
        with SessionLocal() as db:
            logger.info("Starting database cleanup...")
            db.execute(text(cleanup_script))
            db.commit()
            logger.info("Database cleanup completed successfully!")
            logger.info("All tables, enums, and data have been removed.")
            logger.info("Database is now empty and ready for initialization.")
        return True
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        return False

def init_db():
    """Initialize the database with tables and sample data"""
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # SQL script for schema and data initialization
        sql_script = r"""
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone to UTC for consistency
SET timezone = 'UTC';

-- Drop existing enum types if they exist
DROP TYPE IF EXISTS book_status CASCADE;
DROP TYPE IF EXISTS book_condition CASCADE;
DROP TYPE IF EXISTS acquisition_type CASCADE;
DROP TYPE IF EXISTS borrow_status CASCADE;
DROP TYPE IF EXISTS student_status CASCADE;

-- Create enum types 
CREATE TYPE book_status AS ENUM ('available', 'borrowed', 'missing', 'unpublished', 'disposed');
CREATE TYPE book_condition AS ENUM ('new', 'good', 'fair', 'poor', 'damaged');
CREATE TYPE acquisition_type AS ENUM ('purchased', 'donated');
CREATE TYPE student_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE borrow_status AS ENUM ('borrowed', 'returned', 'overdue', 'lost');

-- Drop tables if they exist (in reverse order to respect foreign keys)
DROP TABLE IF EXISTS borrowing_records CASCADE;
DROP TABLE IF EXISTS book_copies CASCADE;
DROP TABLE IF EXISTS book_locations CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS publishers CASCADE;
DROP TABLE IF EXISTS dewey_categories CASCADE;
DROP TABLE IF EXISTS languages CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- Create tables

-- Languages
CREATE TABLE languages (
    language_code VARCHAR(3) PRIMARY KEY,
    language_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Book Locations
CREATE TABLE book_locations (
    location_id SERIAL PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL UNIQUE,
    location_description TEXT,
    location_qr_code UUID DEFAULT uuid_generate_v4() UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authors
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    author_name VARCHAR(255) NOT NULL UNIQUE
);

-- Publishers
CREATE TABLE publishers (
    publisher_id SERIAL PRIMARY KEY,
    publisher_name VARCHAR(128) NOT NULL UNIQUE
);

-- Dewey Categories
CREATE TABLE dewey_categories (
    category_id SERIAL PRIMARY KEY,
    category_code VARCHAR(20) NOT NULL UNIQUE,
    category_name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES dewey_categories(category_id),
    CONSTRAINT valid_dewey_code CHECK (category_code ~ '^[0-9]{3}(\\.[0-9]+)?$')
);

-- Students
CREATE TABLE students (
    matric_number VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    status student_status DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    telegram_id VARCHAR(50) UNIQUE,
    CONSTRAINT valid_matric CHECK (matric_number ~ '^A[0-9]{7}[A-Za-z]$')
);
CREATE INDEX idx_student_status ON students(status);

-- Books
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE,
    title VARCHAR(255) NOT NULL,
    call_number VARCHAR(50) NOT NULL,
    author_id INTEGER NOT NULL REFERENCES authors(author_id),
    publisher_id INTEGER REFERENCES publishers(publisher_id),
    publication_year SMALLINT,
    language_code VARCHAR(3) REFERENCES languages(language_code),
    category_id INTEGER NOT NULL REFERENCES dewey_categories(category_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_call_number CHECK (call_number ~ '^[0-9]{3}_[A-Z]{3}$')
);
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_call_number ON books(call_number);

-- Book Copies
CREATE TABLE book_copies (
    copy_id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    qr_code UUID DEFAULT uuid_generate_v4(),
    acquisition_type acquisition_type NOT NULL,
    acquisition_date DATE NOT NULL,
    price NUMERIC(10,2),
    condition book_condition DEFAULT 'good',
    status book_status DEFAULT 'available',
    location_id INTEGER REFERENCES book_locations(location_id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_book_copies_status ON book_copies(status);
CREATE INDEX idx_book_copies_location ON book_copies(location_id);

-- Borrowing Records
CREATE TABLE borrowing_records (
    borrow_id SERIAL PRIMARY KEY,
    copy_id INTEGER NOT NULL REFERENCES book_copies(copy_id),
    matric_number VARCHAR(20) NOT NULL REFERENCES students(matric_number),
    borrow_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    extension_date TIMESTAMP WITH TIME ZONE,
    return_date TIMESTAMP WITH TIME ZONE,
    status borrow_status DEFAULT 'borrowed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_dates CHECK (borrow_date <= due_date),
    CONSTRAINT valid_extension CHECK (extension_date IS NULL OR extension_date < due_date),
    CONSTRAINT valid_return CHECK (return_date IS NULL OR return_date >= borrow_date)
);
CREATE INDEX idx_borrowing_status ON borrowing_records(status);
CREATE INDEX idx_borrowing_due_date ON borrowing_records(due_date);
CREATE INDEX idx_borrowing_matric ON borrowing_records(matric_number);

-- Insert sample data

-- Insert languages
INSERT INTO languages (language_code, language_name) VALUES
    ('eng', 'English'),
    ('chi', 'Chinese'),
    ('jpn', 'Japanese'),
    ('kor', 'Korean'),
    ('mal', 'Malay'),
    ('tam', 'Tamil'),
    ('spa', 'Spanish'),
    ('fre', 'French'),
    ('ger', 'German'),
    ('rus', 'Russian');

-- Insert Dewey categories (main classes)
INSERT INTO dewey_categories (category_code, category_name, parent_id) VALUES
    ('000', 'General Knowledge & Information', NULL),
    ('100', 'Philosophy & Psychology', NULL),
    ('200', 'Religion', NULL),
    ('300', 'Social Sciences', NULL),
    ('400', 'Language', NULL),
    ('500', 'Science', NULL),
    ('600', 'Technology & Medicine', NULL),
    ('700', 'Arts & Recreation', NULL),
    ('800', 'Literature', NULL),
    ('900', 'History & Geography', NULL);

-- Insert Dewey subcategories
INSERT INTO dewey_categories (category_code, category_name, parent_id) VALUES
    ('004', 'Computer Science', 1),
    ('005', 'Programming', 1),
    ('150', 'Psychology', 2),
    ('220', 'Bible', 3),
    ('330', 'Economics', 4),
    ('370', 'Education', 4),
    ('420', 'English & Old English', 5),
    ('501', 'Theory of Science', 6),
    ('510', 'Mathematics', 6),
    ('550', 'Earth Sciences', 6),
    ('570', 'Biology', 6),
    ('610', 'Medicine', 7),
    ('641', 'Food & Drink', 7),
    ('741', 'Drawing & Drawings', 8),
    ('780', 'Music', 8),
    ('813', 'American Fiction', 9),
    ('823', 'English Fiction', 9),
    ('954', 'South Asia; India', 10);

-- Insert authors
INSERT INTO authors (author_name) VALUES
    ('J.K. Rowling'),
    ('George Orwell'),
    ('Jane Austen'),
    ('F. Scott Fitzgerald'),
    ('Harper Lee'),
    ('Agatha Christie'),
    ('J.R.R. Tolkien'),
    ('Charles Dickens'),
    ('Mark Twain'),
    ('Leo Tolstoy'),
    ('Haruki Murakami'),
    ('Gabriel García Márquez'),
    ('Margaret Atwood'),
    ('Neil Gaiman'),
    ('Stephen King'),
    ('Thomas H. Cormen'),
    ('Stuart Russell'),
    ('Lillian Pierson'),
    ('Andrew S. Tanenbaum'),
    ('Oxford University Press'),
    ('Yuval Noah Harari'),
    ('Malcolm Gladwell'),
    ('Bill Bryson'),
    ('Daniel Kahneman'),
    ('Cal Newport'),
    ('James Clear'),
    ('Angela Duckworth'),
    ('Simon Sinek'),
    ('Adam Grant'),
    ('Brene Brown');

-- Insert publishers
INSERT INTO publishers (publisher_name) VALUES
    ('Penguin Random House'),
    ('HarperCollins'),
    ('Simon & Schuster'),
    ('Hachette Book Group'),
    ('Macmillan Publishers'),
    ('Oxford University Press'),
    ('Cambridge University Press'),
    ('Scholastic'),
    ('Wiley'),
    ('Pearson Education'),
    ('MIT Press'),
    ('Princeton University Press'),
    ('Springer'),
    ('Addison-Wesley'),
    ('O''Reilly Media'),
    ('Bloomsbury'),
    ('Vintage Books'),
    ('Little, Brown and Company'),
    ('Riverhead Books'),
    ('Crown Publishing Group');

-- Insert book locations
INSERT INTO book_locations (location_name, location_description) VALUES
    ('Main Shelf A', 'Main book area, including literature and history books'),
    ('Main Shelf B', 'Science and technology book area'),
    ('Main Shelf C', 'Art and music book area'),
    ('Reference Book Area', 'Reference book and tool book area'),
    ('Journal Area', 'Journal and magazine area'),
    ('New Book Display Area', 'New book display area'),
    ('Special Collection Area', 'Rare book and special collection area'),
    ('Computer Science Area', 'Computer science book area'),
    ('Medical Area', 'Medical book area'),
    ('Study Room A', 'Quiet study area'),
    ('Study Room B', 'Group study area'),
    ('Electronic Resource Area', 'Electronic resource and multimedia area'),
    ('Children''s Book Area', 'Children''s book area'),
    ('Foreign Language Book Area', 'Foreign language book area'),
    ('Ancient Book Area', 'Ancient book and precious document area'),
    ('Multimedia Area', 'Multimedia resource area'),
    ('Self-Study Room', 'Self-study and reading area'),
    ('Discussion Room', 'Group discussion area'),
    ('Reading Room', 'Reading and reference area'),
    ('Exhibition Area', 'Book exhibition and display area');

-- Insert students
INSERT INTO students (matric_number, full_name, email, status, telegram_id) VALUES
    ('A1234567B', 'John Smith', 'john.smith@u.nus.edu', 'active', '123456789'),
    ('A2345678C', 'Emma Wong', 'emma.wong@u.nus.edu', 'active', '234567890'),
    ('A3456789D', 'David Tan', 'david.tan@u.nus.edu', 'active', '345678901'),
    ('A4567890E', 'Sarah Johnson', 'sarah.j@u.nus.edu', 'active', '456789012'),
    ('A5678901F', 'Michael Zhang', 'michael.z@u.nus.edu', 'active', '567890123'),
    ('A6789012G', 'Linda Kumar', 'linda.k@u.nus.edu', 'active', '678901234'),
    ('A7890123H', 'James Wilson', 'james.w@u.nus.edu', 'inactive', '789012345'),  
    ('A8901234J', 'Olivia Lee', 'olivia.l@u.nus.edu', 'active', '890123456'),
    ('A9012345K', 'Robert Chen', 'robert.c@u.nus.edu', 'suspended', '901234567'),
    ('A0123456L', 'Jennifer Lim', 'jennifer.l@u.nus.edu', 'active', '012345678'),
    ('A1122334M', 'Alex Thompson', 'alex.t@u.nus.edu', 'active', '112233445'),
    ('A2233445N', 'Sophia Park', 'sophia.p@u.nus.edu', 'active', '223344556'),
    ('A3344556O', 'William Brown', 'william.b@u.nus.edu', 'active', '334455667'),
    ('A4455667P', 'Isabella Garcia', 'isabella.g@u.nus.edu', 'active', '445566778'),
    ('A5566778Q', 'Ethan Kim', 'ethan.k@u.nus.edu', 'active', '556677889'),
    ('A6677889R', 'Mia Patel', 'mia.p@u.nus.edu', 'active', '667788990'),
    ('A7788990S', 'Noah Anderson', 'noah.a@u.nus.edu', 'active', '778899001'),
    ('A8899001T', 'Ava Martinez', 'ava.m@u.nus.edu', 'active', '889900112'),
    ('A9900112U', 'Lucas Wang', 'lucas.w@u.nus.edu', 'active', '990011223'),
    ('A0011223V', 'Ruofan Xu', 'ruofan.x@u.nus.edu', 'active', '6640904968'),
    ('A0012345X', 'Jing Han', 'han_jing@u.nus.edu', 'active', '883061077'),
    ('A6666666A', 'Selvia T', 'selvia_t@u.nus.edu', 'active', '962442060');

-- Insert books
INSERT INTO books (isbn, title, call_number, author_id, publisher_id, publication_year, language_code, category_id) VALUES
    ('9780747532743', 'Harry Potter and the Philosopher''s Stone', '800_ROW', 1, 8, 1997, 'eng', 17),
    ('9780451524935', '1984', '800_ORW', 2, 1, 1949, 'eng', 17),
    ('9780141439518', 'Pride and Prejudice', '800_AUS', 3, 1, 1813, 'eng', 17),
    ('9780743273565', 'The Great Gatsby', '800_FIT', 4, 3, 1925, 'eng', 16),
    ('9780061120084', 'To Kill a Mockingbird', '800_LEE', 5, 2, 1960, 'eng', 16),
    ('9780062073488', 'Murder on the Orient Express', '800_CHR', 6, 2, 1934, 'eng', 17),
    ('9780547928227', 'The Hobbit', '800_TOL', 7, 8, 1937, 'eng', 17),
    ('9780141439563', 'A Tale of Two Cities', '800_DIC', 8, 1, 1859, 'eng', 17),
    ('9780143107422', 'Adventures of Huckleberry Finn', '800_TWA', 9, 1, 1884, 'eng', 16),
    ('9780198800545', 'War and Peace', '800_TOL', 10, 6, 1869, 'eng', 17),
    ('9780307593313', '1Q84', '800_MUR', 11, 1, 2009, 'eng', 17),
    ('9780060883287', 'One Hundred Years of Solitude', '800_MAR', 12, 2, 1967, 'eng', 17),
    ('9780385490818', 'The Handmaid''s Tale', '800_ATW', 13, 1, 1985, 'eng', 17),
    ('9780062059888', 'American Gods', '800_GAI', 14, 2, 2001, 'eng', 17),
    ('9781501142970', 'The Shining', '800_KIN', 15, 3, 1977, 'eng', 16),
    ('9780262033848', 'Introduction to Algorithms', '001_MIT', 16, 11, 2009, 'eng', 2),
    ('9780134670942', 'Artificial Intelligence: A Modern Approach', '001_RUS', 17, 10, 2016, 'eng', 2),
    ('9781119293491', 'Data Science For Dummies', '001_PIC', 18, 9, 2017, 'eng', 2),
    ('9780132126953', 'Computer Networks', '001_TAN', 19, 10, 2013, 'eng', 2),
    ('9780199571857', 'Oxford Handbook of Clinical Medicine', '610_LON', 20, 6, 2017, 'eng', 12),
    ('9780062316097', 'Sapiens: A Brief History of Humankind', '300_HAR', 21, 2, 2014, 'eng', 3),
    ('9780316478526', 'Outliers: The Story of Success', '300_GLA', 22, 3, 2008, 'eng', 3),
    ('9780767908184', 'A Short History of Nearly Everything', '500_BRY', 23, 1, 2003, 'eng', 5),
    ('9780374533557', 'Thinking, Fast and Slow', '150_KAH', 24, 4, 2011, 'eng', 3),
    ('9781455586691', 'Deep Work', '650_NEW', 25, 5, 2016, 'eng', 3),
    ('9780735211292', 'Atomic Habits', '150_CLE', 26, 1, 2018, 'eng', 3),
    ('9781501111105', 'Grit: The Power of Passion and Perseverance', '150_DUC', 27, 3, 2016, 'eng', 3),
    ('9781591846352', 'Start with Why', '650_SIN', 28, 3, 2009, 'eng', 3),
    ('9781982137278', 'Think Again', '150_GRA', 29, 3, 2021, 'eng', 3),
    ('9781592408412', 'Daring Greatly', '150_BRO', 30, 1, 2012, 'eng', 3);

-- Insert book copies
INSERT INTO book_copies (book_id, acquisition_type, acquisition_date, price, condition, status, location_id) VALUES
    (1, 'purchased', '2020-01-15', 15.99, 'good', 'available', 1),
    (1, 'purchased', '2020-01-15', 15.99, 'good', 'available', 2),
    (2, 'purchased', '2019-11-20', 12.50, 'good', 'available', 4),
    (3, 'donated', '2018-05-12', NULL, 'fair', 'available', 3),
    (4, 'purchased', '2020-06-30', 14.95, 'good', 'available', 1),
    (5, 'purchased', '2019-08-18', 16.99, 'good', 'borrowed', 5),
    (6, 'donated', '2017-12-05', NULL, 'fair', 'available', 4),
    (7, 'purchased', '2021-02-28', 19.99, 'new', 'available', 3),
    (8, 'donated', '2018-03-17', NULL, 'poor', 'missing', 6),
    (9, 'purchased', '2020-09-12', 13.50, 'good', 'available', 2),
    (10, 'purchased', '2019-07-23', 22.99, 'good', 'available', 2),
    (11, 'purchased', '2021-01-09', 24.99, 'new', 'available', 3),
    (12, 'donated', '2016-11-30', NULL, 'fair', 'available', 5),
    (13, 'purchased', '2020-05-15', 18.75, 'good', 'borrowed', 1),
    (14, 'purchased', '2021-03-11', 20.50, 'new', 'available', 4),
    (15, 'purchased', '2019-10-25', 17.99, 'good', 'available', 3),
    (16, 'purchased', '2021-02-05', 65.99, 'good', 'available', 8),
    (17, 'purchased', '2022-01-15', 89.99, 'new', 'borrowed', 8),
    (18, 'donated', '2020-06-17', NULL, 'good', 'available', 5),
    (19, 'purchased', '2021-09-30', 72.50, 'good', 'available', 8),
    (20, 'purchased', '2022-05-12', 59.99, 'new', 'available', 9),
    (21, 'purchased', '2022-01-15', 29.99, 'new', 'available', 2),
    (21, 'purchased', '2022-01-15', 29.99, 'new', 'borrowed', 3),
    (22, 'purchased', '2021-06-20', 24.99, 'good', 'available', 5),
    (23, 'purchased', '2020-11-10', 27.50, 'good', 'available', 4),
    (24, 'purchased', '2021-03-05', 32.99, 'new', 'borrowed', 6),
    (25, 'purchased', '2022-02-28', 26.99, 'new', 'available', 3),
    (26, 'purchased', '2022-03-15', 28.99, 'new', 'borrowed', 2),
    (27, 'purchased', '2021-09-20', 25.99, 'good', 'available', 3),
    (28, 'purchased', '2020-12-10', 23.99, 'good', 'available', 5),
    (29, 'purchased', '2022-04-05', 27.99, 'new', 'borrowed', 1),
    (30, 'purchased', '2021-11-15', 26.99, 'good', 'available', 4);

-- Insert borrowing records (simplified with no duplicate copy_id usage)
INSERT INTO borrowing_records (copy_id, matric_number, borrow_date, due_date, return_date, status) VALUES
    -- Regular returned books (mostly 14 days default, some custom periods)
    (1, 'A1234567B', '2025-04-05 00:00:00+00:00', '2025-04-19 00:00:00+00:00', '2025-04-17 00:00:00+00:00', 'returned'),  -- 14 days, returned early
    (2, 'A2345678C', '2025-04-12 00:00:00+00:00', '2025-04-26 00:00:00+00:00', '2025-04-24 00:00:00+00:00', 'returned'),  -- 14 days, returned early
    (3, 'A3456789D', '2025-04-13 00:00:00+00:00', '2025-04-20 00:00:00+00:00', '2025-04-20 00:00:00+00:00', 'returned'),  -- 7 days, returned on time
    (4, 'A4567890E', '2025-04-14 00:00:00+00:00', '2025-04-28 00:00:00+00:00', '2025-04-28 00:00:00+00:00', 'returned'),  -- 14 days, returned on time
    (5, 'A5678901F', '2025-04-15 00:00:00+00:00', '2025-05-15 00:00:00+00:00', '2025-05-10 00:00:00+00:00', 'returned'), -- 30 days, returned early
    (6, 'A6789012G', '2025-04-16 00:00:00+00:00', '2025-04-30 00:00:00+00:00', '2025-04-30 00:00:00+00:00', 'returned'),  -- 14 days, returned on time
    (7, 'A7890123H', '2025-04-17 00:00:00+00:00', '2025-05-01 00:00:00+00:00', '2025-05-01 00:00:00+00:00', 'returned'),  -- 14 days, returned on time
    (8, 'A8901234J', '2025-04-18 00:00:00+00:00', '2025-05-18 00:00:00+00:00', '2025-05-15 00:00:00+00:00', 'returned'), -- 30 days, returned early
    (9, 'A0123456L', '2025-04-19 00:00:00+00:00', '2025-05-03 00:00:00+00:00', '2025-05-03 00:00:00+00:00', 'returned'),  -- 14 days, returned on time
    (10, 'A9012345K', '2025-04-20 00:00:00+00:00', '2025-05-04 00:00:00+00:00', '2025-05-04 00:00:00+00:00', 'returned'),  -- 14 days, returned on time

    -- Currently borrowed books (mostly 14 days default, some custom periods)
    (11, 'A1122334M', '2025-05-01 00:00:00+00:00', '2025-05-15 00:00:00+00:00', NULL, 'borrowed'),       -- 14 days
    (12, 'A2233445N', '2025-05-02 00:00:00+00:00', '2025-05-16 00:00:00+00:00', NULL, 'borrowed'),       -- 14 days
    (13, 'A3344556O', '2025-05-03 00:00:00+00:00', '2025-05-10 00:00:00+00:00', NULL, 'borrowed'),       -- 7 days
    (14, 'A4455667P', '2025-05-04 00:00:00+00:00', '2025-06-03 00:00:00+00:00', NULL, 'borrowed'),       -- 30 days
    (15, 'A5566778Q', '2025-05-05 00:00:00+00:00', '2025-05-19 00:00:00+00:00', NULL, 'borrowed'),       -- 14 days

    -- Overdue books (mostly 14 days default, some custom periods)
    (16, 'A6677889R', '2025-04-20 00:00:00+00:00', '2025-05-04 00:00:00+00:00', NULL, 'borrowed'),       -- 14 days, overdue
    (17, 'A7788990S', '2025-04-25 00:00:00+00:00', '2025-05-09 00:00:00+00:00', NULL, 'borrowed'),       -- 14 days, overdue
    (18, 'A8899001T', '2025-04-28 00:00:00+00:00', '2025-05-05 00:00:00+00:00', NULL, 'borrowed'),       -- 7 days, overdue

    -- More returned books (mostly 14 days default)
    (19, 'A9900112U', '2025-04-15 00:00:00+00:00', '2025-04-29 00:00:00+00:00', '2025-04-29 00:00:00+00:00', 'returned'), -- 14 days, returned on time
    (20, 'A0011223V', '2025-04-20 00:00:00+00:00', '2025-05-20 00:00:00+00:00', '2025-05-18 00:00:00+00:00', 'returned'), -- 30 days, returned early

    -- Overdue and returned late (mostly 14 days default)
    (21, 'A1234567B', '2025-04-01 00:00:00+00:00', '2025-04-15 00:00:00+00:00', '2025-04-19 00:00:00+00:00', 'returned'), -- 14 days, returned 4 days late
    (22, 'A2345678C', '2025-04-05 00:00:00+00:00', '2025-04-19 00:00:00+00:00', '2025-04-25 00:00:00+00:00', 'returned'), -- 14 days, returned 6 days late
    (23, 'A3456789D', '2025-04-10 00:00:00+00:00', '2025-04-17 00:00:00+00:00', '2025-04-22 00:00:00+00:00', 'returned'), -- 7 days, returned 5 days late

    -- Severely overdue (mostly 14 days default)
    (24, 'A4567890E', '2025-04-15 00:00:00+00:00', '2025-04-29 00:00:00+00:00', NULL, 'borrowed'),       -- 14 days, severely overdue
    (25, 'A5678901F', '2025-04-20 00:00:00+00:00', '2025-05-20 00:00:00+00:00', NULL, 'borrowed'),       -- 30 days, severely overdue

    -- Extended and returned on time (mostly 14 days default)
    (26, 'A6789012G', '2025-04-01 00:00:00+00:00', '2025-04-15 00:00:00+00:00', '2025-04-29 00:00:00+00:00', 'returned'), -- 14 days, extended and returned
    (27, 'A7890123H', '2025-04-05 00:00:00+00:00', '2025-04-19 00:00:00+00:00', '2025-05-02 00:00:00+00:00', 'returned'), -- 14 days, extended and returned

    -- Extended and still borrowed (mostly 14 days default)
    (28, 'A8901234J', '2025-04-15 00:00:00+00:00', '2025-04-29 00:00:00+00:00', NULL, 'borrowed'),       -- 14 days, extended
    (29, 'A9012345K', '2025-04-20 00:00:00+00:00', '2025-05-20 00:00:00+00:00', NULL, 'borrowed'),       -- 30 days, extended

    -- Extended but overdue (mostly 14 days default)
    (30, 'A0123456L', '2025-04-25 00:00:00+00:00', '2025-05-09 00:00:00+00:00', NULL, 'borrowed');       -- 14 days, extended but overdue

-- Update book copy status to match borrowing records
UPDATE book_copies SET status = 'borrowed' WHERE copy_id IN (
    11, 12, 13, 14, 15,  -- Currently borrowed books (not overdue)
    16, 17, 18,          -- Overdue books (still borrowed)
    24, 25,              -- Severely overdue (still borrowed)
    28, 29, 30           -- Extended books (still borrowed)
);

-- Update book copy status to 'available' for copies that have been returned
UPDATE book_copies SET status = 'available' WHERE copy_id IN (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10,       -- Regular returned books
    19, 20, 21, 22, 23, 26, 27           -- Additional returned books
);

-- Set search path to public schema
SET search_path TO public;
"""

        # Execute the SQL script
        with SessionLocal() as db:
            logger.info("Starting database initialization...")
            db.execute(text(sql_script))
            db.commit()
            logger.info("Database initialization completed successfully!")

        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def reset_database():
    """Complete database reset: clean + initialize"""
    logger.info("=== Starting Complete Database Reset ===")
    
    # Step 1: Clean database
    if clean_database():
        logger.info("✓ Database cleaned successfully")
    else:
        logger.error("✗ Database cleanup failed")
        return False
    
    # Step 2: Initialize database
    if init_db():
        logger.info("✓ Database initialized successfully")
        logger.info("=== Database Reset Complete ===")
        return True
    else:
        logger.error("✗ Database initialization failed")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "clean":
            clean_database()
        elif command == "init":
            init_db()
        elif command == "reset":
            reset_database()
        else:
            print("Usage:")
            print("  python script.py clean  - Clean database only")
            print("  python script.py init   - Initialize database only")
            print("  python script.py reset  - Clean + Initialize (recommended)")
    else:
        # Default: full reset
        reset_database()

