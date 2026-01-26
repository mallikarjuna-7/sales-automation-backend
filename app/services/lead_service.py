from typing import List, Optional
from datetime import datetime
import logging
from app.models.lead import Lead
from app.models.email import Email
from app.schemas.lead import LeadCreate
from app.services.ml_service import ml_client
from app.core import nppes_client, emr_estimator

logger = logging.getLogger(__name__)


async def load_leads_from_nppes(location: str, specialty: str = "Primary Care"):
    """
    Load leads from NPPES API and store in database
    
    Args:
        location: City name for lead generation
        specialty: Medical specialty (default: "Primary Care")
    
    Returns:
        Dictionary with load results and statistics
    """
    logger.info("="*80)
    logger.info(f"📥 NPPES LEAD LOADING REQUEST")
    logger.info(f"   Location: {location}")
    logger.info(f"   Specialty: {specialty}")
    logger.info("="*80)
    
    try:
        # Step 1: Call NPPES API directly
        logger.info(f"🔍 Calling NPPES API for {location} | {specialty}...")
        providers = await nppes_client.search_providers(
            city=location,
            specialty=specialty,
            limit=50  # Fetch up to 50 providers
        )
        
        if not providers:
            logger.warning(f"No providers found for {location}, {specialty}")
            return {
                "status": "success",
                "location": location,
                "specialty": specialty,
                "leads_loaded": 0,
                "with_email": 0,
                "without_email": 0
            }
        
        logger.info(f"   ✓ NPPES returned {len(providers)} providers")
        
        # Step 2: Process and store each provider
        leads_loaded = 0
        with_email_count = 0
        without_email_count = 0
        
        for provider in providers:
            npi = provider.get("npi")
            
            # Check for duplicate NPI
            existing = await Lead.find_one({"npi": npi})
            if existing:
                logger.debug(f"   ⊘ Skipping duplicate NPI: {npi}")
                continue
            
            # Email fallback logic
            email = None
            has_email = False
            
            # Priority 1: Use email if available (NPPES doesn't typically have this)
            if provider.get("email"):
                email = provider.get("email")
                has_email = True
                logger.info(f"   ✓ Found email for {provider.get('name')}: {email}")
            # Priority 2: Use direct_address as fallback
            elif provider.get("direct_messaging_address"):
                email = provider.get("direct_messaging_address")
                has_email = True
                logger.info(f"   ✓ Using Direct Address for {provider.get('name')}: {email}")
            else:
                logger.debug(f"   ⊘ No email for {provider.get('name')}")
            
            # Estimate EMR and clinic size
            state = provider.get('state', '').upper()
            org_name = provider.get('organization_name') or "Private Practice"
            
            size_estimate, emr_estimate = emr_estimator.estimate_provider_systems(
                organization_name=org_name,
                state=state,
                specialty=specialty
            )
            
            # Create lead document
            lead_data = {
                "npi": npi,
                "name": provider.get("name"),
                "clinic_name": org_name,
                "address": provider.get("address", ""),
                "city": provider.get("city", location),
                "state": state,
                "specialty": specialty,
                "phone": provider.get("phone"),
                "fax": provider.get("fax"),
                "email": email,
                "has_email": has_email,
                "website": None,
                "profile_url": None,
                "direct_messaging_address": provider.get("direct_messaging_address"),
                "emr_system": emr_estimate.emr_system,
                "emr_confidence": emr_estimate.confidence,
                "emr_source": "regional_estimate",
                "clinic_size": size_estimate.clinic_size,
                "size_confidence": size_estimate.confidence,
                "data_source": "nppes_enriched",
                "enrichment_status": "scout_only",
                "visited": False,  # Not yet sent to Apollo
                "is_emailed": False,  # Not yet emailed
                "created_at": datetime.utcnow()
            }
            
            # Insert into database
            lead = Lead(**lead_data)
            await lead.insert()
            
            leads_loaded += 1
            if has_email:
                with_email_count += 1
            else:
                without_email_count += 1
        
        logger.info("="*80)
        logger.info(f"✅ NPPES LOADING COMPLETE")
        logger.info(f"   Total Loaded: {leads_loaded}")
        logger.info(f"   With Email: {with_email_count}")
        logger.info(f"   Without Email: {without_email_count}")
        logger.info("="*80)
        
        return {
            "status": "success",
            "location": location,
            "specialty": specialty,
            "leads_loaded": leads_loaded,
            "with_email": with_email_count,
            "without_email": without_email_count
        }
    
    except Exception as e:
        logger.error(f"❌ NPPES LOADING FAILED: {str(e)}")
        raise Exception(f"Lead loading failed: {str(e)}")



