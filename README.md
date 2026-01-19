# Sales Automation Backend

Backend for the Sales Automation platform, built with FastAPI, Poetry, and MongoDB (Beanie ODM).

## Setup

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Environment Variables**:
   Ensure `.env` is configured with your MongoDB URL:
   ```env
   MONGODB_URL=mongodb+srv://...
   DB_NAME=kabaddi
   PORT=8000
   ```

3. **Run the Application**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## API Endpoints

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: `GET /api/health`
- **Leads**:
  - `POST /api/leads/`: Create a new lead.
  - `GET /api/leads/`: List leads with filters (`city`, `emr_system`).
- **Emails**:
  - `POST /api/emails/send`: Simulate sending an email and store the record.
- **Dashboard**:
  - `GET /api/dashboard/stats`: Get analytics with time period filtering.

## Tech Stack
- **Framework**: FastAPI
- **Database**: MongoDB (Atlas)
- **ODM**: Beanie (with Motor)
- **Dependency Management**: Poetry
