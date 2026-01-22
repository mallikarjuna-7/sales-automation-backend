from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.lead import Lead
from app.schemas.lead import LeadCreate
from app.services import lead_service

router = APIRouter()

@router.post("/", response_model=List[Lead])
async def create_leads(leads_data: List[LeadCreate]):
    return await lead_service.create_bulk_leads(leads_data)

@router.get("/", response_model=List[Lead])
async def list_leads(
    city: Optional[str] = Query(None),
    emr_system: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    return await lead_service.search_leads(city, emr_system, limit)

@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    lead = await lead_service.get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
