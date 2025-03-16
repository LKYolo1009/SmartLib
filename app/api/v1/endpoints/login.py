from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["login"])
async def login():
    return {"message": "Login endpoint"} 