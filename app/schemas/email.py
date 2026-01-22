from pydantic import BaseModel, EmailStr
from typing import Optional

class EmailSendRequest(BaseModel):
    sender: str
    receiver: str
    subject: str
    body: str
    lead_id: Optional[str] = None
