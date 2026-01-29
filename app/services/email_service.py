from datetime import datetime
from fastapi import HTTPException
from app.core.config import get_settings
from app.models.email import Email
from app.models.lead import Lead
from app.schemas.email import EmailSendRequest
from beanie import PydanticObjectId
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

def get_smtp_config():
    """Get SMTP configuration if credentials are available"""
    if not all([settings.SMTP_USER, settings.SMTP_PASSWORD, settings.MAIL_FROM]):
        return None
    
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )

async def send_outreach_email(email_data: EmailSendRequest):
    """Send email using SMTP with Google App Password"""
    lead = None
    if email_data.lead_id:
        if not PydanticObjectId.is_valid(email_data.lead_id):
            raise HTTPException(status_code=400, detail="Invalid Lead ID format")
            
        lead = await Lead.get(email_data.lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

    # Send email using SMTP
    sent_status = "stored (simulated)"
    email_error = None
    
    # Check if SMTP is configured
    smtp_config = get_smtp_config()
    
    if smtp_config:
        try:
            # Create FastMail instance with config
            fm = FastMail(smtp_config)
            
            # Create email message
            message = MessageSchema(
                subject=email_data.subject,
                recipients=[email_data.receiver],
                body=email_data.body,
                subtype=MessageType.html
            )
            
            # Send the email
            await fm.send_message(message)
            
            sent_status = "sent"
            logger.info(f"Email sent successfully via SMTP to: {email_data.receiver}")
            
        except Exception as e:
            # Log error but don't fail - continue with database operations
            email_error = str(e)
            sent_status = "failed"
            logger.error(f"Email sending failed: {email_error}")
    else:
        logger.warning("SMTP credentials not configured. Email will be stored but not sent.")
        email_error = "SMTP credentials not configured"
    
    # Save email record to database
    email_record = Email(
        sender=email_data.sender,
        receiver=email_data.receiver,
        subject=email_data.subject,
        body=email_data.body,
        lead=lead,
        status=sent_status,
        timestamp=datetime.utcnow()
    )
    
    await email_record.insert()
    
    # Update lead's is_emailed status if lead exists
    if lead:
        lead.is_emailed = True
        await lead.save()
    
    response_data = {
        "status": sent_status,
        "email_id": str(email_record.id),
        "timestamp": email_record.timestamp
    }
    
    if email_error:
        response_data["error"] = email_error
    
    return response_data
