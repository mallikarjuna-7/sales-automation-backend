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
    
    # Email Settings (Resend)
    RESEND_API_KEY: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str = "Sales Automation"

@lru_cache()
def get_settings():
    return Settings()

