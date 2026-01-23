from pydantic import BaseModel, EmailStr
from typing import Optional, List

class LeadCreate(BaseModel):
    name: str
    clinic_name: str
    address: str
    city: str
    emr_system: str
    clinic_size: str
    email: EmailStr

class LeadLoadRequest(BaseModel):
    location: str
    specialty: Optional[str] = "Primary Care"

class LeadLoadResponse(BaseModel):
    status: str
    location: str
    specialty: str
    leads_loaded: int
    with_email: int
    without_email: int

class LeadRecruitRequest(BaseModel):
    location: str
    specialty: Optional[str] = "Primary Care"


class LeadRecruitResponse(BaseModel):
    status: str
    location: str
    specialty: str
    enriched_count: int
    returned_count: int
    leads: List[dict]  # List of lead objects


