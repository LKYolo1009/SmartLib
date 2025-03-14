from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["出版社"])
async def get_publishers():
    return {"message": "Publisher endpoint"} 