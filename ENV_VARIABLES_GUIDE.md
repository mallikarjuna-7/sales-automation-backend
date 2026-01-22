# Environment Variables Guide - Complete Explanation

This guide explains how environment variables work in this project and how to handle them when deploying to Render.

## 📁 Understanding the Three Files

### 1. `.env` (Local Development - **DO NOT COMMIT**)
**Location:** `c:\Users\sajja\Desktop\sales-automation\sales-automation-backend\.env`

This file contains your **actual secrets** for local development. It should be in `.gitignore` and **never committed to Git**.

**Current values in your .env:**
```env
MONGODB_URL=mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi...
DB_NAME=kabaddi
PORT=8000
DEBUG=True
MAIL_USERNAME=mrewards7745@gmail.com
MAIL_PASSWORD=jowo yrvh rvrk hygk
MAIL_FROM=mrewards7745@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

### 2. `.env.example` (Template - Safe to Commit)
**Location:** `c:\Users\sajja\Desktop\sales-automation\sales-automation-backend\.env.example`

This is a **template** showing what variables are needed, with placeholder values. Safe to commit to Git.

**Current values in .env.example:**
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=sales_automation
PORT=8080
DEBUG=False
ML_SERVICE_URL=http://localhost:8080
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
...
```

### 3. `config.py` (Default Values - Hardcoded)
**Location:** `app/core/config.py`

This file defines:
- Which variables are **required** (no default value)
- Which variables are **optional** (have default values)

**How it works:**
```python
class Settings(BaseSettings):
    MONGODB_URL: str              # ❌ REQUIRED - no default
    DB_NAME: str = "sales_automation"  # ✅ Optional - has default
    PORT: int = 8000              # ✅ Optional - has default
    DEBUG: bool = False           # ✅ Optional - has default
    ML_SERVICE_URL: str = "http://localhost:8080"  # ✅ Optional - has default
    MAIL_USERNAME: str = ""       # ✅ Optional - has default (empty)
    ...
```

## 🔄 How They Work Together

### Priority Order (Highest to Lowest):
1. **Environment variables** (from Render or system)
2. **`.env` file** (local development only)
3. **Default values in `config.py`** (hardcoded fallbacks)

### Example:
If you have:
- `config.py`: `PORT: int = 8000`
- `.env`: `PORT=8080`
- Render env var: `PORT=10000`

The app will use: **10000** (Render wins)

## 🚀 For Render Deployment

### Step 1: Identify Missing Variables in .env

Your `.env` is **missing** this variable that's in `.env.example`:
- `ML_SERVICE_URL` (but it has a default in config.py, so it's optional)

### Step 2: Add These to Render Environment Variables

In Render's dashboard, add these environment variables:

#### ✅ Required Variables

| Variable | Value from Your .env | Notes |
|----------|---------------------|-------|
| `MONGODB_URL` | `mongodb+srv://smallikarjun713_db_user:lIOKUAVgJX47lx3X@kabaddi.iaqsvzl.mongodb.net/kabaddi?retryWrites=true&w=majority&appName=kabaddi` | Your actual MongoDB connection |
| `DB_NAME` | `kabaddi` | Your database name |

#### ⚙️ Recommended Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `DEBUG` | `False` | Set to False for production |
| `PORT` | (Leave empty) | Render sets this automatically |

#### 📧 Optional - Email Variables (if you want email functionality)

| Variable | Value from Your .env |
|----------|---------------------|
| `MAIL_USERNAME` | `mrewards7745@gmail.com` |
| `MAIL_PASSWORD` | `jowo yrvh rvrk hygk` |
| `MAIL_FROM` | `mrewards7745@gmail.com` |
| `MAIL_SERVER` | `smtp.gmail.com` |
| `MAIL_PORT` | `587` |

#### 🤖 Optional - ML Service (uses default if not set)

| Variable | Default Value | When to Change |
|----------|---------------|----------------|
| `ML_SERVICE_URL` | `http://localhost:8080` | Only if you have a separate ML service deployed |

### Step 3: What NOT to Add

**Don't add these** - they already have good defaults in `config.py`:
- `MAIL_FROM_NAME` (defaults to "Sales Automation")
- `MAIL_STARTTLS` (defaults to True)
- `MAIL_SSL_TLS` (defaults to False)

## 📋 Quick Checklist for Render

### Minimum Required (to get app running):
- ✅ `MONGODB_URL` - Your MongoDB connection string
- ✅ `DB_NAME` - Your database name (e.g., "kabaddi")

### Recommended:
- ✅ `DEBUG` - Set to `False`

### Optional (add if you need these features):
- 📧 Email variables (MAIL_*) - Only if sending emails
- 🤖 `ML_SERVICE_URL` - Only if you have external ML service

## 🔒 Security Notes

> [!CAUTION]
> **Never commit `.env` to Git!** It contains your actual passwords and secrets.

> [!WARNING]
> Your `.env` file contains real credentials. Make sure `.env` is in your `.gitignore` file.

## 🛠️ Local vs Production

| Aspect | Local Development | Render Production |
|--------|------------------|-------------------|
| **Where variables come from** | `.env` file | Render Environment Variables UI |
| **DEBUG mode** | `True` (in your .env) | `False` (set in Render) |
| **PORT** | `8000` (in your .env) | Auto-set by Render |
| **How to change** | Edit `.env` file | Update in Render dashboard |

## 📝 Summary

**For Render deployment, you need to:**

1. **Copy values from your `.env`** to Render's Environment Variables section
2. **Change `DEBUG` to `False`**
3. **Don't set `PORT`** - Render handles this
4. **Optionally skip email variables** if you don't need email functionality yet

**The `.env.example` file is just a template** - it shows what variables exist but with fake values. Use your actual values from `.env` when deploying to Render.
