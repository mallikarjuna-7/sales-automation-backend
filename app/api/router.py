from fastapi import APIRouter
from app.api.endpoints import leads, emails, dashboard, health

api_router = APIRouter()

api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
