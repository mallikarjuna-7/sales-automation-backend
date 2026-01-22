import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import init_db
from app.api.router import api_router
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Sales Automation API",
    description="Backend for Sales Automation with FastAPI and MongoDB",
    version="0.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Sales Automation API...")
    await init_db()
    logger.info("Database initialized successfully")

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Sales Automation API is running"}

