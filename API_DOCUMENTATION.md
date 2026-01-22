# Sales Automation API - Technical Documentation

## Table of Contents
1. [API Base URL](#api-base-url)
2. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [Leads Management](#leads-management)
   - [Email Management](#email-management)
   - [Dashboard Analytics](#dashboard-analytics)
3. [Database Structure](#database-structure)

---

## API Base URL

```
http://localhost:8000
```

---

## API Endpoints

### Health Check

#### **GET** `/api/health/`

**Description:**  
Verifies that the API server is running and can successfully connect to the MongoDB database. Returns the current health status of the application, database connection status, and the total number of leads stored in the database. Use this endpoint for monitoring, health checks, uptime monitoring, load balancer health checks, or troubleshooting connectivity issues.

**cURL Command:**
```bash
curl -X GET "http://localhost:8000/api/health/" \
  -H "accept: application/json"
```

**Response Body (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "total_leads_in_db": 42
}
```

---

### Leads Management

#### **POST** `/api/leads/`

**Description:**  
Create new lead records in the database. Supports both single lead creation and bulk import of multiple leads in a single API call. This endpoint allows you to add new sales leads (clinics and doctors) to the system. It accepts an array of lead objects, making it ideal for importing leads from CSV files, CRM systems, or web forms. The system enforces email uniqueness to prevent duplicate entries.

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/leads/" \
  -H "accept: application/json" \
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
    },
    {
      "name": "Dr. Sarah Johnson",
      "clinic_name": "Johnson Family Clinic",
      "address": "456 Oak Avenue",
      "city": "Los Angeles",
      "emr_system": "Cerner",
      "clinic_size": "Small",
      "email": "sarah.johnson@johnsonclinic.com"
    }
  ]'
```

**Request Body Schema:**
```json
[
  {
    "name": "string",
    "clinic_name": "string",
    "address": "string",
    "city": "string",
    "emr_system": "Epic | Cerner | Athena | eClinicalWorks | Other",
    "clinic_size": "Solo | Small | Medium | Large",
    "email": "string (valid email)"
  }
]
```

**Response Body (200 OK):**
```json
[
  {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "name": "Dr. John Smith",
    "clinic_name": "Smith Medical Center",
    "address": "123 Main Street",
    "city": "New York",
    "emr_system": "Epic",
    "clinic_size": "Medium",
    "email": "john.smith@smithmedical.com",
    "created_at": "2026-01-22T05:47:58.123Z"
  },
  {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k2",
    "name": "Dr. Sarah Johnson",
    "clinic_name": "Johnson Family Clinic",
    "address": "456 Oak Avenue",
    "city": "Los Angeles",
    "emr_system": "Cerner",
    "clinic_size": "Small",
    "email": "sarah.johnson@johnsonclinic.com",
    "created_at": "2026-01-22T05:47:58.456Z"
  }
]
```

---

#### **GET** `/api/leads/`

**Description:**  
Retrieve a list of leads from the database with optional filtering capabilities. Fetch leads based on specific criteria such as city or EMR system. This endpoint is useful for segmenting your sales targets, creating targeted outreach campaigns, or generating reports. Results are paginated with a configurable limit to manage large datasets efficiently.

**Query Parameters:**
- `city` (optional): Filter by city name
- `emr_system` (optional): Filter by EMR system
- `limit` (optional, default: 50, max: 100): Number of results to return

**cURL Command (No Filters):**
```bash
curl -X GET "http://localhost:8000/api/leads/?limit=50" \
  -H "accept: application/json"
```

**cURL Command (With Filters):**
```bash
curl -X GET "http://localhost:8000/api/leads/?city=New%20York&emr_system=Epic&limit=10" \
  -H "accept: application/json"
```

**Response Body (200 OK):**
```json
[
  {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k1",
    "name": "Dr. John Smith",
    "clinic_name": "Smith Medical Center",
    "address": "123 Main Street",
    "city": "New York",
    "emr_system": "Epic",
    "clinic_size": "Medium",
    "email": "john.smith@smithmedical.com",
    "created_at": "2026-01-22T05:47:58.123Z"
  }
]
```

---

#### **GET** `/api/leads/{lead_id}`

**Description:**  
Retrieve detailed information about a specific lead using its unique identifier. Fetch complete details of a single lead record. This endpoint is useful when you need to display lead information in detail views, update forms, or verify lead data before sending emails. Returns a 404 error if the lead ID doesn't exist.

**Path Parameters:**
- `lead_id`: MongoDB ObjectId of the lead

**cURL Command:**
```bash
curl -X GET "http://localhost:8000/api/leads/65a1b2c3d4e5f6g7h8i9j0k1" \
  -H "accept: application/json"
```

**Response Body (200 OK):**
```json
{
  "_id": "65a1b2c3d4e5f6g7h8i9j0k1",
  "name": "Dr. John Smith",
  "clinic_name": "Smith Medical Center",
  "address": "123 Main Street",
  "city": "New York",
  "emr_system": "Epic",
  "clinic_size": "Medium",
  "email": "john.smith@smithmedical.com",
  "created_at": "2026-01-22T05:47:58.123Z"
}
```

**Response Body (404 Not Found):**
```json
{
  "detail": "Lead not found"
}
```

---

### Email Management

#### **POST** `/api/emails/send`

**Description:**  
Send a sales outreach email to a lead and automatically log the communication in the database. This endpoint handles the entire email workflow: sending the email via SMTP and creating a permanent record in the database. By linking emails to lead IDs, you can track all communications with each prospect, maintain email history, and analyze outreach effectiveness. Essential for sales automation and follow-up tracking.

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/emails/send" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "sales@company.com",
    "receiver": "john.smith@smithmedical.com",
    "subject": "Transform Your Practice with Our EMR Solution",
    "body": "Dear Dr. Smith,\n\nWe would like to introduce our cutting-edge EMR solution...",
    "lead_id": "65a1b2c3d4e5f6g7h8i9j0k1"
  }'
```

**Request Body Schema:**
```json
{
  "sender": "string",
  "receiver": "string",
  "subject": "string",
  "body": "string",
  "lead_id": "string (optional, MongoDB ObjectId)"
}
```

**Response Body (200 OK):**
```json
{
  "status": "success",
  "message": "Email sent successfully",
  "email_id": "65a1b2c3d4e5f6g7h8i9j0k3",
  "details": {
    "sender": "sales@company.com",
    "receiver": "john.smith@smithmedical.com",
    "subject": "Transform Your Practice with Our EMR Solution",
    "timestamp": "2026-01-22T05:50:15.789Z"
  }
}
```

---

#### **GET** `/api/emails/`

**Description:**  
Retrieve a list of recently sent emails from the database. Fetch the most recent email records, sorted by timestamp in descending order. This endpoint is useful for displaying email history, auditing outreach activities, or reviewing recent communications. The results include the associated lead reference for tracking which prospects have been contacted.

**Query Parameters:**
- `limit` (optional, default: 10): Number of emails to return

**cURL Command:**
```bash
curl -X GET "http://localhost:8000/api/emails/?limit=5" \
  -H "accept: application/json"
```

**Response Body (200 OK):**
```json
[
  {
    "_id": "65a1b2c3d4e5f6g7h8i9j0k3",
    "sender": "sales@company.com",
    "receiver": "john.smith@smithmedical.com",
    "subject": "Transform Your Practice with Our EMR Solution",
    "body": "Dear Dr. Smith,\n\nWe would like to introduce our cutting-edge EMR solution...",
    "lead": {
      "$ref": "leads",
      "$id": "65a1b2c3d4e5f6g7h8i9j0k1"
    },
    "timestamp": "2026-01-22T05:50:15.789Z"
  }
]
```

---

### Dashboard Analytics

#### **GET** `/api/dashboard/stats`

**Description:**  
Generate comprehensive analytics and statistics for the sales automation platform. This endpoint provides key performance metrics including total leads created, total emails sent, recent activity feed, and geographic distribution of leads and emails. The data can be filtered by date range, making it perfect for creating dashboards, generating reports, tracking campaign performance, and analyzing sales team productivity. Defaults to the last 7 days if no date range is specified.

**Query Parameters:**
- `start_date` (optional, format: YYYY-MM-DD): Start date for analytics (defaults to 7 days ago)
- `end_date` (optional, format: YYYY-MM-DD): End date for analytics (defaults to today)

**cURL Command (Default - Last 7 Days):**
```bash
curl -X GET "http://localhost:8000/api/dashboard/stats" \
  -H "accept: application/json"
```

**cURL Command (Custom Date Range):**
```bash
curl -X GET "http://localhost:8000/api/dashboard/stats?start_date=2026-01-01&end_date=2026-01-22" \
  -H "accept: application/json"
```

**Response Body (200 OK):**
```json
{
  "total_leads": 42,
  "total_emails": 128,
  "recent_activity": [
    {
      "name": "Dr. John Smith",
      "clinic_name": "Smith Medical Center",
      "emr_system": "Epic",
      "timestamp": "2026-01-22T05:50:15.789Z"
    },
    {
      "name": "Dr. Sarah Johnson",
      "clinic_name": "Johnson Family Clinic",
      "emr_system": "Cerner",
      "timestamp": "2026-01-22T04:30:22.456Z"
    },
    {
      "name": "Dr. Michael Brown",
      "clinic_name": "Brown Healthcare",
      "emr_system": "Athena",
      "timestamp": "2026-01-22T03:15:10.123Z"
    }
  ],
  "leads_by_city": [
    {
      "city": "New York",
      "leads": 15,
      "emails": 45
    },
    {
      "city": "Los Angeles",
      "leads": 12,
      "emails": 38
    },
    {
      "city": "Chicago",
      "leads": 8,
      "emails": 25
    },
    {
      "city": "Houston",
      "leads": 7,
      "emails": 20
    }
  ]
}
```

---

## Database Structure

### MongoDB Collections

The application uses MongoDB with the Beanie ODM (Object Document Mapper). Below is the detailed structure of each collection:

---

#### **Collection: `leads`**

Stores information about potential sales leads (clinics and doctors).

**Schema:**

| Field | Type | Required | Unique | Default | Description |
|-------|------|----------|--------|---------|-------------|
| `_id` | ObjectId | Yes | Yes | Auto-generated | MongoDB unique identifier |
| `name` | String | Yes | No | - | Name of the contact person (e.g., doctor) |
| `clinic_name` | String | Yes | No | - | Name of the clinic or medical practice |
| `address` | String | Yes | No | - | Physical address of the clinic |
| `city` | String | Yes | No | - | City where the clinic is located |
| `emr_system` | Enum | Yes | No | - | Current EMR system used (Epic, Cerner, Athena, eClinicalWorks, Other) |
| `clinic_size` | Enum | Yes | No | - | Size of the clinic (Solo, Small, Medium, Large) |
| `email` | String | Yes | **Yes** | - | Email address (must be unique) |
| `created_at` | DateTime | Yes | No | Current UTC time | Timestamp when the lead was created |

**Indexes:**
- `city` (ascending)
- `emr_system` (ascending)
- `clinic_size` (ascending)
- `created_at` (ascending)
- `email` (unique index)

**Example Document:**
```json
{
  "_id": ObjectId("65a1b2c3d4e5f6g7h8i9j0k1"),
  "name": "Dr. John Smith",
  "clinic_name": "Smith Medical Center",
  "address": "123 Main Street",
  "city": "New York",
  "emr_system": "Epic",
  "clinic_size": "Medium",
  "email": "john.smith@smithmedical.com",
  "created_at": ISODate("2026-01-22T05:47:58.123Z")
}
```

---

#### **Collection: `emails`**

Stores records of all outreach emails sent to leads.

**Schema:**

| Field | Type | Required | Unique | Default | Description |
|-------|------|----------|--------|---------|-------------|
| `_id` | ObjectId | Yes | Yes | Auto-generated | MongoDB unique identifier |
| `sender` | String | Yes | No | - | Email address of the sender |
| `receiver` | String | Yes | No | - | Email address of the recipient |
| `subject` | String | Yes | No | "Sales Automation Outreach" | Subject line of the email |
| `body` | String | Yes | No | - | Full body content of the email |
| `lead` | DBRef (Link) | No | No | null | Reference to the associated lead document |
| `timestamp` | DateTime | Yes | No | Current UTC time | Timestamp when the email was sent |

**Indexes:**
- `sender` (ascending)
- `receiver` (ascending)
- `timestamp` (ascending)

**Example Document:**
```json
{
  "_id": ObjectId("65a1b2c3d4e5f6g7h8i9j0k3"),
  "sender": "sales@company.com",
  "receiver": "john.smith@smithmedical.com",
  "subject": "Transform Your Practice with Our EMR Solution",
  "body": "Dear Dr. Smith,\n\nWe would like to introduce our cutting-edge EMR solution that can help streamline your practice operations...",
  "lead": {
    "$ref": "leads",
    "$id": ObjectId("65a1b2c3d4e5f6g7h8i9j0k1")
  },
  "timestamp": ISODate("2026-01-22T05:50:15.789Z")
}
```

---

### Database Relationships

```mermaid
erDiagram
    LEADS ||--o{ EMAILS : "receives"
    
    LEADS {
        ObjectId _id PK
        string name
        string clinic_name
        string address
        string city
        enum emr_system
        enum clinic_size
        string email UK
        datetime created_at
    }
    
    EMAILS {
        ObjectId _id PK
        string sender
        string receiver
        string subject
        string body
        ObjectId lead FK
        datetime timestamp
    }
```

**Relationship Details:**
- One Lead can have many Emails (One-to-Many)
- The `lead` field in the `emails` collection is a DBRef (database reference) that links to a document in the `leads` collection
- This relationship is optional - emails can exist without being linked to a lead

---

### Database Configuration

**Connection Details:**
- **Database Type:** MongoDB Atlas (Cloud-hosted)
- **ODM:** Beanie (built on top of Motor, the async MongoDB driver)
- **Connection String:** Configured via environment variable `MONGODB_URL`
- **Database Name:** Configured via environment variable `DB_NAME` (default: "kabaddi")

**Environment Variables:**
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=kabaddi
PORT=8000
```

---

## Additional Notes

### Data Validation

- **Email Uniqueness:** The system enforces unique email addresses for leads. Attempting to create a lead with a duplicate email will result in an error.
- **Email Format:** All email fields are validated to ensure they follow proper email format.
- **Enum Validation:** The `emr_system` and `clinic_size` fields only accept predefined values.

### Error Handling

Common HTTP status codes returned by the API:

- **200 OK:** Request successful
- **404 Not Found:** Resource not found (e.g., lead ID doesn't exist)
- **422 Unprocessable Entity:** Validation error (e.g., invalid email format, duplicate email)
- **500 Internal Server Error:** Server-side error

### API Documentation

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
