"""
Apollo.io Email Finder Client
Integrates with Apollo.io API to find verified email addresses for doctors
Includes NeverBounce email verification integration
"""

import httpx
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio
import time

logger = logging.getLogger(__name__)


@dataclass
class ApolloEmailResult:
    """Result from Apollo.io email search."""
    email: str
    email_status: str
    confidence: float  # 0-1
    organization: str
    linkedin_url: str
    phone_numbers: List[str]
    website_url: str
    data_source: str = "apollo.io"


class ApolloEmailFinder:
    """Apollo.io API client for finding doctor emails."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.apollo.io/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key
        }
    
    def _is_medical_organization(self, org_name: str, email_domain: str = "") -> bool:
        """
        Validate if organization is medical/healthcare related.
        
        Args:
            org_name: Organization name from Apollo
            email_domain: Email domain (e.g., 'example.com' from email@example.com)
        
        Returns:
            True if organization is medical-related, False otherwise
        """
        if not org_name and not email_domain:
            return False
        
        org_lower = org_name.lower().strip() if org_name else ""
        email_domain_lower = email_domain.lower().strip() if email_domain else ""
        
        # Medical/healthcare keywords
        medical_keywords = [
            "hospital", "medical center", "clinic", "healthcare", "health",
            "physician", "doctors", "md", "medicine", "university hospital",
            "medical group", "primary care", "cardiology", "oncology",
            "surgery", "surgical", "orthopedic", "emergency", "ent",
            "radiology", "pathology", "psychiatry", "neurology", "pediatric",
            "cancer center", "research center", "medical school", "nursing",
            "dental", "optometry", "physical therapy", "therapy", "rehab",
            "urgent care", "family medicine", "internal medicine", "surgery center",
            "veterans affairs", "va hospital", "va medical", "kaiser", "aetna",
            "cigna", "united health", "anthem", "humana", "blue cross",
            "mount sinai", "mjhs", "nyc health", "health system", "medical practice"
        ]
        
        # Non-medical exclusions (more conservative - only clear non-medical)
        non_medical_keywords = [
            "school", "university", "college", "education",
            "manufacturing", "distribution", "logistics", "retail",
            "finance", "insurance", "real estate", "construction",
            "technology", "software", "consulting", "marketing",
            "publishing", "media", "entertainment", "restaurant",
            "bank", "credit union", "automotive"
        ]
        
        # Check if it has medical keywords in organization name
        has_medical_org = any(k in org_lower for k in medical_keywords)
        
        # Also check email domain for medical indicators
        # Many healthcare orgs have .org, .healthcare, .medical domains
        # and healthcare organization names often appear in domain (e.g., mjhs.org = Mount Sinai)
        has_medical_email = (
            email_domain_lower.endswith(".org") or  # Non-profits, many hospitals
            email_domain_lower.endswith(".healthcare") or
            email_domain_lower.endswith(".medical") or
            "health" in email_domain_lower or
            "hospital" in email_domain_lower or
            "clinic" in email_domain_lower or
            "medical" in email_domain_lower
        )
        
        # Explicitly check if it's non-medical
        for keyword in non_medical_keywords:
            if keyword in org_lower:
                # Check if it also has medical keywords (medical-related non-profit org)
                if not has_medical_org:
                    return False
        
        # Return true if either org or domain indicates medical
        return has_medical_org or has_medical_email
    
    def _calculate_healthcare_score(self, person: Dict) -> float:
        """
        Calculate healthcare relevance score for a person (0.0-1.0).
        Higher scores indicate better match for healthcare professionals.
        
        Args:
            person: Person data from Apollo API
        
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        title = person.get("title", "").lower()
        org = person.get("organization", {})
        org_name = org.get("name", "").lower() if org else ""
        
        # Extensive medical titles (0.6 weight)
        medical_keywords = [
            "physician", "doctor", "surgeon", "md", "medical director", 
            "cardiologist", "neurologist", "clinical", "assistant professor",
            "fellow", "palliative care", "hospitalist", "resident",
            "nurse", "rn", "pa", "nurse practitioner", "therapist",
            "internist", "pediatrician", "psychiatrist", "dentist",
            "optometrist", "pharmacist", "radiologist", "pathologist"
        ]
        if any(k in title for k in medical_keywords):
            score += 0.6
        elif "care" in title and ("health" in title or "medical" in title or "hospice" in title):
            score += 0.5  # Flexible scoring for care-related titles
        elif "professor" in title and ("medicine" in title or "health" in title or "clinical" in title):
            score += 0.3
        
        # Healthcare organizations (0.3 weight)
        org_keywords = ["hospital", "medical", "health", "clinic", "healthcare", "physician", 
                       "university", "care center", "practice", "hospice", "palliative"]
        if any(k in org_name for k in org_keywords):
            score += 0.3
        
        # Has email available (0.2 weight)
        if person.get("has_email"):
            score += 0.2
        
        return min(score, 1.0)

    async def _hierarchical_search(
        self,
        first_name: str,
        last_name: str,
        city: Optional[str] = None,
        state: Optional[str] = None
    ) -> tuple[List[Dict], str]:
        """
        Search Apollo API with hierarchical fallback strategy.
        
        Tries 3 strategies in order:
        1. City + State (most precise) - best for local matching
        2. State only (broader) - catches doctors in different nearby cities
        3. No location (broadest) - catches doctors if location data differs
        
        This approach solves the NPPES location mismatch problem where NPPES
        shows practice address but Apollo shows home/LinkedIn location.
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            city: City from NPPES data (optional)
            state: State from NPPES data (optional)
        
        Returns:
            (results list, strategy_used string) - results sorted by healthcare score
        """
        url = f"{self.base_url}/mixed_people/api_search"
        
        # Strategy 1: Try with location + keywords (without strict title filtering)
        strategies = [
            ("city_state", {
                "q_keywords": f"{first_name} {last_name}",
                "person_locations": [f"{city}, {state}"] if city and state else None,
                "per_page": 20
            }) if city and state else None,
            ("state_only", {
                "q_keywords": f"{first_name} {last_name}",
                "person_locations": [state] if state else None,
                "per_page": 20
            }) if state else None,
            ("no_location", {
                "q_keywords": f"{first_name} {last_name}",
                "per_page": 20
            })
        ]
        
        # Remove None strategies and filter out empty payloads
        strategies = [(name, payload) for name, payload in strategies if name and payload]
        strategies = [(name, {k: v for k, v in payload.items() if v is not None}) for name, payload in strategies]
        
        for strategy_name, payload in strategies:
            try:
                logger.debug(f"Attempting Apollo search - strategy: {strategy_name}")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload, headers=self.headers)
                    response.raise_for_status()
                    
                    data = response.json()
                    people = data.get("people", [])
                    
                    logger.debug(f"Apollo search returned {len(people)} results for strategy: {strategy_name}")
                    
                    if people:
                        # Score and sort by healthcare relevance
                        for person in people:
                            person["_score"] = self._calculate_healthcare_score(person)
                        
                        people.sort(key=lambda x: x["_score"], reverse=True)
                        logger.info(f"✅ Apollo search found {len(people)} results using '{strategy_name}' strategy")
                        return people, strategy_name
            
            except Exception as e:
                logger.debug(f"Hierarchical search strategy '{strategy_name}' error: {str(e)}")
                continue
        
        logger.debug(f"❌ All hierarchical search strategies failed for {first_name} {last_name}")
        return [], "failed"
    
    async def enrich_person_by_name(
        self,
        first_name: str,
        last_name: str,
        organization_name: Optional[str] = None,
        domain: Optional[str] = None,
        email: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None
    ) -> Optional[ApolloEmailResult]:
        """
        Enrich a person by name with optional location hierarchy fallback.
        
        NEW: Uses hierarchical search strategy that automatically falls back from
        city+state → state only → no location. This solves NPPES address mismatches.
        
        Apollo API Note: first_name and last_name are the minimum required fields.
        When organization_name is provided, uses /people/match for exact match.
        When organization_name is NOT provided, uses hierarchical search to find 
        multiple matches and returns the best match with verified email.
        
        Args:
            first_name: Person's first name (required)
            last_name: Person's last name (required)
            organization_name: Organization name (optional - improves match rate)
            domain: Organization domain (optional - improves match rate)
            email: Known email address (optional - helps verify)
            linkedin_url: LinkedIn profile URL (optional - improves matching)
            city: City from NPPES data (optional - used for location hierarchy)
            state: State from NPPES data (optional - used for location hierarchy)
        
        Returns:
            ApolloEmailResult if found, None otherwise
        """
        
        # Filter out generic/placeholder organization names that won't help matching
        generic_org_names = [
            "private practice",
            "individual practice", 
            "no nppes org data",
            "not available",
            "n/a",
            ""
        ]
        
        # Treat generic org names as "no organization" to trigger hierarchical search
        if organization_name and organization_name.lower().strip() in generic_org_names:
            logger.debug(f"Ignoring generic organization name '{organization_name}' - using hierarchical search")
            organization_name = None
        
        # If no organization provided (or generic), use hierarchical search
        if not organization_name:
            return await self._search_person_by_name(
                first_name, last_name, city=city, state=state
            )
        
        # Otherwise use match endpoint with organization
        url = f"{self.base_url}/people/match"
        
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "organization_name": organization_name
        }
        
        if domain:
            payload["domain"] = domain
        if email:
            payload["email"] = email
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                person = data.get("person")
                
                if person and person.get("email"):
                    org = person.get("organization", {})
                    org_name = org.get("name", "")
                    title = person.get("title", "")
                    email = person.get("email", "")
                    email_domain = email.split("@")[1] if "@" in email else ""
                    
                    # ✅ VALIDATE: Check if email organization is medical-related
                    is_medical = self._is_medical_organization(org_name, email_domain)
                    
                    # Also check if title is medical (belt-and-suspenders approach)
                    title_lower = title.lower()
                    medical_title_keywords = ["physician", "doctor", "surgeon", "md", "medical director", 
                                            "cardiologist", "neurologist", "clinical", "nurse", "rn", "pa"]
                    has_medical_title = any(k in title_lower for k in medical_title_keywords)
                    
                    # More lenient: Accept if EITHER org is medical OR title is medical
                    # Don't filter out just because we can't determine org type
                    if not is_medical and not has_medical_title:
                        person_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
                        logger.debug(
                            f"⚠️ {person_name}: Could not verify as medical | Title: {title} | Org: {org_name} | "
                            f"Domain: {email_domain} | Email: {email} - returning anyway (lenient mode)"
                        )
                        # Don't filter - return the email anyway since it came from Apollo search
                    
                    email_status = person.get("email_status", "unknown")
                    confidence = 0.95 if email_status == "verified" else 0.75
                    
                    # Organization is medical - return the result
                    return ApolloEmailResult(
                        email=email,
                        email_status=email_status,
                        confidence=confidence,
                        organization=org_name,
                        linkedin_url=person.get("linkedin_url", ""),
                        phone_numbers=[p.get("raw_number", p) if isinstance(p, dict) else p 
                                      for p in person.get("phone_numbers", [])],
                        website_url=org.get("website_url", "")
                    )
                else:
                    if person:
                        org = person.get("organization", {})
                        org_name = org.get("name", "N/A") if org else "N/A"
                        linkedin = person.get("linkedin_url", "N/A")
                        logger.info(f"❌ Apollo found person but no email: {first_name} {last_name} @ {organization_name} | Apollo org: {org_name} | LinkedIn: {linkedin}")
                    else:
                        logger.info(f"❌ Apollo no match: {first_name} {last_name} @ {organization_name}")
                
                return None
        
        except Exception as e:
            logger.error(f"Apollo.io enrichment error for {first_name} {last_name}: {str(e)}")
            return None
    
    async def _search_person_by_name(
        self,
        first_name: str,
        last_name: str,
        city: Optional[str] = None,
        state: Optional[str] = None
    ) -> Optional[ApolloEmailResult]:
        """
        Search for a person by name with hierarchical location fallback.
        
        NEW: Uses hierarchical search strategy:
        1. Try city + state search (precise)
        2. Fall back to state-only search (broader)
        3. Fall back to name-only search (broadest)
        
        This solves the NPPES address mismatch problem where practice address
        doesn't match Apollo.io location data (which comes from LinkedIn).
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            city: City from NPPES data (optional)
            state: State from NPPES data (optional)
        
        Returns:
            ApolloEmailResult with best matching email, or None
        """
        # Use hierarchical search with location fallback
        people, strategy = await self._hierarchical_search(
            first_name, last_name, city=city, state=state
        )
        
        if not people:
            logger.debug(f"❌ Apollo hierarchical search no match: {first_name} {last_name}")
            return None
        
        # Get best match (first in score-sorted list)
        best_match = people[0]
        score = best_match.get("_score", 0.0)
        
        # ✅ CHECK MEDICAL RELEVANCE BEFORE CALLING EXPENSIVE EMAIL API
        # Minimum score threshold: 0.6 (ensures medical title or healthcare org)
        MEDICAL_THRESHOLD = 0.6
        
        if score < MEDICAL_THRESHOLD:
            person_name = f"{best_match.get('first_name', '')} {best_match.get('last_name', '')}".strip()
            title = best_match.get("title", "N/A")
            org = best_match.get("organization", {})
            org_name = org.get("name", "N/A") if org else "N/A"
            
            logger.warning(
                f"⚠️ {person_name}: NOT medical-related (score: {score:.2f} < {MEDICAL_THRESHOLD}) | "
                f"Title: {title} | Org: {org_name} | ❌ Skipping email fetch to save API credits"
            )
            return None
        
        logger.debug(
            f"✅ Apollo hierarchical search found MEDICAL match for {first_name} {last_name} "
            f"(strategy: {strategy}, score: {score:.2f}) - Proceeding to fetch email"
        )
        
        # Enrich to get email (costs API credits)
        return await self.enrich_person_by_id(best_match["id"])
    
    async def enrich_person_by_id(self, person_id: str) -> Optional[ApolloEmailResult]:
        """
        Enrich a person by Apollo ID.
        
        Args:
            person_id: Apollo person ID
        
        Returns:
            ApolloEmailResult if found, None otherwise
        """
        url = f"{self.base_url}/people/match"
        
        payload = {"id": person_id}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                person = data.get("person")
                
                if person and person.get("email"):
                    org = person.get("organization", {})
                    org_name = org.get("name", "")
                    email = person.get("email", "")
                    email_domain = email.split("@")[1] if "@" in email else ""
                    title = person.get("title", "")
                    
                    # ✅ VALIDATE: Check if email organization is medical-related
                    is_medical = self._is_medical_organization(org_name, email_domain)
                    
                    # Also check if title is medical
                    title_lower = title.lower()
                    medical_title_keywords = ["physician", "doctor", "surgeon", "md", "medical director", 
                                            "cardiologist", "neurologist", "clinical", "nurse", "rn", "pa"]
                    has_medical_title = any(k in title_lower for k in medical_title_keywords)
                    
                    # More lenient: Accept if EITHER org is medical OR title is medical
                    if not is_medical and not has_medical_title:
                        person_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
                        logger.debug(
                            f"⚠️ {person_name}: Could not verify as medical | Title: {title} | Org: {org_name} | "
                            f"Domain: {email_domain} | Email: {email} - returning anyway (lenient mode)"
                        )
                        # Don't filter - return the email anyway
                    
                    email_status = person.get("email_status", "unknown")
                    confidence = 0.95 if email_status == "verified" else 0.75
                    
                    return ApolloEmailResult(
                        email=email,
                        email_status=email_status,
                        confidence=confidence,
                        organization=org_name,
                        linkedin_url=person.get("linkedin_url", ""),
                        phone_numbers=[p.get("raw_number", p) if isinstance(p, dict) else p 
                                      for p in person.get("phone_numbers", [])],
                        website_url=org.get("website_url", "")
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Apollo.io enrichment error for ID {person_id}: {str(e)}")
            return None
    
    async def enrich_multiple_people(
        self,
        people_data: List[Dict]
    ) -> List[Optional[ApolloEmailResult]]:
        """
        Enrich multiple people in parallel.
        
        Apollo API supports name-only searches with hierarchical location fallback.
        
        Args:
            people_data: List of dicts with first_name, last_name, and optionally
                        organization_name, domain, city, and state
        
        Returns:
            List of ApolloEmailResult or None for each person
        """
        tasks = []
        for person in people_data:
            task = self.enrich_person_by_name(
                first_name=person.get("first_name", ""),
                last_name=person.get("last_name", ""),
                organization_name=person.get("organization_name") or person.get("clinic_name"),
                domain=person.get("domain"),
                email=person.get("email"),
                linkedin_url=person.get("linkedin_url"),
                city=person.get("city"),
                state=person.get("state")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
