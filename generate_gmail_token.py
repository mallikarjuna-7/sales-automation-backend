"""
Gmail API Token Generator
This script helps you generate a refresh token for Gmail API authentication.

Prerequisites:
1. Download credentials.json from Google Cloud Console
2. Place it in the same directory as this script
3. Install required packages: pip install google-auth-oauthlib

Usage:
    python generate_gmail_token.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import os
import sys

# Define the scopes - we only need to send emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Path to your credentials.json file
CREDENTIALS_FILE = 'credentials.json'

def get_refresh_token():
    """Generate a refresh token for Gmail API"""
    
    # Check if credentials.json exists
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ Error: credentials.json not found!")
        print("\nPlease follow these steps:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create OAuth 2.0 credentials (Desktop app)")
        print("3. Download the credentials.json file")
        print("4. Place it in the same directory as this script")
        print(f"   Current directory: {os.getcwd()}")
        sys.exit(1)
    
    print("🔐 Starting Gmail API authentication...")
    print("📝 A browser window will open for you to sign in with your Gmail account")
    print(f"   Use: smallikarjun713@gmail.com\n")
    
    try:
        # Create the flow using the client secrets file
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, 
            SCOPES
        )
        
        # Run the OAuth flow - this will open a browser window
        creds = flow.run_local_server(port=0)
        
        # Extract the values we need
        client_id = creds.client_id
        client_secret = creds.client_secret
        refresh_token = creds.refresh_token
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Your Gmail API credentials are ready!")
        print("="*60)
        print("\n📋 Copy these values to your .env file:\n")
        print(f"GMAIL_CLIENT_ID={client_id}")
        print(f"GMAIL_CLIENT_SECRET={client_secret}")
        print(f"GMAIL_REFRESH_TOKEN={refresh_token}")
        print(f"GMAIL_SENDER=smallikarjun713@gmail.com")
        print(f"MAIL_FROM_NAME=Sales Automation")
        print("\n" + "="*60)
        print("\n💡 Tip: Keep these credentials secure and never commit them to git!")
        
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token
        }
        
    except Exception as e:
        print(f"\n❌ Error during authentication: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you've enabled Gmail API in Google Cloud Console")
        print("2. Verify your OAuth consent screen is configured")
        print("3. Add your email as a test user if the app is in testing mode")
        print("4. Check that the scope 'https://www.googleapis.com/auth/gmail.send' is added")
        sys.exit(1)

if __name__ == '__main__':
    print("="*60)
    print("Gmail API Refresh Token Generator")
    print("="*60)
    print()
    get_refresh_token()
