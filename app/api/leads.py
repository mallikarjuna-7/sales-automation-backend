from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadLoadRequest, LeadLoadResponse, LeadRecruitRequest, LeadRecruitResponse
from app.services import lead_service

router = APIRouter()

@router.post("/load", response_model=LeadLoadResponse)
async def load_leads(request: LeadLoadRequest):
    """
    Load leads from NPPES API and store in database
    
    - Fetches physician data from NPPES (government database)
    - Uses direct_address as email fallback if email is missing
    - Prevents duplicates using NPI checking
    - Stores leads with visited=false for later Apollo enrichment
    """
    try:
        result = await lead_service.load_leads_from_nppes(
            location=request.location,
            specialty=request.specialty
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead loading failed: {str(e)}")

@router.post("/recruit", response_model=LeadRecruitResponse)
async def recruit_leads(request: LeadRecruitRequest):
    """
    Enrich unvisited leads with Apollo and return top candidates
    
    - Fetches top 10 unvisited leads from database
    - Enriches with Apollo API (email, LinkedIn, phone)
    - Updates database and marks leads as visited=true
    - Returns top 5 leads ready for email campaign
    """
    try:
        result = await lead_service.recruit_leads(
            location=request.location,
            specialty=request.specialty
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead recruitment failed: {str(e)}")

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

