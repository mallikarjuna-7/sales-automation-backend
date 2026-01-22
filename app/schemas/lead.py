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

class LeadRecruitRequest(BaseModel):
    location: str
    specialty: Optional[str] = "Primary Care"
    count: Optional[int] = 10

class LeadRecruitResponse(BaseModel):
    status: str
    location: str
    specialty: str
    total_leads: int
    with_email: int
    without_email: int
    email_coverage_percent: float
    leads: List[dict]  # List of lead objects

