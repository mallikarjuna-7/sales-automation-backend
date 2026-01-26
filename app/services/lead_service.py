from typing import List, Optional
from datetime import datetime
import logging
from app.models.lead import Lead
from app.models.email import Email
from app.schemas.lead import LeadCreate
from app.services.ml_service import ml_client
from app.core import nppes_client, emr_estimator

logger = logging.getLogger(__name__)


async def load_leads_from_nppes(location: str, specialty: str = "Primary Care", limit: int = 1000):
    """
    Load leads from NPPES API and store in database using high-performance bulk processing.
    
    Args:
        location: City name for lead generation
        specialty: Medical specialty (default: "Primary Care")
        limit: Max leads to fetch (Max 1200)
    
    Returns:
        Dictionary with load results and statistics
    """
    logger.info("="*80)
    logger.info(f"📥 NPPES BULK LEAD LOADING")
    logger.info(f"   Location: {location} | Specialty: {specialty} | Limit: {limit}")
    logger.info("="*80)
    
    try:
        # Step 1: Call NPPES API with pagination support
        providers = await nppes_client.search_providers(
            city=location,
            specialty=specialty,
            limit=limit
        )
        
        if not providers:
            return {
                "status": "success",
                "location": location,
                "specialty": specialty,
                "leads_loaded": 0,
                "with_email": 0,
                "without_email": 0
            }
        
        logger.info(f"🔍 Processing {len(providers)} providers from NPPES...")
        
        # Step 2: Optimized Duplicate Check (Bulk)
        # Fetch all NPIs in one trip to compare in memory (Global check across all cities)
        new_npis = [p.get("npi") for p in providers if p.get("npi")]
        existing_leads = await Lead.find({"npi": {"$in": new_npis}}).to_list()
        existing_npis = {l.npi for l in existing_leads}
        
        leads_to_create = []
        with_email_count = 0
        
        # Step 3: Map data and prepare for bulk insert
        for provider in providers:
            npi = provider.get("npi")
            if not npi or npi in existing_npis:
                continue
            
            # Email Priority Logic
            email = provider.get("email") or provider.get("direct_messaging_address")
            has_email = bool(email)
            
            # regional estimates for EMR/Size
            state = provider.get('state', '').upper()
            org_name = provider.get('organization_name') or "Private Practice"
            size_est, emr_est = emr_estimator.estimate_provider_systems(org_name, state, specialty)
            
            lead_data = {
                "npi": npi,
                "name": provider.get("name"),
                "clinic_name": org_name,
                "address": provider.get("address", ""),
                "city": provider.get("city", location).title(),
                "state": state,
                "specialty": specialty,
                "phone": provider.get("phone"),
                "fax": provider.get("fax"),
                "email": email,
                "has_email": has_email,
                "direct_messaging_address": provider.get("direct_messaging_address"),
                "emr_system": emr_est.emr_system,
                "emr_confidence": emr_est.confidence,
                "emr_source": "regional_estimate",
                "clinic_size": size_est.clinic_size,
                "size_confidence": size_est.confidence,
                "data_source": "nppes_enriched",
                "enrichment_status": "scout_only",
                "visited": False,
                "is_emailed": False,
                "created_at": datetime.utcnow()
            }
            
            leads_to_create.append(Lead(**lead_data))
            if has_email:
                with_email_count += 1
        
        # Step 4: Perform Bulk Insert (Atomic Trip)
        inserted_count = 0
        if leads_to_create:
            # Use Beanie/Motor insert_many for high performance
            # Setting ordered=False allows valid inserts to proceed even if one fails
            result = await Lead.get_pymongo_collection().insert_many(
                [l.model_dump(by_alias=True, exclude={"id"}) for l in leads_to_create],
                ordered=False
            )
            inserted_count = len(result.inserted_ids)
            logger.info(f"✅ Bulk Insert Successful: {inserted_count} new leads created.")
        else:
            logger.info("ℹ️ No new leads found (all entries were duplicates).")

        return {
            "status": "success",
            "location": location,
            "specialty": specialty,
            "leads_loaded": inserted_count,
            "with_email": with_email_count if inserted_count > 0 else 0,
            "without_email": (inserted_count - with_email_count) if inserted_count > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"❌ BULK LOADING FAILED: {str(e)}")
        raise e



