# Gmail API Migration Summary

## ✅ Changes Completed

### 1. **Dependencies Updated**
- ✅ Removed: `resend>=0.8.0`
- ✅ Added: 
  - `google-auth>=2.16.0`
  - `google-auth-oauthlib>=1.0.0`
  - `google-auth-httplib2>=0.1.0`
  - `google-api-python-client>=2.0.0`

### 2. **Environment Variables Updated** (`.env`)
**Old (Resend):**
```env
RESEND_API_KEY=re_VjvKjZBn_A2PhkAH2TqGtREVaYk4kGn91
MAIL_FROM=onboarding@resend.dev
MAIL_FROM_NAME=Sales Automation
```

**New (Gmail API):**
```env
GMAIL_CLIENT_ID=your_client_id_from_credentials.json
GMAIL_CLIENT_SECRET=your_client_secret_from_credentials.json
GMAIL_REFRESH_TOKEN=your_generated_refresh_token
GMAIL_SENDER=smallikarjun713@gmail.com
MAIL_FROM_NAME=Sales Automation
```

### 3. **Configuration Updated** (`app/core/config.py`)
- ✅ Replaced `RESEND_API_KEY`, `MAIL_FROM` with Gmail API settings
- ✅ Added: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_SENDER`

### 4. **Email Service Rewritten** (`app/services/email_service.py`)
- ✅ Removed Resend API integration
- ✅ Implemented Gmail API with OAuth2 authentication
- ✅ Added `get_gmail_service()` function for API authentication
- ✅ Added `create_message()` function for MIME message creation
- ✅ Updated `send_outreach_email()` to use Gmail API
- ✅ Maintained all existing database operations and error handling

### 5. **Security Enhanced** (`.gitignore`)
- ✅ Added `credentials.json` to prevent committing OAuth credentials
- ✅ Added `token.json` to prevent committing access tokens

### 6. **Documentation Created**
- ✅ `GMAIL_SETUP_GUIDE.md` - Complete setup instructions
- ✅ `generate_gmail_token.py` - Token generation script
- ✅ `GMAIL_MIGRATION_SUMMARY.md` - This file

---

## 🚀 Next Steps (Action Required)

### Step 1: Get Gmail API Credentials

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create/Select a project**
3. **Enable Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Configure OAuth consent screen if needed
   - Choose "Desktop app" as application type
   - Download the `credentials.json` file

### Step 2: Generate Refresh Token

1. **Place `credentials.json`** in your backend directory:
   ```
   c:\Users\sajja\Desktop\sales-automation\sales-automation-backend\
   ```

2. **Run the token generator**:
   ```bash
   python generate_gmail_token.py
   ```

3. **Follow the prompts**:
   - A browser will open
   - Sign in with `smallikarjun713@gmail.com`
   - Grant the requested permissions
   - Copy the output credentials

### Step 3: Update .env File

Replace the placeholder values in `.env` with your actual credentials:

```env
GMAIL_CLIENT_ID=<your_actual_client_id>
GMAIL_CLIENT_SECRET=<your_actual_client_secret>
GMAIL_REFRESH_TOKEN=<your_actual_refresh_token>
GMAIL_SENDER=smallikarjun713@gmail.com
MAIL_FROM_NAME=Sales Automation
```

### Step 4: Test the Integration

**Start your backend server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Send a test email:**
```bash
curl -X POST "http://localhost:8000/api/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "smallikarjun713@gmail.com",
    "receiver": "your-test-email@example.com",
    "subject": "Test Email from Gmail API",
    "body": "This is a test email to verify Gmail API integration is working!"
  }'
```

---

## 📝 Important Notes

### Gmail Sending Limits
- **Free Gmail**: ~500 emails/day
- **Google Workspace**: ~2000 emails/day

### OAuth Consent Screen
- If in "Testing" mode, only test users can authenticate
- For production, you'll need to verify your app

### Security Best Practices
- ✅ Never commit `credentials.json` to git (already in `.gitignore`)
- ✅ Never commit `.env` file to git (already in `.gitignore`)
- ✅ Keep your refresh token secure
- ✅ Rotate credentials if compromised

### Refresh Token Expiration
The refresh token will expire if:
- User revokes access
- Not used for 6 months
- User changes password
- Token limit exceeded (50 per user per client)

---

## 🔧 Code Changes Summary

### Files Modified:
1. ✅ `requirements.txt` - Updated dependencies
2. ✅ `.env` - Updated environment variables
3. ✅ `app/core/config.py` - Updated configuration
4. ✅ `app/services/email_service.py` - Rewritten for Gmail API
5. ✅ `.gitignore` - Added credential files

### Files Created:
1. ✅ `GMAIL_SETUP_GUIDE.md` - Setup instructions
2. ✅ `generate_gmail_token.py` - Token generator script
3. ✅ `GMAIL_MIGRATION_SUMMARY.md` - This summary

### No Changes Required:
- ✅ `app/api/emails.py` - API endpoints remain the same
- ✅ `app/models/email.py` - Email model unchanged
- ✅ `app/schemas/email.py` - Email schemas unchanged
- ✅ Database operations - All preserved

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] Gmail API enabled in Google Cloud Console
- [ ] OAuth 2.0 credentials created and downloaded
- [ ] Refresh token generated using `generate_gmail_token.py`
- [ ] `.env` file updated with actual credentials
- [ ] Test email sent successfully
- [ ] `credentials.json` NOT committed to git
- [ ] `.env` file NOT committed to git
- [ ] Backend server starts without errors
- [ ] Email sending works in development
- [ ] Environment variables set in production (Render)

---

## 🆘 Troubleshooting

### "Access blocked: This app's request is invalid"
- Ensure Gmail API is enabled
- Add your email as a test user in OAuth consent screen

### "Invalid grant" error
- Refresh token expired - regenerate it
- Check client ID and secret are correct

### "Insufficient Permission" error
- Verify scope `https://www.googleapis.com/auth/gmail.send` is included
- Re-run the token generation script

### Import errors
- Run: `pip install -r requirements.txt`
- Ensure all Google packages are installed

---

## 📞 Support

For detailed setup instructions, see: `GMAIL_SETUP_GUIDE.md`

For token generation help, run: `python generate_gmail_token.py`
