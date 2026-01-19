from datetime import datetime, date, time
from typing import List, Dict, Any
from app.models.lead import Lead
from app.models.email import Email

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
