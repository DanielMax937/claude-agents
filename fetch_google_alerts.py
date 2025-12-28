#!/usr/bin/env python3
"""
Fetch Google Alerts emails from today

This script fetches emails from googlealerts-noreply@google.com sent today
and displays them in a clean, readable format.
"""

import json
import base64
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import ssl

# Path to Gmail token
TOKEN_PATH = Path.home() / '.claude/skills/gmail-reader/token.json'


def refresh_access_token():
    """Refresh the access token using refresh token"""
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)

    data = urlencode({
        'refresh_token': token_data['refresh_token'],
        'client_id': token_data['client_id'],
        'client_secret': token_data['client_secret'],
        'grant_type': 'refresh_token'
    }).encode()

    req = Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        method='POST'
    )
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    response = urlopen(req, timeout=30, context=ssl._create_unverified_context())
    result = json.loads(response.read().decode())

    return result['access_token']


def gmail_api_get(endpoint, access_token, params=None):
    """Make a GET request to Gmail API"""
    if params:
        query_string = urlencode(params)
        url = f'https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}?{query_string}'
    else:
        url = f'https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}'

    req = Request(url)
    req.add_header('Authorization', f'Bearer {access_token}')

    response = urlopen(req, timeout=30, context=ssl._create_unverified_context())
    return json.loads(response.read().decode())


def extract_text_from_payload(payload):
    """Extract plain text email body from Gmail payload"""
    # Try direct body first
    if 'body' in payload and 'data' in payload['body']:
        try:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        except:
            pass

    # Recursively search parts for plain text
    if 'parts' in payload:
        for part in payload['parts']:
            # Prefer plain text over HTML
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                try:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                except:
                    pass

            # Recurse into nested parts
            text = extract_text_from_payload(part)
            if text:
                return text

    return ""


def format_email(message):
    """Format email message for display"""
    # Extract headers
    headers = {h['name']: h['value'] for h in message['payload']['headers']}

    subject = headers.get('Subject', 'No Subject')
    from_email = headers.get('From', 'Unknown')
    date = headers.get('Date', 'Unknown')
    body = extract_text_from_payload(message['payload'])

    return f"""
{'='*70}
Subject: {subject}
From: {from_email}
Date: {date}
{'='*70}

{body}
"""


def fetch_google_alerts_today():
    """Fetch Google Alerts emails from today"""

    # Get today's date in YYYY/MM/DD format
    today = datetime.now().strftime('%Y/%m/%d')

    print(f"🔍 Fetching Google Alerts from {today}...")
    print()

    # Refresh access token
    print("🔐 Authenticating...")
    access_token = refresh_access_token()
    print("✓ Authenticated")
    print()

    # Search for Google Alerts from today
    query = f'from:googlealerts-noreply@google.com after:{today}'

    print(f"📧 Searching for messages: {query}")
    messages_result = gmail_api_get('messages', access_token, {
        'q': query,
        'maxResults': 20
    })

    messages = messages_result.get('messages', [])
    print(f"✓ Found {len(messages)} messages")
    print()

    if not messages:
        print("No Google Alerts found for today.")
        return

    # Fetch full details for each message
    for i, msg in enumerate(messages, 1):
        print(f"📥 Fetching message {i}/{len(messages)}...")
        full_message = gmail_api_get(f'messages/{msg["id"]}', access_token, {
            'format': 'full'
        })
        print(f"✓ Retrieved")

        # Display formatted email
        print(format_email(full_message))
        print()

if __name__ == '__main__':
    try:
        fetch_google_alerts_today()
    except FileNotFoundError:
        print("❌ Error: Token file not found")
        print(f"   Expected at: {TOKEN_PATH}")
        print("\nPlease run the Gmail skill setup first:")
        print("  cd ~/.claude/skills/gmail-reader")
        print("  python scripts/setup_auth.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
