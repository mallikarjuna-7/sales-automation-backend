# Sales Automation API Documentation (Definitive Guide)

All API endpoints use the base URL:  
`https://sales-automation-backend-67f1.onrender.com/api`

---

## 🔐 Authentication (Modern Flow)

Every protected request **must** include this header:  
`Authorization: Bearer <ACCESS_TOKEN>`

---

## 🔑 Authentication Endpoints

### 1. Token Exchange
**`POST /auth/token`** (Public)  
Exchange Google Identity Token for Backend JWT.

- **Query Parameters**:
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id_token_str` | string | **Yes** | The `credential` string returned by Google GSI. |

- **Complete Response Structure**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "user@hikigai.ai",
    "name": "Jane Doe",
    "picture": "https://lh3.googleusercontent.com/a/..."
  }
}
```

- **CURL**:
```bash
curl -X POST "https://sales-automation-backend-67f1.onrender.com/api/auth/token?id_token_str=YOUR_GOOGLE_ID_TOKEN"
```

---

### 2. Token Refresh
**`POST /auth/refresh`** (Public)  
Get a new Access Token.

- **Query Parameters**:
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `token` | string | **Yes** | Your long-lived Refresh Token. |

- **Complete Response Structure**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 3. Logout
**`POST /auth/logout`** (Protected)  
Revokes all active sessions for the current user.

- **CURL**:
```bash
curl -X POST "https://sales-automation-backend-67f1.onrender.com/api/auth/logout" \
     -H "Authorization: Bearer <TOKEN>"
```

---

## 📊 Dashboard & Analytics (Protected)

### 1. Main Stats Summary
**`GET /dashboard/main-stats`**
Overall summary of the entire sales pipeline.

- **Optional Filters**: `start_date`, `end_date` (Format: `YYYY-MM-DD`).

- **Complete Response Structure**:
```json
{
  "total_leads": 1250,
  "with_email": 850,
  "without_email": 400,
  "apollo_enriched_leads": 120,
  "apollo_searched": 200,
  "email_success_rate": 68.5,
  "total_drafts": 45,
  "sent": 150,
  "failed": 12,
  "last_updated": "2026-01-27T04:30:00Z",
  "city_stats": [
    {
      "city": "Florida",
      "total_leads": 150,
      "with_email": 110,
      "without_email": 40,
      "apollo_enriched_leads": 25,
      "apollo_searched": 30,
      "email_success_rate": 83.3,
      "total_drafts": 5,
      "sent": 15,
      "failed": 1,
      "leads_left": 80
    }
  ]
}
```

---

### 2. Leads WITH Emails 
**`GET /dashboard/with-email-stats`**
List of leads that possess a valid email address.

- **Query Parameters**: `page` (default 1), `page_size` (default 10), `start_date` (YYYY-MM-DD).

- **Complete Response Structure**:
```json
{
  "total_with_email": 850,
  "drafted": 45,
  "sent": 150,
  "success_rate": 92.0,
  "leads_data": {
    "leads": [
      {
        "id": "65b2f1...",
        "npi": "1982736450",
        "name": "Dr. Sarah Johnson",
        "clinic_name": "Evergreen Health",
        "address": "456 Oak Ave",
        "city": "Tampa",
        "state": "FL",
        "specialty": "Internal Medicine",
        "phone": "+1-813-555-0199",
        "email": "s.johnson@evergreen.com",
        "has_email": true,
        "is_emailed": false,
        "visited": true,
        "emr_system": "Epic",
        "enrichment_status": "apollo_enriched",
        "created_at": "2026-01-20T10:00:00Z"
      }
    ],
    "total": 850,
    "page": 1,
    "page_size": 10,
    "pages": 85
  }
}
```

---

### 3. Leads WITHOUT Emails
**`GET /dashboard/without-email-stats`**
List of leads requiring manual research.

