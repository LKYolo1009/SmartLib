from fastapi import FastAPI
from .api_router import api_router  # Ensure correct import path

app = FastAPI()

app.include_router(api_router)