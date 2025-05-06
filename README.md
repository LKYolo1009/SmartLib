# SmartLib - Smart Library Management System

SmartLib is a modern library management system that provides API services for book management, user management, and borrowing management.

## Tech Stack

- Python 3.13
- FastAPI
- PostgreSQL

## Quick Start

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the service:
```bash
uvicorn app.main:app --reload
```

The service will start at http://localhost:8000

## API Documentation

After starting the service, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Main API Endpoints

### User Management
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user information
- `PUT /api/v1/users/{user_id}` - Update user information
- `DELETE /api/v1/users/{user_id}` - Delete user

### Book Management
- `POST /api/v1/books/` - Add a new book
- `GET /api/v1/books/` - Get book list
- `GET /api/v1/books/{book_id}` - Get book details
- `PUT /api/v1/books/{book_id}` - Update book information
- `DELETE /api/v1/books/{book_id}` - Delete book

### Borrowing Management
- `POST /api/v1/borrows/` - Create a borrowing record
- `GET /api/v1/borrows/{borrow_id}` - Get borrowing details
- `PUT /api/v1/borrows/{borrow_id}/return` - Return a book

## Environment Variables

Create a `.env` file and configure the following environment variables:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/smartlib
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Project Structure

```
app/
├── api/          # API routes
├── core/         # Core configurations
├── crud/         # Database operations
├── db/           # Database configurations
├── models/       # Data models
├── schemas/      # Pydantic models
└── service/      # Business logic
```

## Development Team

- [Your Name] - Project Lead

## License

MIT License
