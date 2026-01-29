# Sales Automation Backend

Backend for the Sales Automation platform, built with FastAPI, Poetry, and MongoDB (Beanie ODM).

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
```

Required environment variables:
```env
MONGODB_URL=mongodb+srv://your-connection-string
DB_NAME=sales_automation
ML_SERVICE_URL=http://your-ml-service-url:8000
```

### 3. Run the Application

```bash
poetry run uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

---

## 🔐 Authentication (Modern Flow)

The system uses a **Modern Token Exchange** flow with Google OAuth 2.0. To access protected APIs, you must include a JWT token in the header.

**Full Technical Guide**: [README_API.md](README_API.md)

---

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **Technical Integration Guide**: [README_API.md](README_API.md)

---

## 🧪 Testing Endpoints with cURL

### Health Check

```bash
curl -X GET "http://localhost:8000/api/health/" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "total_leads_in_db": 42
}
```

---

### Lead Recruitment (NEW)

#### Recruit Leads for a Location

```bash
curl -X POST "http://localhost:8000/api/leads/recruit" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "New York",
    "specialty": "Primary Care",
    "count": 10
  }'
```

**Response:**
```json
{
  "status": "success",
  "location": "New York",
  "specialty": "Primary Care",
  "total_leads": 10,
  "with_email": 8,
  "without_email": 2,
  "email_coverage_percent": 80.0,
  "leads": [...]
}
```

#### Recruit with Default Settings

```bash
curl -X POST "http://localhost:8000/api/leads/recruit" \
  -H "Content-Type: application/json" \
  -d '{"location": "Chicago"}'
```

---

### Leads Management

#### Create Leads (Bulk)

```bash
curl -X POST "http://localhost:8000/api/leads/" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "Dr. John Smith",
      "clinic_name": "Smith Medical Center",
      "address": "123 Main Street",
      "city": "New York",
      "emr_system": "Epic",
      "clinic_size": "Medium",
      "email": "john.smith@smithmedical.com"
    }
  ]'
```

#### List All Leads

```bash
curl -X GET "http://localhost:8000/api/leads/?limit=10" \
  -H "accept: application/json"
```

#### Filter Leads by City

```bash
curl -X GET "http://localhost:8000/api/leads/?city=New%20York&limit=10" \
  -H "accept: application/json"
```

#### Filter Leads by EMR System

```bash
curl -X GET "http://localhost:8000/api/leads/?emr_system=Epic&limit=10" \
  -H "accept: application/json"
```

#### Get Specific Lead by ID

```bash
curl -X GET "http://localhost:8000/api/leads/{lead_id}" \
  -H "accept: application/json"
```

---

### Email Management

#### Send Email

```bash
curl -X POST "http://localhost:8000/api/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "sales@company.com",
    "receiver": "john.smith@smithmedical.com",
    "subject": "Transform Your Practice",
    "body": "Dear Dr. Smith, we would like to introduce...",
    "lead_id": "65a1b2c3d4e5f6g7h8i9j0k1"
  }'
```

#### List Recent Emails

```bash
curl -X GET "http://localhost:8000/api/emails/?limit=5" \
  -H "accept: application/json"
```

---

### Dashboard Analytics

#### Get Dashboard Stats (Last 7 Days)

```bash
curl -X GET "http://localhost:8000/api/dashboard/stats" \
  -H "accept: application/json"
```

#### Get Stats for Custom Date Range

```bash
curl -X GET "http://localhost:8000/api/dashboard/stats?start_date=2026-01-01&end_date=2026-01-22" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "total_leads": 42,
  "total_emails": 128,
  "recent_activity": [...],
  "leads_by_city": [
    {
      "city": "New York",
      "leads": 15,
      "emails": 45
    }
  ]
}
```

---

## 🏗️ Architecture

### Lead Recruitment Flow

```
Frontend → Backend → Database (check NPIs)
                  → ML Scout (generate leads)
                  → ML Apollo (enrich emails)
                  → Database (save all)
                  → Frontend (display)
```

**Key Features:**
- ✅ NPI-based duplicate prevention
- ✅ Scout API for lead generation
- ✅ Apollo API for email enrichment
- ✅ Smart data merge (Scout primary, Apollo fills gaps)
- ✅ 80-90% email coverage

---

## 📊 Database Schema

### Lead Model

**Primary Key:** `npi` (National Provider Identifier)

**Fields:**
- Basic Info: `name`, `clinic_name`, `address`, `city`, `state`, `phone`, `fax`
- Email: `email`, `has_email`
- Online: `website`, `profile_url`, `direct_messaging_address`
- EMR: `emr_system`, `emr_confidence`, `emr_source`
- Clinic: `clinic_size`, `size_confidence`
- Apollo: `apollo_email`, `apollo_confidence`, `apollo_linkedin`, etc.
- Tracking: `enrichment_status`, `created_at`, `last_enriched_at`

### Email Model

**Fields:**
- `sender`, `receiver`, `subject`, `body`
- `lead` (reference to Lead)
- `timestamp`

---

## 🔧 Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB (Atlas)
- **ODM**: Beanie (with Motor)
- **HTTP Client**: httpx (for ML service)
- **Dependency Management**: Poetry

---

## 📝 Development

### Install Development Dependencies

```bash
poetry install --with dev
```

### Run Tests

```bash
poetry run pytest
```

### Format Code

```bash
poetry run black .
```

---

## 🌐 ML Service Integration

The application integrates with an external ML service for lead generation and enrichment:

- **Scout API**: Generates physician leads with NPPES data
- **Apollo API**: Enriches leads with verified email addresses

Configure the ML service URL in `.env`:
```env
ML_SERVICE_URL=http://your-ml-service-url:8000
```

---

## 📖 Additional Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Implementation Plan](C:\Users\sajja\.gemini\antigravity\brain\ae0fa563-10a3-4b53-8c83-d4fad900bd24\implementation_plan.md) - Technical implementation details
- [Walkthrough](C:\Users\sajja\.gemini\antigravity\brain\ae0fa563-10a3-4b53-8c83-d4fad900bd24\walkthrough.md) - Implementation walkthrough

---

## 🚨 Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB connection string in .env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
```

### ML Service Connection Issues

```bash
# Verify ML service is running and accessible
curl http://your-ml-service-url:8000/api/scout
```

### Poetry Issues

```bash
# Clear cache and reinstall
poetry cache clear . --all
poetry install
```

---

## 📄 License

MIT License

---

## 👥 Contributors

- Antigravity AI Assistant
