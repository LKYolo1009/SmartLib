from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["登录"])
async def login():
    return {"message": "Login endpoint"} 