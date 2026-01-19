from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.lead import Lead
from pydantic import BaseModel

router = APIRouter()

class LeadCreate(BaseModel):
    name: str
    clinic_name: str
    address: str
    city: str
    emr_system: str
    clinic_size: str
    email: Optional[str] = None

@router.post("/", response_model=List[Lead])
async def create_leads(leads_data: List[LeadCreate]):
    from app.models.email import Email
    
    saved_leads = []
    for data in leads_data:
        # Check if lead already exists by email
        existing_lead = await Lead.find_one(Lead.email == data.email)
        if existing_lead:
            continue
            
        # Check if we have ever sent an email to this address (History check)
        # This fulfills the request: "if we alreasy sent to the email then we cant store lead"
        existing_email = await Email.find_one(Email.receiver == data.email)
        if existing_email:
            continue
            
        lead = Lead(**data.dict())
        await lead.insert()
        saved_leads.append(lead)
        
    return saved_leads

@router.get("/", response_model=List[Lead])
async def list_leads(
    city: Optional[str] = Query(None),
    emr_system: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    query = {}
    if city:
        query["city"] = city
    if emr_system:
        query["emr_system"] = emr_system
    
    leads = await Lead.find(query).limit(limit).to_list()
    return leads

@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    lead = await Lead.get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