- **Complete Response Structure**:
```json
{
  "total_without_email": 400,
  "with_phone_number": 350,
  "with_address": 400,
  "contactable": 100.0,
  "leads_data": {
    "leads": [
      {
        "id": "65b2f2...",
        "npi": "1029384756",
        "name": "Dr. Robert Miller",
        "clinic_name": "Sunrise Cardiology",
        "address": "789 Palm Dr",
        "city": "Miami",
        "state": "FL",
        "specialty": "Cardiology",
        "phone": "+1-305-555-0122",
        "email": null,
        "has_email": false,
        "visited": false,
        "emr_system": "Cerner",
        "enrichment_status": "scout_only",
        "created_at": "2026-01-22T14:30:00Z"
      }
    ],
    "total": 400,
    "page": 1,
    "page_size": 10,
    "pages": 40
  }
}
```

---

## 🩺 Lead Management (Protected)

### 1. Intelligent Recruitment (Apollo + NPPES)
**`POST /leads/recruit`**
Triggers the automated enrichment flow.

- **Request Body (JSON)**:
| Field | Type | Required | Default |
| :--- | :--- | :--- | :--- |
| `location` | string | **Yes** | - |
| `specialty` | string | No | `Primary Care` |

- **Complete Response Structure**:
```json
{
  "status": "success",
  "location": "Florida",
  "specialty": "Internal Medicine",
  "enriched_count": 10,
  "returned_count": 5,
  "remaining_credits": 3450,
  "leads": [
    {
      "npi": "1982736450",
      "name": "Dr. Sarah Johnson",
      "clinic_name": "Evergreen Health",
      "address": "456 Oak Ave",
      "city": "Tampa",
      "state": "FL",
      "specialty": "Internal Medicine",
      "phone": "+1-813-555-0199",
      "email": "s.johnson@evergreen.com",
      "has_email": true,
      "is_emailed": false,
      "visited": true,
      "website": "www.evergreen.com",
      "emr_system": "Epic",
      "apollo_linkedin": "https://linkedin.com/in/sjohnson",
      "enrichment_status": "apollo_enriched",
      "created_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

- **CURL**:
```bash
curl -X POST "https://sales-automation-backend-67f1.onrender.com/api/leads/recruit" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"location": "Florida", "specialty": "Internal Medicine"}'
```

---

### 2. Bulk Load (NPPES Scout)
**`POST /leads/load`**
- **Request Body (JSON)**:
| Field | Type | Required | Default |
| :--- | :--- | :--- | :--- |
| `location` | string | **Yes** | - |
| `specialty` | string | No | `Primary Care` |
| `limit` | integer | No | 1200 |

- **Complete Response Structure**:
```json
{
  "status": "success",
  "location": "New York",
  "specialty": "Primary Care",
  "leads_loaded": 1200,
  "with_email": 450,
  "without_email": 750
}
```

- **CURL**:
```bash
curl -X POST "https://sales-automation-backend-67f1.onrender.com/api/leads/load" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"location": "New York", "specialty": "Primary Care"}'
```

---

## 📧 Email Outreach (Protected)

### 1. Send Email
**`POST /emails/send`**
- **Request Body (JSON)**:
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `sender` | string | **Yes** | Your account email. |
| `receiver` | string | **Yes** | Doctor's email. |
| `subject` | string | **Yes** | Email subject. |
| `body` | string | **Yes** | Supports HTML. |
| `lead_id` | string | No | Links to Lead record. |

- **Complete Response Structure**:
```json
{
  "status": "sent",
  "message_id": "GMAIL_18f2a...",
  "receiver": "dr.smith@example.com",
  "subject": "EMR Efficiency",
  "timestamp": "2026-01-27T10:00:00Z"
}
```

- **CURL**:
```bash
curl -X POST "https://sales-automation-backend-67f1.onrender.com/api/emails/send" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
           "sender": "user@hikigai.ai",
           "receiver": "dr.smith@example.com",
           "subject": "EMR Efficiency",
           "body": "Hi Doctor..."
         }'
```

---

## 📋 Response Error Key
- **401**: Missing or Expired Token. Trigger Token Refresh.
- **403**: Forbidden (Incorrect domain or inactive account).
- **422**: Validation Error (Check your JSON body structure).
