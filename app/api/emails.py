from fastapi import APIRouter
from app.schemas.email import EmailSendRequest
from app.services import email_service
from app.models.email import Email
from typing import List

router = APIRouter()

@router.post("/send")
async def send_email(email_data: EmailSendRequest):
    return await email_service.send_outreach_email(email_data)

@router.get("/", response_model=List[Email])
async def list_emails(limit: int = 10):
    return await Email.find_all().sort("-timestamp").limit(limit).to_list()
