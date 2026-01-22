import logging
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.core import nppes_client, emr_estimator, apollo_client, neverbounce_verifier

settings = get_settings()
logger = logging.getLogger(__name__)

class MLServiceClient:
    """Client for lead generation and enrichment using direct API integrations"""
    
    def __init__(self):
        self.timeout = 120.0  # Increased to 120 seconds for long Apollo searches
        
        # Initialize Apollo client if API key is provided
        self.apollo_finder = None
        if settings.APOLLO_API_KEY:
            self.apollo_finder = apollo_client.ApolloEmailFinder(
                api_key=settings.APOLLO_API_KEY
            )
        
        # Initialize NeverBounce verifier if API key is provided
        self.neverbounce_verifier = None
        if settings.NEVERBOUNCE_API_KEY:
            self.neverbounce_verifier = neverbounce_verifier.get_verifier(
                api_key=settings.NEVERBOUNCE_API_KEY
            )
    
    async def call_scout(
        self,
        city: str,
        specialty: str = "Primary Care",
        count: int = 10,
        exclude_npis: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Call Scout API to generate leads using NPPES and EMR estimation
        
        Args:
            city: Target city for lead generation
            specialty: Medical specialty (default: "Primary Care")
            count: Number of leads to generate
            exclude_npis: List of NPIs to exclude (for duplicate prevention)
        
        Returns:
            Scout API response with leads array
        """
        logger.info(f"Calling Scout (NPPES) for city: {city}, count: {count}")
        
        try:
            # 1. Search NPPES for real providers
            providers = await nppes_client.search_providers(
                city=city,
                specialty=specialty,
                limit=count
            )
            
            if not providers:
                logger.warning(f"No providers found for {city}, {specialty}")
                return {
                    "leads": [],
                    "generation_time_ms": 0,
                    "model": "nppes_direct",
                    "data_source": "nppes_no_results"
                }
            
            # 2. Filter out excluded NPIs if provided
            if exclude_npis:
                providers = [p for p in providers if p.get("npi") not in exclude_npis]
                logger.info(f"Filtered to {len(providers)} providers after excluding {len(exclude_npis)} NPIs")
            
            # 3. Enrich with EMR and clinic size estimates
            leads = []
            for provider in providers:
                state = provider.get('state', '').upper()
                org_name = provider.get('organization_name') or "Individual Practice"
                specialty_val = provider.get('specialty', '')
                
                # Use EMR estimator for baseline
                size_estimate, emr_estimate = emr_estimator.estimate_provider_systems(
                    organization_name=org_name,
                    state=state,
                    specialty=specialty_val
                )
                
                # Use "Private Practice" as default clinic name if no organization data
                clinic_name = org_name if provider.get('organization_name') else "Private Practice"
                
                leads.append({
                    'npi': provider.get('npi'),
                    'name': provider.get('name'),
                    'clinic_name': clinic_name,
                    'address': f"{provider.get('address', '')}, {provider.get('city', '')}, {state} {provider.get('zip', '')}",
                    'city': provider.get('city', ''),
                    'state': state,
                    'phone': provider.get('phone'),
                    'fax': provider.get('fax'),
                    'email': None,  # Will be enriched later by Apollo
                    'website': None,
                    'profile_url': None,
                    'direct_messaging_address': provider.get('direct_messaging_address'),
                    'emr_system': emr_estimate.emr_system,
                    'emr_confidence': emr_estimate.confidence,
                    'emr_source': 'regional_estimate',
                    'clinic_size': size_estimate.clinic_size,
                    'size_confidence': size_estimate.confidence,
                    'data_source': 'nppes_enriched'
                })
            
            logger.info(f"Scout (NPPES) returned {len(leads)} enriched leads")
            
            return {
                "leads": leads,
                "generation_time_ms": 0,  # Not tracking time for direct calls
                "model": "nppes_direct",
                "data_source": "nppes_enriched"
            }
            
        except Exception as e:
            logger.error(f"Scout (NPPES) error: {e}")
            raise Exception(f"Failed to generate leads: {str(e)}")
    
    async def call_apollo(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Call Apollo API to enrich leads with email addresses
        
        Args:
            leads: List of lead objects to enrich
        
        Returns:
            Apollo API response with enriched leads
        """
        if not self.apollo_finder:
            logger.warning("Apollo API key not configured, skipping email enrichment")
            return {
                "leads": leads,
                "emails_found": 0,
                "error": "Apollo API key not configured"
            }
        
        logger.info(f"Calling Apollo API for {len(leads)} leads")
        
        try:
            # Prepare enrichment data
            enrichment_data = []
            
            for lead in leads:
                # Clean name: remove titles and credentials
                name = lead.get("name", "")
                name = name.replace("Dr.", "").replace("Dr ", "")
                name = name.replace("M.D.", "").replace("MD", "").replace(" MD", "")
                name = name.replace("D.O.", "").replace("DO", "").replace(" DO", "")
                name = name.replace("Ph.D.", "").replace("PhD", "")
                name = name.replace(",", "").replace("  ", " ").strip()
                
                name_parts = name.split()
                
                # Extract first and last name
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                last_name = name_parts[-1] if len(name_parts) > 1 else ""
                
                organization = lead.get("clinic_name") or ""
                
                # Don't filter out generic org names - Apollo can still find accurate matches
                if not organization or organization.strip() == "":
                    organization = None
                
                enrichment_data.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "organization_name": organization,
                    "city": lead.get("city"),
                    "state": lead.get("state")
                })
            
            # Enrich with Apollo
            results = await self.apollo_finder.enrich_multiple_people(enrichment_data)
            
            # Merge results back with leads
            enriched_leads = []
            emails_to_verify = {}
            
            for i, lead in enumerate(leads):
                enriched_lead = lead.copy()
                
                if results[i]:
                    apollo_result = results[i]
                    enriched_lead["apollo_email"] = apollo_result.email
                    enriched_lead["apollo_email_status"] = apollo_result.email_status
                    enriched_lead["apollo_confidence"] = apollo_result.confidence
                    enriched_lead["apollo_organization"] = apollo_result.organization
                    enriched_lead["apollo_linkedin"] = apollo_result.linkedin_url
                    enriched_lead["apollo_phone_numbers"] = apollo_result.phone_numbers
                    enriched_lead["apollo_website"] = apollo_result.website_url
                    
                    # Update lead email if not already set
                    if not enriched_lead.get("email") and apollo_result.email:
                        enriched_lead["email"] = apollo_result.email
                    
                    # Collect email for batch verification if enabled
                    if self.neverbounce_verifier and apollo_result.email:
                        emails_to_verify[apollo_result.email] = (i, apollo_result)
                    
                    logger.info(f"✅ Found Apollo email for {lead.get('name')}: {apollo_result.email}")
                else:
                    enriched_lead["apollo_email"] = None
                    logger.debug(f"❌ No Apollo email found for {lead.get('name')}")
                
                enriched_leads.append(enriched_lead)
            
            # Perform batch verification with NeverBounce if emails found
            if self.neverbounce_verifier and emails_to_verify:
                logger.info(f"🔄 Starting batch verification for {len(emails_to_verify)} emails")
                batch_results = await self.neverbounce_verifier.verify_batch(list(emails_to_verify.keys()))
                
                # Merge verification results back
                for email, (idx, apollo_result) in emails_to_verify.items():
                    if email in batch_results:
                        verification = batch_results[email]
                        enriched_leads[idx]["email_verification"] = verification
                        enriched_leads[idx]["email_valid"] = (verification['status'] == 'valid')
                        logger.info(f"   📧 {email}: {verification['status_display']}")
            
            emails_found = sum(1 for l in enriched_leads if l.get('apollo_email'))
            verified_count = sum(1 for l in enriched_leads if l.get('email_valid') is True)
            
            logger.info(f"Apollo API found {emails_found} emails, {verified_count} verified as valid")
            
            return {
                "leads": enriched_leads,
                "emails_found": emails_found,
                "data_source": "apollo.io"
            }
            
        except Exception as e:
            logger.error(f"Apollo API error: {e}")
            # Don't raise - Apollo failure is not critical
            return {
                "leads": leads,
                "emails_found": 0,
                "error": str(e)
            }


# Singleton instance
ml_client = MLServiceClient()
