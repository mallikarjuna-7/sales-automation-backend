from datetime import datetime
from fastapi import HTTPException
from app.core.config import get_settings
from app.models.email import Email
from app.models.lead import Lead
from app.schemas.email import EmailSendRequest
from beanie import PydanticObjectId
import resend

settings = get_settings()
resend.api_key = settings.RESEND_API_KEY

async def send_outreach_email(email_data: EmailSendRequest):
    lead = None
    if email_data.lead_id:
        if not PydanticObjectId.is_valid(email_data.lead_id):
            raise HTTPException(status_code=400, detail="Invalid Lead ID format")
            
        lead = await Lead.get(email_data.lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

    # Send email using Resend API
    sent_status = "stored (simulated)"
    email_error = None
    
    if settings.RESEND_API_KEY:
        params = {
            "from": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>",
            "to": [email_data.receiver],
            "subject": email_data.subject,
            "html": f"<p>{email_data.body}</p>",
        }
        
        try:
            response = resend.Emails.send(params)
            sent_status = "sent"
            print(f"Email sent successfully via Resend: {response}")
        except Exception as e:
            # Log error but don't fail - continue with database operations
            email_error = str(e)
            sent_status = "failed"
            print(f"Email sending failed: {email_error}")
    
    # Save email record to database
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
    
    response_data = {
        "status": sent_status,
        "email_id": str(email_record.id),
        "timestamp": email_record.timestamp
    }
    
    if email_error:
        response_data["error"] = email_error
    
    return response_data