async def recruit_leads(location: str, specialty: str = "Primary Care"):
    """
    Recruit leads with Apollo credit protection:
    1. Only enrich leads WITHOUT an email.
    2. Respect 500 total search cap.
    3. Always mark processed leads as visited.
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    logger.info("="*80)
    logger.info(f"🎯 CREDIT-SAFE LEAD RECRUITMENT")
    logger.info(f"   Location: {location} | Specialty: {specialty}")
    logger.info("="*80)
    
    try:
        # Step 1: Credit Usage Check
        total_searched = await Lead.find({"apollo_searched": True}).count()
        remaining_credits = max(0, settings.APOLLO_TOTAL_CAP - total_searched)
        logger.info(f"📊 Credit Status: {total_searched}/{settings.APOLLO_TOTAL_CAP} used | {remaining_credits} remaining")

        # Step 2: Smart Batch Fetching
        # Goal: Get 10 unvisited leads, prioritizing those that already HAVE emails (SAVE CREDITS)
        
        # 1. First, get leads that have a free email already
        free_leads = await Lead.find({
            "city": location,
            "specialty": specialty,
            "visited": False,
            "has_email": True,
            "is_emailed": False
        }).limit(10).to_list()
        
        # 2. If we need more to reach 10, get leads that need enrichment
        needed_count = 10 - len(free_leads)
        to_enrich_leads = []
        if needed_count > 0:
            to_enrich_leads = await Lead.find({
                "city": location,
                "specialty": specialty,
                "visited": False,
                "has_email": False
            }).limit(needed_count).to_list()
            
        unvisited_leads = free_leads + to_enrich_leads
        
        if not unvisited_leads:
            logger.warning(f"⚠️ No unvisited leads found for {location}")
            ready_leads = await Lead.find({
                "city": location,
                "specialty": specialty,
                "has_email": True,
                "is_emailed": False
            }).limit(10).to_list()
            
            return {
                "status": "success", "location": location, "specialty": specialty,
                "enriched_count": 0, "returned_count": len(ready_leads),
                "remaining_credits": remaining_credits,
                "leads": [{**l.model_dump(mode="python", exclude={"id"}), "id": str(l.id)} for l in ready_leads]
            }

        # Step 3: Identify leads needing enrichment (NO email)
        leads_needing_enrichment = [l for l in unvisited_leads if not l.has_email]
        leads_with_existing_email = [l for l in unvisited_leads if l.has_email]
        
        logger.info(f"🔍 Selective Enrichment: {len(leads_needing_enrichment)} need search | {len(leads_with_existing_email)} already have email")

        enriched_count = 0
        if remaining_credits > 0 and leads_needing_enrichment:
            # We ONLY enrich what we have credits for
            target_leads = leads_needing_enrichment[:remaining_credits]
            
            logger.info(f"🌐 Calling Apollo for {len(target_leads)} leads needing emails...")
            # CRITICAL: Convert Lead objects to dicts! 
            # Otherwise, lead.get() calls the Document.get class method (coroutine).
            apollo_input = [l.model_dump(mode="python") for l in target_leads]
            apollo_response = await ml_client.call_apollo(apollo_input)
            apollo_results = apollo_response.get("leads", [])

            # Update database for enriched leads
            for i, lead in enumerate(target_leads):
                res = apollo_results[i] if i < len(apollo_results) else {}
                update = {
                    "visited": True, 
                    "apollo_searched": True, 
                    "last_enriched_at": datetime.utcnow()
                }
                
                # Only update if Apollo actually found a NEW email
                if res.get("apollo_email"):
                    update.update({
                        "email": res.get("apollo_email"),
                        "has_email": True,
                        "apollo_email": res.get("apollo_email"),
                        "enrichment_status": "apollo_enriched",
                        "apollo_linkedin": res.get("apollo_linkedin"),
                        "apollo_phone_numbers": res.get("apollo_phone_numbers"),
                        "apollo_organization": res.get("apollo_organization"),
                        "apollo_website": res.get("apollo_website")
                    })
                    enriched_count += 1
                
                await Lead.find_one({"npi": lead.npi}).update({"$set": update})
            
            # Update unvisited_leads list status for the ones we didn't search but marked as visited
            # (Handled by the universal update below anyway)
            
        # Step 4: Final Universal Update (Mark all top 10 as visited)
        processed_npis = [l.npi for l in unvisited_leads]
        await Lead.get_pymongo_collection().update_many(
            {"npi": {"$in": processed_npis}},
            {"$set": {"visited": True}}
        )
        
        # Recalculate usage for response
        final_usage = await Lead.find({"apollo_searched": True}).count()
        final_remaining = max(0, settings.APOLLO_TOTAL_CAP - final_usage)

        # Step 5: Fetch results to return
        ready_leads = await Lead.find({
            "city": location, "specialty": specialty,
            "has_email": True, "is_emailed": False
        }).limit(10).to_list()
        
        logger.info(f"✅ RECRUITMENT COMPLETE | Enriched: {enriched_count} | Ready: {len(ready_leads)} | Remaining Credits: {final_remaining}")
        
        return {
            "status": "success", "location": location, "specialty": specialty,
            "enriched_count": enriched_count, "returned_count": len(ready_leads),
            "remaining_credits": final_remaining,
            "leads": [{**l.model_dump(mode="python", exclude={"id"}), "id": str(l.id)} for l in ready_leads]
        }
    
    except Exception as e:
        logger.error(f"❌ RECRUITMENT FAILED: {str(e)}")
        raise e






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

