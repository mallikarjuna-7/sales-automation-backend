# How to Upload Environment Variables to Render

## ✅ Changes Made

1. **config.py** - Removed ALL hardcoded defaults
   - Now requires ALL variables from environment
   - Reads from `.env` locally
   - Reads from Render environment variables in production

2. **render.env** - Created this file for you to upload to Render
   - Contains all environment variables with production values
   - Ready to copy-paste into Render

---

## 📤 Upload to Render - Two Methods

### Method 1: Copy-Paste Individual Variables (Recommended)

1. Go to your Render service dashboard
2. Click **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Copy each line from `render.env` file:

```
MONGODB_URL=mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi.iaqsvzl.mongodb.net/kabaddi?retryWrites=true&w=majority&appName=kabaddi
DB_NAME=kabaddi
PORT=10000
DEBUG=False
ML_SERVICE_URL=http://localhost:8080
MAIL_USERNAME=mrewards7745@gmail.com
MAIL_PASSWORD=jowo yrvh rvrk hygk
MAIL_FROM=mrewards7745@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_FROM_NAME=Sales Automation
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
```

5. For each line:
   - **Key** = everything before `=`
   - **Value** = everything after `=`
6. Click **"Save Changes"**

### Method 2: Bulk Upload (If Render Supports It)

Some Render plans allow uploading a `.env` file directly. If available:

1. Go to Environment tab
2. Look for "Upload .env file" or "Bulk add" option
3. Upload the `render.env` file

---

## 📋 All Environment Variables

| Variable Name | Value in render.env |
|---------------|---------------------|
| `MONGODB_URL` | `mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi.iaqsvzl.mongodb.net/kabaddi?retryWrites=true&w=majority&appName=kabaddi` |
| `DB_NAME` | `kabaddi` |
| `PORT` | `10000` |
| `DEBUG` | `False` |
| `ML_SERVICE_URL` | `http://localhost:8080` |
| `MAIL_USERNAME` | `mrewards7745@gmail.com` |
| `MAIL_PASSWORD` | `jowo yrvh rvrk hygk` |
| `MAIL_FROM` | `mrewards7745@gmail.com` |
| `MAIL_SERVER` | `smtp.gmail.com` |
| `MAIL_PORT` | `587` |
| `MAIL_FROM_NAME` | `Sales Automation` |
| `MAIL_STARTTLS` | `True` |
| `MAIL_SSL_TLS` | `False` |

---

## ⚠️ Important Notes

> [!WARNING]
> **PORT Value**: I set PORT to `10000` in render.env, but Render usually auto-sets this. If Render automatically provides a PORT variable, you can skip adding it manually.

> [!NOTE]
> **No Hardcoded Values**: config.py now has ZERO hardcoded defaults. All values MUST come from environment variables.

---

## 🔄 How It Works Now

```
Local Development:
  .env file → config.py → Your App

Render Production:
  Render env vars → config.py → Your App
```

**Same config.py, different sources!**

---

## ✅ Verification

After uploading to Render, check the logs. You should see:
- ✅ "Starting Sales Automation API..."
- ✅ "Database initialized successfully"

If you see errors about missing environment variables, double-check that all 13 variables are added to Render.

---

## 📁 Files Updated

1. **[config.py](file:///c:/Users/sajja/Desktop/sales-automation/sales-automation-backend/app/core/config.py)** - No hardcoded defaults
2. **[.env](file:///c:/Users/sajja/Desktop/sales-automation/sales-automation-backend/.env)** - Updated with all variables (local use)
3. **[.env.example](file:///c:/Users/sajja/Desktop/sales-automation/sales-automation-backend/.env.example)** - Updated template
4. **[render.env](file:///c:/Users/sajja/Desktop/sales-automation/sales-automation-backend/render.env)** - NEW! Ready for Render upload
