from fastapi import APIRouter, Query
from datetime import date, timedelta
from typing import Optional
from app.services.analytics import get_dashboard_stats

router = APIRouter()

@router.get("/stats")
async def dashboard_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    today = date.today()
    
    # If dates aren't provided, default to the last 7 days
    if not start_date:
        start_date = today - timedelta(days=7)
    if not end_date:
        end_date = today
        
    stats = await get_dashboard_stats(start_date, end_date)
    return stats
