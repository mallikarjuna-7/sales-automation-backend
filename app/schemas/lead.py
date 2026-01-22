from pydantic import BaseModel, EmailStr
from typing import Optional

class LeadCreate(BaseModel):
    name: str
    clinic_name: str
    address: str
    city: str
    emr_system: str
    clinic_size: str
    email: EmailStr
