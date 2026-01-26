from datetime import datetime
from typing import Optional
from beanie import Document, Link
from pydantic import Field
from app.models.lead import Lead

class Email(Document):
    sender: str
    receiver: str
    subject: str = "Sales Automation Outreach"
    body: str
    lead: Optional[Link[Lead]] = None
    status: Optional[str] = "sent"  # "sent", "failed", etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "emails1"
        indexes = [
            "sender",
            "receiver",
            "timestamp"
        ]
