"""
Run this ONCE locally to get Google OAuth refresh token.
Then add the output to Streamlit Cloud secrets.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.modify'
]

if __name__ == '__main__':
    if not os.path.exists('credentials.json'):
        print("ERROR: credentials.json not found!")
        print("Download from Google Cloud Console > APIs & Services > Credentials")
        exit(1)
    
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    print("\n" + "="*60)
    print("COPY THESE TO STREAMLIT CLOUD SECRETS:")
    print("="*60)
    print(f'GOOGLE_CLIENT_ID = "{creds.client_id}"')
    print(f'GOOGLE_CLIENT_SECRET = "{creds.client_secret}"')
    print(f'GOOGLE_REFRESH_TOKEN = "{creds.refresh_token}"')
    print("="*60)
    print("\nIn Streamlit Cloud: Settings > Secrets > paste above")