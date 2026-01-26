from datetime import datetime
from fastapi import HTTPException
from app.core.config import get_settings
from app.models.email import Email
from app.models.lead import Lead
from app.schemas.email import EmailSendRequest
from beanie import PydanticObjectId
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

settings = get_settings()

def get_gmail_service():
    """Create and return Gmail API service with OAuth2 credentials"""
    creds = Credentials(
        token=None,
        refresh_token=settings.GMAIL_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GMAIL_CLIENT_ID,
        client_secret=settings.GMAIL_CLIENT_SECRET
    )
    
    # Refresh the token if needed
    if not creds.valid:
        creds.refresh(Request())
    
    service = build('gmail', 'v1', credentials=creds)
    return service

def create_message(sender, to, subject, body):
    """Create a MIME message for Gmail API"""
    message = MIMEText(body, 'html')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Encode the message in base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

async def send_outreach_email(email_data: EmailSendRequest):
    lead = None
    if email_data.lead_id:
        if not PydanticObjectId.is_valid(email_data.lead_id):
            raise HTTPException(status_code=400, detail="Invalid Lead ID format")
            
        lead = await Lead.get(email_data.lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

    # Send email using Gmail API
    sent_status = "stored (simulated)"
    email_error = None
    
    if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET and settings.GMAIL_REFRESH_TOKEN:
        try:
            # Get Gmail service
            service = get_gmail_service()
            
            # Create the email message
            sender_email = f"{settings.MAIL_FROM_NAME} <{settings.GMAIL_SENDER}>"
            message = create_message(
                sender=sender_email,
                to=email_data.receiver,
                subject=email_data.subject,
                body=f"<p>{email_data.body}</p>"
            )
            
            # Send the email
            response = service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            sent_status = "sent"
            print(f"Email sent successfully via Gmail API: {response.get('id')}")
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
