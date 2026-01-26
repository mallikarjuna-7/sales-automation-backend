"""
NPPES API Client - Real-time physician data lookup.
Queries the official CMS National Provider Identifier Registry.
"""

import asyncio
import logging
from typing import List, Optional
import httpx

from app.core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

settings = get_settings()

# Mapping of common specialty names to NPI taxonomy descriptions
SPECIALTY_TAXONOMY_MAP = {
    "Primary Care": "Internal Medicine",
    "Family Medicine": "Family Medicine",
    "Cardiology": "Cardiovascular Disease",
    "Dermatology": "Dermatology",
    "Orthopedics": "Orthopaedic Surgery",
    "Pediatrics": "Pediatrics",
    "Neurology": "Neurology",
    "Oncology": "Medical Oncology",
    "Psychiatry": "Psychiatry",
    "Gastroenterology": "Gastroenterology",
    "Pulmonology": "Pulmonary Disease",
    "Endocrinology": "Endocrinology, Diabetes & Metabolism",
    "Rheumatology": "Rheumatology",
    "Nephrology": "Nephrology",
    "Urology": "Urology",
}

# US state abbreviations for city-to-state guessing
MAJOR_CITIES_STATE_MAP = {
    "new york": "NY",
    "los angeles": "CA",
    "chicago": "IL",
    "houston": "TX",
    "phoenix": "AZ",
    "philadelphia": "PA",
    "san antonio": "TX",
    "san diego": "CA",
    "dallas": "TX",
    "san jose": "CA",
    "austin": "TX",
    "jacksonville": "FL",
    "fort worth": "TX",
    "columbus": "OH",
    "charlotte": "NC",
    "san francisco": "CA",
    "indianapolis": "IN",
    "seattle": "WA",
    "denver": "CO",
    "boston": "MA",
    "nashville": "TN",
    "detroit": "MI",
    "novi": "MI",
    "ann arbor": "MI",
    "grand rapids": "MI",
    "portland": "OR",
    "las vegas": "NV",
    "miami": "FL",
    "atlanta": "GA",
    "baltimore": "MD",
    "minneapolis": "MN",
    "cleveland": "OH",
    "pittsburgh": "PA",
    "orlando": "FL",
    "tampa": "FL",
    "phoenix": "AZ",
    "milwaukee": "WI",
}


def guess_state_from_city(city: str) -> Optional[str]:
    """Attempt to guess state abbreviation from city name."""
    city_lower = city.lower().strip()
    return MAJOR_CITIES_STATE_MAP.get(city_lower)


def map_specialty_to_taxonomy(specialty: str) -> str:
    """Map common specialty names to NPI taxonomy descriptions."""
    return SPECIALTY_TAXONOMY_MAP.get(specialty, specialty)


async def search_providers(
    city: str,
    state: Optional[str] = None,
    specialty: str = "Internal Medicine",
    limit: int = 1200
) -> List[dict]:
    """
    Search for healthcare providers in the NPPES registry with pagination support.
    
    Args:
        city: City name to search in
        state: Optional state abbreviation
        specialty: Medical specialty to search for
        limit: Maximum number of results to return (capped at 1200 by NPPES API)
        
    Returns:
        List of provider dictionaries.
    """
    # NPPES hard limit is ~1200 via skip pagination
    max_limit = min(limit, 1200)
    
    if not state:
        state = guess_state_from_city(city)
    
    taxonomy = map_specialty_to_taxonomy(specialty)
    
    providers = []
    skip = 0
    batch_size = 200 # NPPES max per request
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            while len(providers) < max_limit and skip <= 1000:
                # Always request a full batch of 200 to be efficient
                # and to avoid complicated skip calculation
                params = {
                    "version": settings.NPPES_API_VERSION,
                    "city": city,
                    "enumeration_type": "NPI-1",
                    "taxonomy_description": taxonomy,
                    "limit": batch_size,
                    "skip": skip
                }
                
                if state:
                    params["state"] = state
                
                logger.info(f"🌐 NPPES Batch: skip={skip}, requested={batch_size}")
                response = await client.get(settings.NPPES_API_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                if not results:
                    break 
                
                for result in results:
                    provider = _extract_provider_data(result, city, state, taxonomy)
                    if provider:
                        providers.append(provider)
                        # Stop immediately if we hit the user's requested limit
                        if len(providers) >= max_limit:
                            break
                
                # If we got fewer than 200, it means the registry is exhausted
                if len(results) < batch_size:
                    break
                    
                skip += batch_size
                    
    except httpx.HTTPError as e:
        logger.error(f"NPPES API error: {e}")
    except Exception as e:
        logger.error(f"Error querying NPPES: {e}")
    
    return providers[:max_limit]


def _extract_provider_data(result: dict, city: str, state: Optional[str], taxonomy: str) -> Optional[dict]:
    """Helper to extract and format provider data from NPPES JSON result"""
    basic = result.get("basic", {})
    first_name = basic.get("first_name", "").title()
    last_name = basic.get("last_name", "").title()
    credential = basic.get("credential", "MD")
    
    if not first_name or not last_name:
        return None
    
    name = f"Dr. {first_name} {last_name}"
    if credential:
        name += f", {credential}"
    
    addresses = result.get("addresses", [])
    practice_address = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), None)
    if not practice_address and addresses:
        practice_address = addresses[0]
    
    if not practice_address:
        return None
        
    org_name = basic.get("organization_name", "")
    if not org_name:
        address_2 = practice_address.get("address_2", "")
        if address_2:
            address_2_lower = address_2.lower().strip()
            is_suite = any(address_2_lower.startswith(s) for s in ["suite", "ste", "#", "floor", "fl ", "unit", "apt", "bldg", "building"])
            if not is_suite and len(address_2) > 5:
                org_name = address_2
                
    phone = practice_address.get("telephone_number", "")
    fax = practice_address.get("fax_number", "")
    
    direct_messaging_address = None
    for ep in result.get("endpoints", []):
        if ep.get("endpointType", "").upper() == "DIRECT":
            direct_messaging_address = ep.get("endpoint")
            break

    # Phone formatting
    if phone:
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) == 10: phone = f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1': phone = f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    
    return {
        "npi": result.get("number"),
        "name": name,
        "address": practice_address.get("address_1", ""),
        "city": practice_address.get("city", city).title(),
        "state": practice_address.get("state", state or ""),
        "zip": practice_address.get("postal_code", "")[:5],
        "phone": phone or None,
        "fax": fax or None,
        "specialty": taxonomy,
        "organization_name": org_name or None,
        "direct_messaging_address": direct_messaging_address,
    }

async def lookup_provider_by_npi(npi: str) -> Optional[dict]:
    """
    Look up a specific provider by their NPI number.
    
    Args:
        npi: 10-digit National Provider Identifier
        
    Returns:
        Provider dictionary or None if not found
    """
    params = {
        "version": settings.NPPES_API_VERSION,
        "number": npi,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.NPPES_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception as e:
        logger.error(f"Error looking up NPI {npi}: {e}")
    
    return None
