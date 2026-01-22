from typing import List, Optional
from datetime import datetime
import logging
from app.models.lead import Lead
from app.models.email import Email
from app.schemas.lead import LeadCreate
from app.services.ml_service import ml_client

logger = logging.getLogger(__name__)

async def recruit_leads(location: str, specialty: str = "Primary Care", count: int = 10):
    """
    Recruit leads for a location using ML Scout and Apollo services
    
    Args:
        location: City name for lead generation
        specialty: Medical specialty (default: "Primary Care")
        count: Number of leads to generate
    
    Returns:
        Dictionary with recruitment results and statistics
    """
    logger.info("="*80)
    logger.info(f"🚀 STARTING LEAD RECRUITMENT")
    logger.info(f"   Location: {location}")
    logger.info(f"   Specialty: {specialty}")
    logger.info(f"   Count: {count}")
    logger.info("="*80)
    
    try:
        # Step 1: Get existing NPIs to avoid duplicates
        logger.info("📊 STEP 1: Checking for existing NPIs in database...")
        try:
            # Simple approach: Just query for NPIs only, no full document validation
            # Use aggregate to get raw NPI values without loading full Lead documents
            pipeline = [
                {"$match": {"city": location}},
                {"$project": {"npi": 1, "_id": 0}},
                {"$match": {"npi": {"$exists": True, "$ne": None}}}
            ]
            
            logger.info(f"   → Querying database for existing NPIs in {location}")
            
            # Use aggregate to bypass document validation - use async for to be safe
            cursor = Lead.aggregate(pipeline)
            existing_npis = []
            async for doc in cursor:
                npi = doc.get("npi")
                if npi:
                    existing_npis.append(npi)
            
            logger.info(f"   ✓ Found {len(existing_npis)} existing NPIs in database")

            if existing_npis:
                logger.info(f"   → Existing NPIs: {existing_npis[:5]}{'...' if len(existing_npis) > 5 else ''}")
        except Exception as e:
            logger.error(f"   ✗ ERROR checking existing NPIs: {str(e)}")
            logger.error(f"   → Error type: {type(e).__name__}")
            # If database check fails, continue with empty list (no duplicates to exclude)
            logger.warning("   ⚠ Continuing with empty NPI list")
            existing_npis = []
        
        # Step 2: Call ML Scout API
        logger.info("")
        logger.info("🔍 STEP 2: Calling ML Scout API...")
        try:
            scout_response = await ml_client.call_scout(
                city=location,
                specialty=specialty,
                count=count,
                exclude_npis=existing_npis
            )
            
            scout_leads = scout_response.get("leads", [])
            logger.info(f"   ✓ Scout API returned {len(scout_leads)} leads")
            
            if not scout_leads:
                logger.warning("   ⚠ Scout API returned no leads - ending recruitment")
                return {
                    "status": "success",
                    "location": location,
                    "specialty": specialty,
                    "total_leads": 0,
                    "with_email": 0,
                    "without_email": 0,
                    "email_coverage_percent": 0.0,
                    "leads": []
                }
        except Exception as e:
            logger.error(f"   ✗ ERROR calling Scout API: {str(e)}")
            logger.error(f"   → Error type: {type(e).__name__}")
            raise Exception(f"Scout API failed: {str(e)}")
        
        # Step 3: Separate leads by email status
        logger.info("")
        logger.info("📧 STEP 3: Separating leads by email status...")
        leads_with_email = []
        leads_without_email = []
        
        for lead in scout_leads:
            if lead.get("email"):
                leads_with_email.append(lead)
            else:
                leads_without_email.append(lead)
        
        logger.info(f"   ✓ Leads WITH email: {len(leads_with_email)}")
        logger.info(f"   ✓ Leads WITHOUT email: {len(leads_without_email)}")
        
        # Step 4: Call Apollo for leads without email
        apollo_enriched = []
        if leads_without_email:
            logger.info("")
            logger.info("🌐 STEP 4: Calling Apollo API for email enrichment...")
            try:
                # Prepare leads for Apollo
                apollo_input = []
                for lead in leads_without_email:
                    apollo_input.append({
                        "name": lead.get("name"),
                        "clinic_name": lead.get("clinic_name"),
                        "address": lead.get("address"),
                        "city": lead.get("city"),
                        "state": lead.get("state"),
                        "npi": lead.get("npi"),
                        # Add required fields for ML service validation
                        "emr_system": lead.get("emr_system"),
                        "clinic_size": lead.get("clinic_size")
                    })
                
                logger.info(f"   → Sending {len(apollo_input)} leads to Apollo")
                apollo_response = await ml_client.call_apollo(apollo_input)
                apollo_enriched = apollo_response.get("leads", [])
                logger.info(f"   ✓ Apollo returned enrichment for {len(apollo_enriched)} leads")
                logger.info(f"   → Emails found: {apollo_response.get('emails_found', 0)}")
            except Exception as e:
                logger.error(f"   ✗ ERROR calling Apollo API: {str(e)}")
                logger.warning("   ⚠ Continuing without Apollo enrichment")
                apollo_enriched = []
        else:
            logger.info("")
            logger.info("⏭️  STEP 4: Skipping Apollo (all leads have emails)")
        
        # Step 5: Merge Scout and Apollo data
        logger.info("")
        logger.info("🔄 STEP 5: Merging Scout and Apollo data...")
        final_leads = []
        
        # Create a lookup dictionary for Apollo data by NPI for faster matching
        apollo_lookup = {}
        if apollo_enriched:
            for apollo_lead in apollo_enriched:
                npi = apollo_lead.get("npi")
                if npi:
                    apollo_lookup[npi] = apollo_lead
            logger.info(f"   → Created Apollo lookup with {len(apollo_lookup)} entries")
        
        # Add leads that already had email from Scout
        for scout_lead in leads_with_email:
            final_leads.append(_prepare_lead_for_db(scout_lead, apollo_data=None))
        
        # Merge Apollo data with Scout data for leads without email
        for scout_lead in leads_without_email:
            # Find matching Apollo data by NPI
            npi = scout_lead.get("npi")
            apollo_data = apollo_lookup.get(npi) if npi else None
            
            if apollo_data:
                logger.info(f"   → Merging Apollo data for NPI {npi}")
            
            final_leads.append(_prepare_lead_for_db(scout_lead, apollo_data))
        
        logger.info(f"   ✓ Prepared {len(final_leads)} leads for database")
        
        # Step 6: Save to database (skip duplicates)
        logger.info("")
        logger.info("💾 STEP 6: Saving leads to database...")
        saved_leads = []
        skipped_count = 0
        
        try:
            for idx, lead_data in enumerate(final_leads):
                try:
                    # Check if NPI already exists
                    existing = await Lead.find_one({"npi": lead_data["npi"]})
                    if existing:
                        logger.info(f"   ⏭️  Skipping duplicate NPI: {lead_data['npi']} ({lead_data.get('name', 'Unknown')})")
                        skipped_count += 1
                        continue
                    
                    # Create and save lead
                    lead = Lead(**lead_data)
                    await lead.insert()
                    saved_leads.append(lead)
                    logger.info(f"   ✓ Saved lead {idx+1}/{len(final_leads)}: {lead.name} (NPI: {lead.npi})")
                except Exception as e:
                    logger.error(f"   ✗ ERROR saving lead {idx+1}: {str(e)}")
                    logger.error(f"   → Lead data: {lead_data.get('name', 'Unknown')} (NPI: {lead_data.get('npi', 'N/A')})")
                    continue
            
            logger.info(f"   ✓ Successfully saved {len(saved_leads)} leads")
            logger.info(f"   ⏭️  Skipped {skipped_count} duplicates")
        except Exception as e:
            logger.error(f"   ✗ ERROR during database save: {str(e)}")
            raise Exception(f"Database save failed: {str(e)}")
        
        # Step 7: Calculate statistics
        logger.info("")
        logger.info("📊 STEP 7: Calculating statistics...")
        with_email_count = sum(1 for lead in saved_leads if lead.has_email)
        without_email_count = len(saved_leads) - with_email_count
        email_coverage = (with_email_count / len(saved_leads) * 100) if saved_leads else 0.0
        
        logger.info(f"   ✓ Total leads saved: {len(saved_leads)}")
        logger.info(f"   ✓ With email: {with_email_count}")
        logger.info(f"   ✓ Without email: {without_email_count}")
        logger.info(f"   ✓ Email coverage: {email_coverage:.2f}%")
        
        logger.info("")
        logger.info("="*80)
        logger.info("✅ LEAD RECRUITMENT COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        
        return {
            "status": "success",
            "location": location,
            "specialty": specialty,
            "total_leads": len(saved_leads),
            "with_email": with_email_count,
            "without_email": without_email_count,
            "email_coverage_percent": round(email_coverage, 2),
            "leads": [lead.model_dump(mode='python', exclude={'id'}) for lead in saved_leads]
        }
    
    except Exception as e:
        logger.error("")
        logger.error("="*80)
        logger.error("❌ LEAD RECRUITMENT FAILED")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"   Type: {type(e).__name__}")
        logger.error("="*80)
        raise



def _prepare_lead_for_db(scout_lead: dict, apollo_data: Optional[dict] = None) -> dict:
    """
    Prepare lead data for database insertion
    Merge Scout (primary) and Apollo (secondary) data
    Rule: If Scout field is empty, use Apollo value
    
    Args:
        scout_lead: Lead data from Scout API
        apollo_data: Optional enrichment data from Apollo API
    
    Returns:
        Dictionary ready for Lead model insertion
    """
    # Start with Scout data (primary source)
    lead_data = {
        "npi": scout_lead.get("npi"),
        "name": scout_lead.get("name"),
        "clinic_name": scout_lead.get("clinic_name"),
        "address": scout_lead.get("address"),
        "city": scout_lead.get("city"),
        "state": scout_lead.get("state"),
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
    }
    
    # Set email from Scout if available
    scout_email = scout_lead.get("email")
    if scout_email:
        lead_data["email"] = scout_email
        lead_data["has_email"] = True
        lead_data["enrichment_status"] = "scout_only"
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

