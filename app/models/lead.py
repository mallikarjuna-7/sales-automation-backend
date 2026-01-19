from datetime import datetime
from typing import Literal, Optional
from beanie import Document
from pydantic import Field

class Lead(Document):
    name: str
    clinic_name: str
    address: str
    city: str
    emr_system: Literal['Epic', 'Cerner', 'Athena', 'eClinicalWorks', 'Other']
    clinic_size: Literal['Solo', 'Small', 'Medium', 'Large']
    email: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "leads"
        indexes = [
            "city",
            "emr_system",
            "clinic_size",
            "created_at"
        ]
