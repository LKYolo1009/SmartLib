from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import api_router
from app.db.session import engine
from app.db.base import Base 
from app.core.config import settings
from starlette.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App is starting...")
    yield
    print("App is shutting down...")
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Library Management System",
    description="API for managing library operations",
    version="1.0.0",
    lifespan=lifespan  #
)

# 设置CORS
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
    return {"message": "Welcom to the Smart Library Api"} 