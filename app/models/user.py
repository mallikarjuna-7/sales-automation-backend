from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field, EmailStr

class User(Document):
    email: EmailStr
    full_name: Optional[str] = None
    picture: Optional[str] = None
    last_login: datetime = Field(default_factory=datetime.utcnow)
    last_logout: Optional[datetime] = None
    is_active: bool = True
    
    class Settings:
        name = "user"
        indexes = [
            "email",
            "last_login"
        ]
