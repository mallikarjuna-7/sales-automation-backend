import httpx
from typing import List, Dict, Any, Optional
import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class MLServiceClient:
    """Client for interacting with the ML Lead Generation Service"""
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
        self.timeout = 120.0  # Increased to 120 seconds for long Apollo searches

    
    async def call_scout(
        self,
        city: str,
        specialty: str = "Primary Care",
        count: int = 10,
        exclude_npis: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Call ML Scout API to generate leads
        
        Args:
            city: Target city for lead generation
            specialty: Medical specialty (default: "Primary Care")
            count: Number of leads to generate
            exclude_npis: List of NPIs to exclude (for duplicate prevention)
        
        Returns:
            Scout API response with leads array
        """
        url = f"{self.base_url}/api/scout"
        payload = {
            "city": city,
            "specialty": specialty,
            "count": count,
            "offset": 0
        }
        
        # Add exclude_npis if ML service supports it
        if exclude_npis:
            payload["exclude_npis"] = exclude_npis
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling Scout API for city: {city}, count: {count}")
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Scout API returned {len(data.get('leads', []))} leads")
                return data
        except httpx.HTTPError as e:
            logger.error(f"Scout API error: {e}")
            raise Exception(f"Failed to generate leads: {str(e)}")
    
    async def call_apollo(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Call ML Apollo API to enrich leads with email addresses
        
        Args:
            leads: List of lead objects to enrich
        
        Returns:
            Apollo API response with enriched leads
        """
        url = f"{self.base_url}/api/apollo"
        payload = {"leads": leads}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Calling Apollo API for {len(leads)} leads")
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Apollo API found {data.get('emails_found', 0)} emails")
                return data
        except httpx.HTTPError as e:
            logger.error(f"Apollo API error: {e}")
            # Don't raise - Apollo failure is not critical
            return {"leads": leads, "emails_found": 0, "error": str(e)}


# Singleton instance
ml_client = MLServiceClient()
