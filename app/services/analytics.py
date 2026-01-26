from datetime import datetime, date, time
from typing import List, Dict, Any
from app.models.lead import Lead
from app.models.email import Email
from typing import Optional

async def get_dashboard_stats(start_date: date, end_date: date) -> Dict[str, Any]:
    # Convert dates to datetimes for MongoDB queries
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    # Total Leads created in period
    total_leads = await Lead.find({
        "created_at": {"$gte": start_dt, "$lte": end_dt}
    }).count()
    
    # Total Emails sent in period
    total_emails = await Email.find({
        "timestamp": {"$gte": start_dt, "$lte": end_dt}
    }).count()
    
    # Recent Activity (Last 3 emails)
    # We fetch them manually to avoid the complex fetch_links cursor issue in this environment
    recent_emails = await Email.find_all().sort("-timestamp").limit(3).to_list()
    recent_activity = []
    for email in recent_emails:
        lead_info = "Unknown"
        clinic_info = "Unknown"
        emr_info = "Unknown"
        
        if email.lead:
            # Manually fetch the linked lead using the reference ID
            lead = await Lead.get(email.lead.ref.id)
            if lead:
                lead_info = lead.name
                clinic_info = lead.clinic_name
                emr_info = lead.emr_system
                
        activity = {
            "name": lead_info,
            "clinic_name": clinic_info,
            "emr_system": emr_info,
            "timestamp": email.timestamp
        }
        recent_activity.append(activity)
        
    # Leads by City using aggregate (direct Motor collection to be safe)
    pipeline_leads = [
        {"$match": {"created_at": {"$gte": start_dt, "$lte": end_dt}}},
        {"$group": {
                "_id": "$city",
                "lead_count": {"$sum": 1}
            }},
        {"$project": {
                "city": "$_id",
                "lead_count": 1,
                "_id": 0
            }}
    ]
    city_leads = await Lead.get_pymongo_collection().aggregate(pipeline_leads).to_list(length=None)
    
    # Email counts by city
    pipeline_emails = [
        {"$match": {"timestamp": {"$gte": start_dt, "$lte": end_dt}}},
        {"$lookup": {
                "from": "leads",
                "localField": "lead.$id",
                "foreignField": "_id",
                "as": "lead_info"
            }},
        {"$unwind": "$lead_info"},
        {"$group": {
                "_id": "$lead_info.city",
                "email_count": {"$sum": 1}
            }},
        {"$project": {
                "city": "$_id",
                "email_count": 1,
                "_id": 0
            }}
    ]
    city_emails = await Email.get_pymongo_collection().aggregate(pipeline_emails).to_list(length=None)
    
    # Merge city stats
    city_map = {item["city"]: {"city": item["city"], "leads": item["lead_count"], "emails": 0} for item in city_leads}
    for item in city_emails:
        if item["city"] in city_map:
            city_map[item["city"]]["emails"] = item["email_count"]
        else:
            city_map[item["city"]] = {"city": item["city"], "leads": 0, "emails": item["email_count"]}
            
    return {
        "total_leads": total_leads,
        "total_emails": total_emails,
        "recent_activity": recent_activity,
        "leads_by_city": list(city_map.values())
    }


