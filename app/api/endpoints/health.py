from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"  # In a real app, you'd check DB connectivity
    }
