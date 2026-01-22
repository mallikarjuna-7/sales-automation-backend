from fastapi import APIRouter
from app.models.lead import Lead

router = APIRouter()

@router.get("/")
async def health_check():
    # Verify DB connectivity
    lead_count = await Lead.count()
    return {
        "status": "healthy",
        "database": "connected",
        "total_leads_in_db": lead_count
    }
