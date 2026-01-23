from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document
from pydantic import Field

class Lead(Document):
    # ===== PRIMARY KEY =====
    npi: str = Field(unique=True, index=True)  # National Provider Identifier (PRIMARY)
    
    # ===== BASIC INFORMATION (from Scout) =====
    name: str
    clinic_name: str
    address: str
    city: str = Field(index=True)
    state: str  # 2-letter state code
    specialty: str = Field(index=True, default="Primary Care")  # Target specialty
    phone: Optional[str] = None
    fax: Optional[str] = None
    
    # ===== EMAIL INFORMATION =====
    email: Optional[str] = Field(default=None, index=True)  # Primary email
    has_email: bool = Field(default=False, index=True)  # Quick filter
    is_emailed: bool = Field(default=False, index=True)  # Campaign tracking
    visited: bool = Field(default=False, index=True)  # Apollo enrichment tracking
    
    # ===== WEBSITE & ONLINE PRESENCE =====

    website: Optional[str] = None
    profile_url: Optional[str] = None  # NPI Registry URL
    direct_messaging_address: Optional[str] = None  # NPPES Direct Messaging
    
    # ===== EMR SYSTEM INFORMATION =====
    emr_system: Optional[str] = None  # e.g., "Epic", "Cerner"
    emr_confidence: Optional[float] = None  # 0-1 confidence score
    emr_source: Optional[str] = None  # "nppes_enriched", "web_detected", "statistical"
    
    # ===== CLINIC SIZE INFORMATION =====
    clinic_size: Optional[str] = None  # e.g., "Medium (5-15 physicians)"
    size_confidence: Optional[float] = None  # 0-1 confidence score
    
    # ===== APOLLO ENRICHMENT DATA =====
    apollo_email: Optional[str] = None
    apollo_email_status: Optional[str] = None  # "verified", "unverified"
    apollo_confidence: Optional[float] = None
    apollo_linkedin: Optional[str] = None
    apollo_phone_numbers: Optional[List[str]] = None
    apollo_organization: Optional[str] = None
    apollo_website: Optional[str] = None
    apollo_searched: bool = Field(default=False)
    
    # ===== EMAIL VERIFICATION (from NeverBounce via Apollo) =====
    email_valid: Optional[bool] = None
    email_verification: Optional[Dict[str, Any]] = None  # Full verification object
    
    # ===== METADATA & TRACKING =====
    data_source: Optional[str] = None  # "nppes_enriched" or "ai_generated"
    enrichment_status: str = Field(default="scout_only")  # "scout_only", "apollo_enriched"
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    last_enriched_at: Optional[datetime] = None
    
    class Settings:
        name = "leads1"
        indexes = [
            "npi",  # Primary unique identifier
            "city",
            "state",
            "specialty",
            "email",
            "has_email",
            "is_emailed",
            "visited",
            "emr_system",
            "clinic_size",
            "enrichment_status",
            "created_at"
        ]
