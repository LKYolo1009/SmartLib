from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["分类"])
async def get_categories():
    return {"message": "Category endpoint"} 