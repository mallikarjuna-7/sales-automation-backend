# 🚀 Quick Start: Gmail API Setup

## What You Need to Do Right Now

### 1️⃣ Get Your Gmail API Credentials (5-10 minutes)

**Go to:** https://console.cloud.google.com/

1. **Create/Select Project** → Click "Select a project" → "New Project"
   - Name: "Sales Automation" (or any name)
   - Click "Create"

2. **Enable Gmail API**
   - Click "APIs & Services" → "Library"
   - Search: "Gmail API"
   - Click on it → Click "Enable"

3. **Configure OAuth Consent Screen** (if not done)
   - Click "APIs & Services" → "OAuth consent screen"
   - Choose "External" → Click "Create"
   - Fill in:
     - App name: "Sales Automation"
     - User support email: smallikarjun713@gmail.com
     - Developer email: smallikarjun713@gmail.com
   - Click "Save and Continue"
   - **Scopes**: Click "Add or Remove Scopes"
     - Search for: `gmail.send`
     - Check: `https://www.googleapis.com/auth/gmail.send`
     - Click "Update" → "Save and Continue"
   - **Test users**: Click "Add Users"
     - Add: smallikarjun713@gmail.com
     - Click "Save and Continue"

4. **Create Credentials**
   - Click "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Sales Automation Desktop"
   - Click "Create"
   - Click "Download JSON" (this is your `credentials.json`)
   - Save it to: `c:\Users\sajja\Desktop\sales-automation\sales-automation-backend\credentials.json`

### 2️⃣ Generate Your Refresh Token (2 minutes)

**Open PowerShell/Terminal in your backend directory:**

```powershell
cd c:\Users\sajja\Desktop\sales-automation\sales-automation-backend
python generate_gmail_token.py
```

**What happens:**
- A browser window opens
- Sign in with: **smallikarjun713@gmail.com**
- Click "Allow" when asked for permissions
- The script will print your credentials

**Copy the output** - it will look like this:

```
GMAIL_CLIENT_ID=123456789.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-abc123xyz
GMAIL_REFRESH_TOKEN=1//0abc123xyz...
GMAIL_SENDER=smallikarjun713@gmail.com
MAIL_FROM_NAME=Sales Automation
```

### 3️⃣ Update Your .env File (1 minute)

**Open:** `c:\Users\sajja\Desktop\sales-automation\sales-automation-backend\.env`

**Replace these lines:**
```env
GMAIL_CLIENT_ID=your_client_id_from_credentials.json
GMAIL_CLIENT_SECRET=your_client_secret_from_credentials.json
GMAIL_REFRESH_TOKEN=your_generated_refresh_token
```

**With the actual values from step 2** ☝️

### 4️⃣ Test It! (1 minute)

**Start your server:**
```powershell
cd c:\Users\sajja\Desktop\sales-automation\sales-automation-backend
uvicorn app.main:app --reload --port 8000
```

**Send a test email** (in a new terminal):
```powershell
curl -X POST "http://localhost:8000/api/emails/send" -H "Content-Type: application/json" -d "{\"sender\": \"smallikarjun713@gmail.com\", \"receiver\": \"your-email@example.com\", \"subject\": \"Test\", \"body\": \"It works!\"}"
```

**Or use the Swagger UI:**
- Open: http://localhost:8000/docs
- Find: `POST /api/emails/send`
- Click "Try it out"
- Fill in the test data
- Click "Execute"

---

## ✅ Success Checklist

- [ ] Downloaded `credentials.json` from Google Cloud Console
- [ ] Placed `credentials.json` in backend directory
- [ ] Ran `python generate_gmail_token.py`
- [ ] Signed in with smallikarjun713@gmail.com
- [ ] Copied the credentials output
- [ ] Updated `.env` file with real values
- [ ] Started the backend server
- [ ] Sent a test email successfully

---

## 🆘 Common Issues

### "credentials.json not found"
→ Make sure you downloaded it from Google Cloud Console and placed it in the backend directory

### "Access blocked: This app's request is invalid"
→ Make sure you added smallikarjun713@gmail.com as a test user in OAuth consent screen

### "Invalid grant"
→ Run `python generate_gmail_token.py` again to get a fresh token

### "Module not found: google_auth_oauthlib"
→ Run: `pip install google-auth-oauthlib`

---

## 📚 More Help

- **Detailed Setup Guide:** See `GMAIL_SETUP_GUIDE.md`
- **All Changes Made:** See `GMAIL_MIGRATION_SUMMARY.md`
- **Token Generator Script:** `generate_gmail_token.py`

---

## 🎯 That's It!

Once you complete these 4 steps, your app will send emails through Gmail API instead of Resend! 🎉
