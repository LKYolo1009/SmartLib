from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import api_router
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.core.config import settings
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('app.log')  # Save to file simultaneously
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App is starting...")
    # Check database connection
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1")).fetchone()
        print("Successfully connected to the database")
        db.close()
    except SQLAlchemyError as e:
        print(f"Failed to connect to the database: {e}")

    yield
    print("App is shutting down...")

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Management System",
    description="API for managing NUS Tembusu College Reading Room operations",
    version="1.0.0",
    lifespan=lifespan,
    # Add OpenAPI configuration
    openapi_tags=[
        {"name": "Books", "description": "Operations with books"},
        {"name": "Book Copies", "description": "Operations with book copies"},
        {"name": "Students", "description": "Operations with students"},
        {"name": "Borrowing", "description": "Operations with borrowing records"},
        {"name": "Metadata", "description": "Operations with metadata (authors, publishers, categories, languages)"},
        {"name": "Statistics", "description": "Statistical data and analytics"},
        {"name": "Health", "description": "Health check endpoints"}
    ],
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Don't expand Models by default
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True
    }
)

# Setup CORS  for potential frontend
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include the API router
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Smart Library API"}
import json


# 导出 OpenAPI 规范
openapi_schema = app.openapi()
with open("openapi.json", "w") as f:
    json.dump(openapi_schema, f)