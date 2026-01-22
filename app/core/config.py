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
    
    # SMTP Settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool

@lru_cache()
def get_settings():
    return Settings()

