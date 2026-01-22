from datetime import datetime
from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import get_settings
from app.models.email import Email
from app.models.lead import Lead
from app.schemas.email import EmailSendRequest
from beanie import PydanticObjectId

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_outreach_email(email_data: EmailSendRequest):
    lead = None
    if email_data.lead_id:
        if not PydanticObjectId.is_valid(email_data.lead_id):
            raise HTTPException(status_code=400, detail="Invalid Lead ID format")
            
        lead = await Lead.get(email_data.lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

    # Send actual email if SMTP is configured
    sent_status = "stored (simulated)"
    if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
        message = MessageSchema(
            subject=email_data.subject,
            recipients=[email_data.receiver],
            body=email_data.body,
            subtype=MessageType.plain
        )
        fm = FastMail(conf)
        try:
            await fm.send_message(message)
            sent_status = "sent"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Email failed to send: {str(e)}")
    
    email_record = Email(
        sender=email_data.sender,
        receiver=email_data.receiver,
        subject=email_data.subject,
        body=email_data.body,
        lead=lead,
        timestamp=datetime.utcnow()
    )
    
    await email_record.insert()
    
    # Update lead's is_emailed status if lead exists
    if lead:
        lead.is_emailed = True
        await lead.save()
    
    return {
        "status": sent_status,
        "email_id": str(email_record.id),
        "timestamp": email_record.timestamp
    }
