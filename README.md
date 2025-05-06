#  Smart Library Management System


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