async def recruit_leads(location: str, specialty: str = "Primary Care"):
    """
    Recruit leads by enriching unvisited leads with Apollo API
    
    Args:
        location: City name for lead recruitment
        specialty: Medical specialty (default: "Primary Care")
    
    Returns:
        Dictionary with recruitment results and top 5 leads ready for email
    """
    logger.info("="*80)
    logger.info(f"🎯 LEAD RECRUITMENT REQUEST")
    logger.info(f"   Location: {location}")
    logger.info(f"   Specialty: {specialty}")
    logger.info("="*80)
    
    try:
        # Step 1: Fetch top 10 unvisited leads
        logger.info(f"📊 STEP 1: Fetching top 10 unvisited leads for {location} | {specialty}...")
        unvisited_leads = await Lead.find({
            "city": location,
            "specialty": specialty,
            "visited": False
        }).limit(10).to_list()
        
        if not unvisited_leads:
            logger.warning(f"⚠️ No unvisited leads found for {location} | {specialty}")
            logger.info("   Tip: Call POST /api/leads/load first to fetch leads from NPPES")
            
            # Still return top 5 ready leads if they exist
            ready_leads = await Lead.find({
                "city": location,
                "specialty": specialty,
                "has_email": True,
                "is_emailed": False
            }).limit(5).to_list()
            
            return {
                "status": "success",
                "location": location,
                "specialty": specialty,
                "enriched_count": 0,
                "returned_count": len(ready_leads),
                "leads": [
                    {
                        **lead.model_dump(mode="python", exclude={"id"}),
                        "id": str(lead.id)
                    }
                    for lead in ready_leads
                ]
            }
        
        logger.info(f"   ✓ Found {len(unvisited_leads)} unvisited leads")
        
        # Step 2: Prepare leads for Apollo enrichment
        logger.info("🌐 STEP 2: Preparing leads for Apollo enrichment...")
        apollo_input = []
        for lead in unvisited_leads:
            # Parse name to extract first and last name
            name = lead.name.replace("Dr.", "").replace("Dr ", "")
            name = name.replace("M.D.", "").replace("MD", "").replace(" MD", "")
            name = name.replace("D.O.", "").replace("DO", "").replace(" DO", "")
            name = name.replace(",", "").replace("  ", " ").strip()
            
            name_parts = name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            
            apollo_input.append({
                "name": lead.name,
                "first_name": first_name,
                "last_name": last_name,
                "clinic_name": lead.clinic_name,
                "address": lead.address,
                "city": lead.city,
                "state": lead.state,
                "npi": lead.npi,
                "emr_system": lead.emr_system,
                "clinic_size": lead.clinic_size
            })
        
        # Step 3: Call Apollo API
        logger.info(f"🔍 STEP 3: Calling Apollo API for {len(apollo_input)} leads...")
        apollo_response = await ml_client.call_apollo(apollo_input)
        apollo_enriched = apollo_response.get("leads", [])
        
        logger.info(f"   ✓ Apollo returned enrichment data for {len(apollo_enriched)} leads")
        
        # Step 4: Update database with Apollo data
        logger.info("💾 STEP 4: Updating database with Apollo enrichment...")
        enriched_count = 0
        
        for i, lead in enumerate(unvisited_leads):
            apollo_data = apollo_enriched[i] if i < len(apollo_enriched) else {}
            
            update_fields = {
                "visited": True,  # Mark as visited
                "apollo_searched": True,  # Mark that we searched Apollo for this lead
                "last_enriched_at": datetime.utcnow()
            }
            
            # Add Apollo data if available
            if apollo_data.get("apollo_email"):
                update_fields["apollo_email"] = apollo_data.get("apollo_email")
                update_fields["apollo_email_status"] = apollo_data.get("apollo_email_status")
                update_fields["apollo_confidence"] = apollo_data.get("apollo_confidence")
                update_fields["apollo_linkedin"] = apollo_data.get("apollo_linkedin")
                update_fields["apollo_phone_numbers"] = apollo_data.get("apollo_phone_numbers")
                update_fields["apollo_organization"] = apollo_data.get("apollo_organization")
                update_fields["apollo_website"] = apollo_data.get("apollo_website")
                update_fields["email_valid"] = apollo_data.get("email_valid")
                update_fields["email_verification"] = apollo_data.get("email_verification")
                update_fields["enrichment_status"] = "apollo_enriched"
                
                # If lead didn't have email but Apollo found one, update primary email
                if not lead.email and apollo_data.get("apollo_email"):
                    update_fields["email"] = apollo_data.get("apollo_email")
                    update_fields["has_email"] = True
                    logger.info(f"   ✓ Assigned Apollo email to {lead.name}: {apollo_data.get('apollo_email')}")
                
                enriched_count += 1
            
            # Update the lead in database
            await Lead.find_one({"npi": lead.npi}).update({"$set": update_fields})
        
        logger.info(f"   ✓ Updated {enriched_count} leads with Apollo data")
        
        # Step 5: Fetch top 5 leads ready for email
        logger.info("📝 STEP 5: Fetching top 5 leads ready for email campaign...")
        ready_leads = await Lead.find({
            "city": location,
            "specialty": specialty,
            "has_email": True,
            "is_emailed": False
        }).limit(5).to_list()
        
        logger.info(f"   ✓ Found {len(ready_leads)} leads ready for campaign")
        
        logger.info("="*80)
        logger.info("✅ LEAD RECRUITMENT FLOW COMPLETE")
        logger.info(f"   Enriched: {enriched_count} leads")
        logger.info(f"   Returned: {len(ready_leads)} leads")
        logger.info("="*80)
        
        return {
            "status": "success",
            "location": location,
            "specialty": specialty,
            "enriched_count": enriched_count,
            "returned_count": len(ready_leads),
            "leads": [
                {
                    **lead.model_dump(mode="python", exclude={"id"}),
                    "id": str(lead.id)
                }
                for lead in ready_leads
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ LEAD RECRUITMENT FAILED: {str(e)}")
        raise Exception(f"Lead recruitment failed: {str(e)}")






def _prepare_lead_for_db(scout_lead: dict, apollo_data: Optional[dict] = None, specialty: str = "Primary Care") -> dict:
    """Merge Scout and Apollo data into single dictionary for database"""
    # Base data from Scout
    lead_data = {
        "npi": scout_lead.get("npi"),
        "name": scout_lead.get("name"),
        "clinic_name": scout_lead.get("clinic_name"),
        "address": scout_lead.get("address"),
        "city": scout_lead.get("city"),
        "state": scout_lead.get("state"),
        "specialty": specialty,  # Added specialty
        "phone": scout_lead.get("phone"),
        "fax": scout_lead.get("fax"),
        "website": scout_lead.get("website"),
        "profile_url": scout_lead.get("profile_url"),
        "direct_messaging_address": scout_lead.get("direct_messaging_address"),
        "emr_system": scout_lead.get("emr_system"),
        "emr_confidence": scout_lead.get("emr_confidence"),
        "emr_source": scout_lead.get("emr_source"),
        "clinic_size": scout_lead.get("clinic_size"),
        "size_confidence": scout_lead.get("size_confidence"),
        "data_source": scout_lead.get("data_source"),
        "created_at": datetime.utcnow(),
        "is_emailed": False,  # Default to False
    }
    
    # Set email from Scout if available
    scout_email = scout_lead.get("email")
    direct_email = scout_lead.get("direct_messaging_address")
    
    if scout_email:
        lead_data["email"] = scout_email
        lead_data["has_email"] = True
        lead_data["enrichment_status"] = "scout_only"
    elif direct_email:
        lead_data["email"] = direct_email
        lead_data["has_email"] = True
        lead_data["enrichment_status"] = "scout_only"
        logger.info(f"      ✓ Using Direct Messaging Address as fallback: {direct_email}")
    else:
        lead_data["email"] = None
        lead_data["has_email"] = False
        lead_data["enrichment_status"] = "scout_only"
    
    # Merge Apollo data if available
    if apollo_data:
        apollo_email = apollo_data.get("apollo_email")
        
        # If Scout didn't have email but Apollo found one, use it
        if not scout_email and apollo_email:
            lead_data["email"] = apollo_email
            lead_data["has_email"] = True
            logger.info(f"      ✓ Assigned Apollo email for {lead_data.get('name')}: {apollo_email}")

        
        # Add Apollo-specific fields
        lead_data["apollo_email"] = apollo_email
        lead_data["apollo_email_status"] = apollo_data.get("apollo_email_status")
        lead_data["apollo_confidence"] = apollo_data.get("apollo_confidence")
        lead_data["apollo_linkedin"] = apollo_data.get("apollo_linkedin")
        lead_data["apollo_phone_numbers"] = apollo_data.get("apollo_phone_numbers")
        lead_data["apollo_organization"] = apollo_data.get("apollo_organization")
        lead_data["apollo_website"] = apollo_data.get("apollo_website")
        lead_data["apollo_searched"] = True
        lead_data["email_valid"] = apollo_data.get("email_valid")
        lead_data["email_verification"] = apollo_data.get("email_verification")
        lead_data["enrichment_status"] = "apollo_enriched"
        lead_data["last_enriched_at"] = datetime.utcnow()
        
        # Fill empty Scout fields with Apollo data (if available)
        if not lead_data["phone"] and apollo_data.get("apollo_phone_numbers"):
            lead_data["phone"] = apollo_data["apollo_phone_numbers"][0]
        
        if not lead_data["website"] and apollo_data.get("apollo_website"):
            lead_data["website"] = apollo_data["apollo_website"]
    
    return lead_data


async def create_bulk_leads(leads_data: List[LeadCreate]) -> List[Lead]:
    saved_leads = []
    for data in leads_data:
        # Check if lead already exists by email
        existing_lead = await Lead.find_one(Lead.email == data.email)
        if existing_lead:
            continue
            
        # Check history: if we already sent an email to this address
        existing_email = await Email.find_one(Email.receiver == data.email)
        if existing_email:
            continue
            
        lead = Lead(**data.dict())
        await lead.insert()
        saved_leads.append(lead)
        
    return saved_leads

async def get_lead_by_id(lead_id: str):
    return await Lead.get(lead_id)

async def search_leads(city: str = None, emr_system: str = None, limit: int = 50):
    query = {}
    if city:
        query["city"] = city
    if emr_system:
        query["emr_system"] = emr_system
    
    return await Lead.find(query).limit(limit).to_list()

