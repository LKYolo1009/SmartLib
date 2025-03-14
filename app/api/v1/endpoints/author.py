from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["作者"])
async def get_authors():
    return {"message": "Author endpoint"} 