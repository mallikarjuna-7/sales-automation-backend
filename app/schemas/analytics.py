from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.models.lead import Lead

class CityStats(BaseModel):
    city: str
    total_leads: int
    with_email: int
    without_email: int
    apollo_enriched_leads: int
    apollo_searched: int
    email_success_rate: float
    total_drafts: int
    sent: int
    failed: int
    last_updated: Optional[Any] = None
    leads_left: int

class MainDashboardStats(BaseModel):
    total_leads: int
    with_email: int
    without_email: int
    apollo_enriched_leads: int
    apollo_searched: int
    email_success_rate: float
    total_drafts: int
    sent: int
    failed: int
    last_updated: Optional[Any] = None
    city_stats: List[CityStats] = []

class PaginatedLeads(BaseModel):
    leads: List[dict]
    total: int
    page: int
    page_size: int
    pages: int

class WithEmailStats(BaseModel):
    total_with_email: int
    drafted: int
    sent: int
    success_rate: float
    leads_data: PaginatedLeads

class WithoutEmailStats(BaseModel):
    total_without_email: int
    with_phone_number: int
    with_address: int
    contactable: float
    leads_data: PaginatedLeads

