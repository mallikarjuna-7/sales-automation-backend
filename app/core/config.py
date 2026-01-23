from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
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
    
    # NeverBounce Settings
    NEVERBOUNCE_API_KEY: str = ""
    
    # Email Settings (Gmail API)
    GMAIL_CLIENT_ID: str
    GMAIL_CLIENT_SECRET: str
    GMAIL_REFRESH_TOKEN: str
    GMAIL_SENDER: str
    MAIL_FROM_NAME: str = "Sales Automation"

@lru_cache()
def get_settings():
    return Settings()

