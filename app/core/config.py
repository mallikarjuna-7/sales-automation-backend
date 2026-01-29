from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
from typing import Optional
import os

# Load .env file into environment variables (local development)
# In production (Render), environment variables are already set
load_dotenv()

class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str
    DB_NAME: str
    PORT: int
    DEBUG: bool
    
    # ML Service Settings
    ML_SERVICE_URL: str
    
    # Apollo.io Settings
    APOLLO_API_KEY: str = ""
    APOLLO_TOTAL_CAP: int = 500  # Total searches allowed
    
    # NeverBounce Settings
    NEVERBOUNCE_API_KEY: str = ""
    
    # Email Settings (SMTP with Google App Password)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None  # Your Gmail address
    SMTP_PASSWORD: Optional[str] = None  # Google App Password
    MAIL_FROM: Optional[str] = None  # Sender email address
    MAIL_FROM_NAME: str = "Sales Automation"
    
    # Auth & JWT Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    JWT_SECRET_KEY: str = "y_fAtC1U8-m8w5yG5-_p8_fAtC1U8-m8w5yG5-_p8" # Default for dev
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALLOWED_DOMAIN: str = "hikigai.ai"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback"
    
    # API URLs & Versions
    NPPES_API_URL: str = "https://npiregistry.cms.hhs.gov/api/"
    NPPES_API_VERSION: str = "2.1"
    
    APOLLO_BASE_URL: str = "https://api.apollo.io/api/v1"
    
    NEVERBOUNCE_BASE_URL: str = "https://api.neverbounce.com/v4"

@lru_cache()
def get_settings():
    return Settings()

