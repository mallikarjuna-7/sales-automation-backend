# Render Deployment Guide

This guide will help you deploy the Sales Automation Backend to Render without Docker.

## Prerequisites

- A [Render account](https://render.com)
- MongoDB database (MongoDB Atlas recommended)
- Your application code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### 1. Create a New Web Service

1. Log in to your Render dashboard
2. Click **"New +"** and select **"Web Service"**
3. Connect your Git repository
4. Select the repository containing this application

### 2. Configure the Web Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `sales-automation-backend` (or your preferred name) |
| **Region** | Choose the region closest to your users |
| **Branch** | `main` (or your default branch) |
| **Root Directory** | Leave empty (or specify if your backend is in a subdirectory) |
| **Runtime** | `Python 3` |
| **Build Command** | `./build.sh` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

### 3. Set Environment Variables

In the **Environment Variables** section, add the following variables:

#### Required Variables

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `MONGODB_URL` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `DB_NAME` | Database name | `sales_automation` |
| `PORT` | Port number (auto-set by Render) | `10000` |
| `DEBUG` | Debug mode | `False` |

#### Optional Variables (ML Service)

| Variable Name | Description | Default Value |
|---------------|-------------|---------------|
| `ML_SERVICE_URL` | ML service endpoint URL | `http://localhost:8080` |

> [!NOTE]
> The ML_SERVICE_URL defaults to `http://localhost:8080`. Update this only if you have a separate ML service deployed.

#### Optional Variables (Email/SMTP)

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `MAIL_USERNAME` | SMTP username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | SMTP password/app password | `your-app-password` |
| `MAIL_FROM` | Sender email address | `your-email@gmail.com` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |

### 4. Deploy

1. Click **"Create Web Service"**
2. Render will automatically build and deploy your application
3. Wait for the deployment to complete (check the logs for any errors)

## Post-Deployment Verification

### 1. Check Health Endpoint

Once deployed, visit your service URL (e.g., `https://sales-automation-backend.onrender.com/`):

```json
{
  "message": "Sales Automation API is running"
}
```

### 2. Test API Documentation

Visit the auto-generated API docs at:
- Swagger UI: `https://your-service.onrender.com/docs`
- ReDoc: `https://your-service.onrender.com/redoc`

### 3. Test CORS

The application is configured to allow all origins (`allow_origins=["*"]`), so your frontend should be able to make requests without CORS issues.

To test CORS from your frontend:
```javascript
fetch('https://your-service.onrender.com/api/leads')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

### 4. Monitor Logs

Check the Render logs for any errors:
1. Go to your service dashboard
2. Click on the **"Logs"** tab
3. Look for successful startup messages:
   - `"Starting Sales Automation API..."`
   - `"Database initialized successfully"`

## MongoDB Configuration

### Allow Render IP Addresses

If using MongoDB Atlas:

1. Go to your MongoDB Atlas dashboard
2. Navigate to **Network Access**
3. Click **"Add IP Address"**
4. Select **"Allow Access from Anywhere"** (0.0.0.0/0) or add Render's specific IP ranges
5. Click **"Confirm"**

> [!WARNING]
> For production, consider restricting access to specific IP ranges instead of allowing all IPs.

## Troubleshooting

### Build Fails

- Check that `build.sh` has execute permissions
- Verify all dependencies in `requirements.txt` are valid
- Check Render build logs for specific error messages

### Application Won't Start

- Verify `MONGODB_URL` is correct and accessible
- Check that MongoDB allows connections from Render
- Review application logs for startup errors

### CORS Errors

- The application is already configured to allow all origins
- If you still see CORS errors, check browser console for specific error messages
- Verify the request is going to the correct Render URL

### Database Connection Issues

- Ensure MongoDB connection string is correct
- Verify MongoDB Atlas network access settings
- Check that database user has proper permissions

## Updating Your Application

Render automatically deploys when you push to your connected Git branch:

1. Make changes to your code
2. Commit and push to your repository
3. Render will automatically detect changes and redeploy

## Additional Resources

- [Render Python Documentation](https://render.com/docs/deploy-fastapi)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [MongoDB Atlas Setup](https://www.mongodb.com/docs/atlas/getting-started/)
