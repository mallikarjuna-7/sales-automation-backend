# Gmail API Setup Guide

This guide will help you set up Gmail API credentials for sending emails from your application.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"

## Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required fields (app name, user support email, developer email)
   - Add your email to "Test users" if in testing mode
   - Add the scope: `https://www.googleapis.com/auth/gmail.send`
4. For Application type, choose "Desktop app"
5. Give it a name (e.g., "Sales Automation Email")
6. Click "Create"
7. Download the credentials JSON file - this is your `credentials.json`

## Step 3: Extract Client ID and Client Secret

Open the downloaded `credentials.json` file. It will look like this:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    ...
  }
}
```

Copy the `client_id` and `client_secret` values.

## Step 4: Generate Refresh Token

Run this Python script to generate your refresh token:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Path to your credentials.json file
CREDENTIALS_FILE = 'credentials.json'

def get_refresh_token():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE, 
        SCOPES
    )
    
    # This will open a browser window for authentication
    creds = flow.run_local_server(port=0)
    
    print("\n=== Your Refresh Token ===")
    print(creds.refresh_token)
    print("\n=== Copy this token to your .env file ===")
    
    return creds.refresh_token

if __name__ == '__main__':
    get_refresh_token()
```

**To run this script:**

1. Save it as `generate_token.py` in your backend directory
2. Place your `credentials.json` file in the same directory
3. Run: `python generate_token.py`
4. A browser window will open - sign in with your Gmail account (smallikarjun713@gmail.com)
5. Grant the requested permissions
6. Copy the refresh token that appears in the terminal

## Step 5: Update Your .env File

Update your `.env` file with the values:

```env
GMAIL_CLIENT_ID=your_client_id_from_credentials.json
GMAIL_CLIENT_SECRET=your_client_secret_from_credentials.json
GMAIL_REFRESH_TOKEN=your_generated_refresh_token
GMAIL_SENDER=smallikarjun713@gmail.com
MAIL_FROM_NAME=Sales Automation
```

## Step 6: Test Your Setup

You can test sending an email using your API endpoint:

```bash
curl -X POST "http://localhost:8000/api/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "smallikarjun713@gmail.com",
    "receiver": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email from Gmail API"
  }'
```

## Important Notes

1. **Gmail Sending Limits**: Gmail has sending limits:
   - Free Gmail accounts: ~500 emails/day
   - Google Workspace accounts: ~2000 emails/day

2. **OAuth Consent Screen**: If your app is in "Testing" mode, only test users you've added can authenticate. To send to anyone, you'll need to publish your app (requires verification for sensitive scopes).

3. **Refresh Token**: The refresh token doesn't expire unless:
   - The user revokes access
   - The token hasn't been used for 6 months
   - The user changes their password
   - You exceed the token limit (50 refresh tokens per user per client)

4. **Security**: Keep your `credentials.json`, client secret, and refresh token secure. Never commit them to version control.

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Make sure you've added the Gmail API scope in the OAuth consent screen
- Ensure your email is added as a test user

### "Invalid grant" error
- Your refresh token may have expired
- Regenerate the refresh token using the script above

### "Insufficient Permission" error
- Make sure you've enabled the Gmail API in your Google Cloud project
- Verify the scope `https://www.googleapis.com/auth/gmail.send` is included
