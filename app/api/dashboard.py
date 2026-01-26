from fastapi import APIRouter, Query
from datetime import date, timedelta
from typing import Optional, List
from app.services.analytics import (
    get_dashboard_stats, 
    get_main_dashboard_stats, 
    get_with_email_stats, 
    get_without_email_stats
)
from app.schemas.analytics import MainDashboardStats, WithEmailStats, WithoutEmailStats

router = APIRouter()

@router.get("/stats")
async def dashboard_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Legacy stats endpoint - still supports date range but no default 7-day filter"""
    stats = await get_dashboard_stats(start_date, end_date)
    return stats


@router.get("/main-stats", response_model=MainDashboardStats)
async def main_dashboard_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Overall summary for the main sales dashboard with optional date filtering"""
    return await get_main_dashboard_stats(start_date, end_date)


@router.get("/with-email-stats", response_model=WithEmailStats)
async def with_email_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """Detailed stats and paginated list for leads that have contact info"""
    return await get_with_email_stats(start_date, end_date, page, page_size)


@router.get("/without-email-stats", response_model=WithoutEmailStats)
async def without_email_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """Stats and paginated list for leads requiring manual research"""
    return await get_without_email_stats(start_date, end_date, page, page_size)

