"""
NPPES API Client - Real-time physician data lookup.
Queries the official CMS National Provider Identifier Registry.
"""

import asyncio
import logging
from typing import List, Optional
import httpx

# Configure logging
logger = logging.getLogger(__name__)


NPPES_API_URL = "https://npiregistry.cms.hhs.gov/api/"
NPPES_API_VERSION = "2.1"

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
    limit: int = 5
) -> List[dict]:
    """
    Search for healthcare providers in the NPPES registry.
    
    Args:
        city: City name to search in
        state: Optional state abbreviation (e.g., 'NY', 'CA'). If not provided, will guess.
        specialty: Medical specialty to search for
        limit: Maximum number of results to return
        
    Returns:
        List of provider dictionaries with keys:
        - npi: National Provider Identifier
        - name: Full name with title
        - address: Full street address
        - city: City name
        - state: State abbreviation
        - zip: ZIP code
        - phone: Practice phone number (if available)
        - fax: Fax number (if available)
        - specialty: Taxonomy description
        - organization_name: Practice/organization name (if available)
    """
    # If no state provided, try to guess from city
    if not state:
        state = guess_state_from_city(city)
    
    # Map specialty to taxonomy description
    taxonomy = map_specialty_to_taxonomy(specialty)
    
    # Build query parameters
    params = {
        "version": NPPES_API_VERSION,
        "city": city,
        "enumeration_type": "NPI-1",  # Individual providers only
        "taxonomy_description": taxonomy,
        "limit": min(limit * 2, 50),  # Request extra in case some are filtered
    }
    
    if state:
        params["state"] = state
    
    providers = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(NPPES_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            
            for result in results[:limit]:
                # Extract basic info
                basic = result.get("basic", {})
                
                # Get first name and last name
                first_name = basic.get("first_name", "").title()
                last_name = basic.get("last_name", "").title()
                credential = basic.get("credential", "MD")
                
                if not first_name or not last_name:
                    continue
                
                # Build full name with title
                name = f"Dr. {first_name} {last_name}"
                if credential:
                    name += f", {credential}"
                
                # Get practice address (prefer location over mailing)
                addresses = result.get("addresses", [])
                practice_address = None
                for addr in addresses:
                    if addr.get("address_purpose") == "LOCATION":
                        practice_address = addr
                        break
                if not practice_address and addresses:
                    practice_address = addresses[0]
                
                if not practice_address:
                    continue
                
                # Get organization name - try multiple sources
                org_name = basic.get("organization_name", "")
                
                # If NPPES has organization name, use it
                if org_name:
                    logger.debug(f"Using NPPES organization name: {org_name}")
                else:
                    # Try to extract from practice location address line 2
                    # BUT: Filter out suite/floor numbers (not real organizations)
                    address_2 = practice_address.get("address_2", "")
                    if address_2:
                        # Check if it's just a suite/floor number (not a real org)
                        address_2_lower = address_2.lower().strip()
                        is_suite_number = any([
                            address_2_lower.startswith("suite"),
                            address_2_lower.startswith("ste "),
                            address_2_lower.startswith("ste."),
                            address_2_lower.startswith("#"),
                            address_2_lower.startswith("floor"),
                            address_2_lower.startswith("fl "),
                            address_2_lower.startswith("unit"),
                            address_2_lower.startswith("apt"),
                            address_2_lower.startswith("bldg"),
                            address_2_lower.startswith("building"),
                        ])
                        
                        if not is_suite_number and len(address_2) > 5:
                            # Looks like a real organization name, not just suite number
                            org_name = address_2
                            logger.debug(f"Using address_2 as organization: {org_name}")
                        else:
                            # It's just a suite number, ignore it
                            org_name = None
                            logger.debug(f"Skipping address_2 (suite/unit): {address_2}")
                    else:
                        org_name = None
                        logger.debug(f"No organization data available for {last_name}")
                
                # Extract phone and fax from practice address
                phone = practice_address.get("telephone_number", "")
                fax = practice_address.get("fax_number", "")
                
                # Extract Direct Messaging Address from endpoints
                direct_messaging_address = None
                endpoints = result.get("endpoints", [])
                if endpoints:
                    for endpoint in endpoints:
                        # NPPES API uses camelCase: endpointType (not endpoint_type)
                        # and the value is "DIRECT" (uppercase)
                        endpoint_type = endpoint.get("endpointType", "").upper()
                        # Look for Direct Messaging Address endpoint
                        if endpoint_type == "DIRECT":
                            direct_messaging_address = endpoint.get("endpoint")
                            if direct_messaging_address:
                                logger.info(f"✅ Found Direct Messaging Address: {direct_messaging_address}")
                                break
                
                # Format phone number if present (remove non-digits, add dashes)
                if phone:
                    phone_digits = ''.join(filter(str.isdigit, phone))
                    if len(phone_digits) == 10:
                        phone = f"{phone_digits[:3]}-{phone_digits[3:6]}-{phone_digits[6:]}"
                    elif len(phone_digits) == 11 and phone_digits[0] == '1':
                        phone = f"{phone_digits[1:4]}-{phone_digits[4:7]}-{phone_digits[7:]}"
                
                if fax:
                    fax_digits = ''.join(filter(str.isdigit, fax))
                    if len(fax_digits) == 10:
                        fax = f"{fax_digits[:3]}-{fax_digits[3:6]}-{fax_digits[6:]}"
                    elif len(fax_digits) == 11 and fax_digits[0] == '1':
                        fax = f"{fax_digits[1:4]}-{fax_digits[4:7]}-{fax_digits[7:]}"
                
                # Build provider data - only include real organization if found
                provider = {
                    "npi": result.get("number"),
                    "name": name,
                    "address": practice_address.get("address_1", ""),
                    "city": practice_address.get("city", city).title(),
                    "state": practice_address.get("state", state or ""),
                    "zip": practice_address.get("postal_code", "")[:5],
                    "phone": phone or None,
                    "fax": fax or None,
                    "specialty": taxonomy,
                    "organization_name": org_name,  # None if no real organization found
                    "direct_messaging_address": direct_messaging_address,  # Direct Messaging Address if available
                }
                
                providers.append(provider)
            
    except httpx.HTTPError as e:
        logger.error(f"NPPES API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error querying NPPES: {e}")
        return []
    
    return providers


async def lookup_provider_by_npi(npi: str) -> Optional[dict]:
    """
    Look up a specific provider by their NPI number.
    
    Args:
        npi: 10-digit National Provider Identifier
        
    Returns:
        Provider dictionary or None if not found
    """
    params = {
        "version": NPPES_API_VERSION,
        "number": npi,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(NPPES_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception as e:
        logger.error(f"Error looking up NPI {npi}: {e}")
    
    return None
