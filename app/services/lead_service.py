from typing import List
from app.models.lead import Lead
from app.models.email import Email
from app.schemas.lead import LeadCreate

async def create_bulk_leads(leads_data: List[LeadCreate]) -> List[Lead]:
    saved_leads = []
    for data in leads_data:
        # Check if lead already exists by email
        existing_lead = await Lead.find_one(Lead.email == data.email)
        if existing_lead:
            continue
            
        # Check history: if we already sent an email to this address
        existing_email = await Email.find_one(Email.receiver == data.email)
        if existing_email:
            continue
            
        lead = Lead(**data.dict())
        await lead.insert()
        saved_leads.append(lead)
        
    return saved_leads

async def get_lead_by_id(lead_id: str):
    return await Lead.get(lead_id)

async def search_leads(city: str = None, emr_system: str = None, limit: int = 50):
    query = {}
    if city:
        query["city"] = city
    if emr_system:
        query["emr_system"] = emr_system
    
    return await Lead.find(query).limit(limit).to_list()
