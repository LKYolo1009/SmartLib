from fastapi import FastAPI
from .api_router import api_router  # 确保导入路径正确

app = FastAPI()

app.include_router(api_router)