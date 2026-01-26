from fastapi import APIRouter, Depends
from app.api import leads, emails, dashboard, health, auth
from app.core.security import get_current_user

api_router = APIRouter()

# Unprotected routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Protected routes (Global Dependency)
api_router.include_router(
    leads.router, 
    prefix="/leads", 
    tags=["leads"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    emails.router, 
    prefix="/emails", 
    tags=["emails"],
    dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    dashboard.router, 
    prefix="/dashboard", 
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)]
)
