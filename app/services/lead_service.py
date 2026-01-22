from typing import List, Optional
from datetime import datetime
import logging
from app.models.lead import Lead
from app.models.email import Email
from app.schemas.lead import LeadCreate
from app.services.ml_service import ml_client

logger = logging.getLogger(__name__)

async def recruit_leads(location: str, specialty: str = "Primary Care"):
    """
    Recruit leads for a location using ML Scout and Apollo services
    
    Args:
        location: City name for lead generation
        specialty: Medical specialty (default: "Primary Care")
    
    Returns:
        Dictionary with recruitment results and statistics
    """
    logger.info("="*80)
    logger.info(f"🚀 LEAD RECRUITMENT REQUEST")
    logger.info(f"   Location: {location}")
    logger.info(f"   Specialty: {specialty}")
    logger.info("="*80)
    
    try:
        # Step 1: Check total records in database for this city/specialty
        logger.info(f"📊 STEP 1: Checking total records for {location} | {specialty}...")
        total_count = await Lead.find({"city": location, "specialty": specialty}).count()
        logger.info(f"   → Total records in DB: {total_count}")
        
        # Step 2: Trigger recruitment ONLY if total records == 0
        if total_count == 0:
            logger.info("🔍 No records found. Triggering AI Recruitment flow...")
            
            # 2.1: Get existing NPIs from other locations (to avoid global duplicates)
            logger.info("   → Checking for global NPI duplicates...")
            # Using distinct is the most efficient and stable way to get all NPIs in Beanie
            existing_npis = await Lead.distinct("npi")
            logger.info(f"   → Found {len(existing_npis)} existing NPIs to exclude.")
            
            # 2.2: Call ML Scout API
            logger.info("🔍 Calling ML Scout API...")
            scout_response = await ml_client.call_scout(
                city=location,
                specialty=specialty,
                count=10,  # Default to 10 for first recruitment
                exclude_npis=existing_npis
            )
            
            scout_leads = scout_response.get("leads", [])
            logger.info(f"   ✓ Scout API returned {len(scout_leads)} leads")
            
            if scout_leads:
                # 2.3: Separate leads by email status
                leads_with_email = []
                leads_without_email = []
                for lead in scout_leads:
                    if lead.get("email"):
                        leads_with_email.append(lead)
                    else:
                        leads_without_email.append(lead)
                
                # 2.4: Call Apollo for email enrichment
                apollo_enriched = []
                if leads_without_email:
                    logger.info("🌐 Calling Apollo API for email enrichment...")
                    apollo_input = []
                    for lead in leads_without_email:
                        apollo_input.append({
                            "name": lead.get("name"),
                            "clinic_name": lead.get("clinic_name"),
                            "address": lead.get("address"),
                            "city": lead.get("city"),
                            "state": lead.get("state"),
                            "npi": lead.get("npi"),
                            "emr_system": lead.get("emr_system"),
                            "clinic_size": lead.get("clinic_size")
                        })
                    apollo_response = await ml_client.call_apollo(apollo_input)
                    apollo_enriched = apollo_response.get("leads", [])
                
                # 2.5: Merge and Save
                apollo_lookup = {lead["npi"]: lead for lead in apollo_enriched if lead.get("npi")}
                final_leads = []
                
                # Prepare with email leads
                for scout_lead in leads_with_email:
                    final_leads.append(_prepare_lead_for_db(scout_lead, None, specialty))
                
                # Prepare without email leads (merging Apollo)
                for scout_lead in leads_without_email:
                    npi = scout_lead.get("npi")
                    apollo_data = apollo_lookup.get(npi)
                    final_leads.append(_prepare_lead_for_db(scout_lead, apollo_data, specialty))
                
                # Save to database
                for lead_data in final_leads:
                    # Final safety check for duplicate NPI
                    existing = await Lead.find_one({"npi": lead_data["npi"]})
                    if not existing:
                        lead = Lead(**lead_data)
                        await lead.insert()
            
            logger.info("💾 Recruitment and save complete.")
        else:
            logger.info("✅ Records exist. Skipping AI Recruitment (using Cache).")
        
        # Step 3: Fetch top 5 valid leads to return
        # Constraints: city=location, specialty=specialty, has_email=True, is_emailed=False
        logger.info("📝 Fetching top 5 leads (has email & not yet emailed)...")
        results = await Lead.find({
            "city": location,
            "specialty": specialty,
            "has_email": True,
            "is_emailed": False
        }).limit(5).to_list()
        
        with_email_count = len(results)
        logger.info(f"   ✓ Found {with_email_count} leads ready for campaign")
        
        logger.info("="*80)
        logger.info("✅ LEAD RECRUITMENT FLOW COMPLETE")
        logger.info("="*80)
        
        return {
            "status": "success",
            "location": location,
            "specialty": specialty,
            "total_leads": with_email_count,
            "with_email": with_email_count,
            "without_email": 0,
            "email_coverage_percent": 100.0 if with_email_count > 0 else 0.0,
            "leads": [
    {
        **lead.model_dump(mode="python", exclude={"id"}),
        "id": str(lead.id)
    }
    for lead in results
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