async def get_main_dashboard_stats(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """Get overall summary for the main sales dashboard"""
    # Build queries
    lead_query = {}
    email_query = {}
    
    if start_date or end_date:
        if start_date:
            start_dt = datetime.combine(start_date, time.min)
            lead_query["created_at"] = {"$gte": start_dt}
            email_query["timestamp"] = {"$gte": start_dt}
        
        if end_date:
            end_dt = datetime.combine(end_date, time.max)
            lead_query.setdefault("created_at", {})["$lte"] = end_dt
            email_query.setdefault("timestamp", {})["$lte"] = end_dt

    # --- HIGH PERFORMANCE AGGREGATION PIPELINE ---
    # This single pipeline replaces all global and city-wise queries
    pipeline = [
        {"$match": lead_query},
        # Join with emails to get city-wise and global outreach stats
        {"$lookup": {
            "from": "emails1",
            "localField": "_id",
            "foreignField": "lead.$id",
            "as": "emails"
        }},
        {"$facet": {
            "global_counts": [
                {"$group": {
                    "_id": None,
                    "total_leads": {"$sum": 1},
                    "with_email": {"$sum": {"$cond": ["$has_email", 1, 0]}},
                    "without_email": {"$sum": {"$cond": ["$has_email", 0, 1]}},
                    "apollo_enriched_leads": {"$sum": {"$cond": [{"$eq": ["$enrichment_status", "apollo_enriched"]}, 1, 0]}},
                    "apollo_searched": {"$sum": {"$cond": ["$apollo_searched", 1, 0]}},
                    "max_lead_created": {"$max": "$created_at"},
                    # Flatten and collect all emails to count status
                    "all_emails": {"$push": "$emails"}
                }}
            ],
            "city_breakdown": [
                # 1. Normalize City Names
                {"$addFields": {
                    "normalized_city_key": {"$trim": {"input": {"$toUpper": "$city"}}}
                }},
                # 2. Fix specific typos (e.g., Newyork -> NEW YORK)
                {"$addFields": {
                    "normalized_city_key": {
                        "$cond": [
                            {"$eq": ["$normalized_city_key", "NEWYORK"]}, 
                            "NEW YORK", 
                            "$normalized_city_key"
                        ]
                    }
                }},
                # 3. Group by the clean city name
                {"$group": {
                    "_id": "$normalized_city_key",
                    "display_city": {"$first": "$city"}, # Store original casing for display
                    "total_leads": {"$sum": 1},
                    "with_email": {"$sum": {"$cond": ["$has_email", 1, 0]}},
                    "without_email": {"$sum": {"$cond": ["$has_email", 0, 1]}},
                    "apollo_enriched_leads": {"$sum": {"$cond": [{"$eq": ["$enrichment_status", "apollo_enriched"]}, 1, 0]}},
                    "apollo_searched": {"$sum": {"$cond": ["$apollo_searched", 1, 0]}},
                    "max_lead_created": {"$max": "$created_at"},
                    # Capture emails in this city bucket
                    "city_emails": {"$push": "$emails"}
                }}
            ]
        }}
    ]

    cursor = Lead.get_pymongo_collection().aggregate(pipeline)
    results = await cursor.to_list(length=1)
    data = results[0] if results else {"global_counts": [], "city_breakdown": []}
    
    # Process Global Stats
    globals = data["global_counts"][0] if data["global_counts"] else {}
    
    # Flatten emails to count global sent/failed
    all_emails = [e for sublist in globals.get("all_emails", []) for e in sublist]
    global_sent = sum(1 for e in all_emails if e.get("status") == "sent")
    global_failed = sum(1 for e in all_emails if e.get("status") == "failed")
    
    t_with_email = globals.get("with_email", 0)
    global_success_rate = (global_sent / t_with_email * 100) if t_with_email > 0 else 0.0

    # Last global updated: strictly the latest lead created
    last_updated = globals.get("max_lead_created")

    # Process City Breakdown
    city_stats_list = []
    for city_data in data.get("city_breakdown", []):
        c_with_email = city_data.get("with_email", 0)
        
        # Flatten city emails
        c_emails = [e for sublist in city_data.get("city_emails", []) for e in sublist]
        c_sent = sum(1 for e in c_emails if e.get("status") == "sent")
        c_failed = sum(1 for e in c_emails if e.get("status") == "failed")
        
        c_success_rate = (c_sent / c_with_email * 100) if c_with_email > 0 else 0.0
        
        # City last updated: strictly the latest lead created in this city
        c_last_updated = city_data.get("max_lead_created")

        city_stats_list.append({
            "city": city_data["display_city"].title() if city_data.get("display_city") else city_data["_id"].title(),
            "total_leads": city_data["total_leads"],
            "with_email": c_with_email,
            "without_email": city_data["without_email"],
            "apollo_enriched_leads": city_data["apollo_enriched_leads"],
            "apollo_searched": city_data["apollo_searched"],
            "email_success_rate": round(c_success_rate, 2),
            "total_drafts": len(c_emails),
            "sent": c_sent,
            "failed": c_failed,
            "last_updated": c_last_updated,
            "leads_left": city_data["total_leads"] - city_data["apollo_searched"]
        })

    return {
        "total_leads": globals.get("total_leads", 0),
        "with_email": t_with_email,
        "without_email": globals.get("without_email", 0),
        "apollo_enriched_leads": globals.get("apollo_enriched_leads", 0),
        "apollo_searched": globals.get("apollo_searched", 0),
        "email_success_rate": round(global_success_rate, 2),
        "total_drafts": len(all_emails),
        "sent": global_sent,
        "failed": global_failed,
        "last_updated": last_updated,
        "city_stats": city_stats_list
    }


async def get_with_email_stats(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """Get metrics for leads with contact info and paginated list using optimized aggregation"""
    lead_query = {"has_email": True}
    
    if start_date or end_date:
        if start_date:
            start_dt = datetime.combine(start_date, time.min)
            lead_query["created_at"] = {"$gte": start_dt}
        
        if end_date:
            end_dt = datetime.combine(end_date, time.max)
            lead_query.setdefault("created_at", {})["$lte"] = end_dt

    skip = (page - 1) * page_size

    pipeline = [
        {"$match": lead_query},
        {"$facet": {
            "metadata": [
                {"$group": {"_id": None, "total": {"$sum": 1}}},
                {"$lookup": {
                    "from": "emails1",
                    "localField": "_id",
                    "foreignField": "lead.$id",
                    "as": "emails"
                }},
                {"$unwind": {"path": "$emails", "preserveNullAndEmptyArrays": True}},
                {"$group": {
                    "_id": None,
                    "total": {"$first": "$total"},
                    "sent": {"$sum": {"$cond": [{"$eq": ["$emails.status", "sent"]}, 1, 0]}},
                    "failed": {"$sum": {"$cond": [{"$eq": ["$emails.status", "failed"]}, 1, 0]}}
                }}
            ],
            "leads": [
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": page_size},
                {"$addFields": {"id": {"$toString": "$_id"}}},
                {"$project": {"_id": 0}}
            ]
        }}
    ]

    cursor = Lead.get_pymongo_collection().aggregate(pipeline)
    results = await cursor.to_list(length=1)
    data = results[0] if results else {"metadata": [], "leads": []}

    meta = data["metadata"][0] if data["metadata"] else {"total": 0, "sent": 0, "failed": 0}
    total = meta.get("total", 0)
    sent_count = meta.get("sent", 0)
    failed_count = meta.get("failed", 0)
    drafted_count = sent_count + failed_count
    
    success_rate = (sent_count / drafted_count * 100) if drafted_count > 0 else 0.0
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "total_with_email": total,
        "drafted": drafted_count,
        "sent": sent_count,
        "success_rate": round(success_rate, 2),
        "leads_data": {
            "leads": data["leads"],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
    }


async def get_without_email_stats(
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """Get metrics for leads needing manual research and paginated list using optimized aggregation"""
    lead_query = {"has_email": False}
    
    if start_date or end_date:
        if start_date:
            start_dt = datetime.combine(start_date, time.min)
            lead_query["created_at"] = {"$gte": start_dt}
        
        if end_date:
            end_dt = datetime.combine(end_date, time.max)
            lead_query.setdefault("created_at", {})["$lte"] = end_dt

    skip = (page - 1) * page_size

    pipeline = [
        {"$match": lead_query},
        {"$facet": {
            "metadata": [
                {"$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "with_phone": {"$sum": {"$cond": [{"$ne": ["$phone", None]}, 1, 0]}},
                    "with_address": {"$sum": {"$cond": [{"$and": [{"$ne": ["$address", None]}, {"$ne": ["$address", ""]}]}, 1, 0]}},
                    "contactable_count": {
                        "$sum": {
                            "$cond": [
                                {"$or": [
                                    {"$ne": ["$phone", None]},
                                    {"$and": [{"$ne": ["$address", None]}, {"$ne": ["$address", ""]}]}
                                ]},
                                1, 0
                            ]
                        }
                    }
                }}
            ],
            "leads": [
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": page_size},
                {"$addFields": {"id": {"$toString": "$_id"}}},
                {"$project": {"_id": 0}}
            ]
        }}
    ]

    cursor = Lead.get_pymongo_collection().aggregate(pipeline)
    results = await cursor.to_list(length=1)
    data = results[0] if results else {"metadata": [], "leads": []}

    meta = data["metadata"][0] if data["metadata"] else {"total": 0, "with_phone": 0, "with_address": 0, "contactable_count": 0}
    total = meta.get("total", 0)
    contactable_count = meta.get("contactable_count", 0)
    
    contactable_rate = (contactable_count / total * 100) if total > 0 else 0.0
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "total_without_email": total,
        "with_phone_number": meta.get("with_phone", 0),
        "with_address": meta.get("with_address", 0),
        "contactable": round(contactable_rate, 2),
        "leads_data": {
            "leads": data["leads"],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
    }

