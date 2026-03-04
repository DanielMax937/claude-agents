#!/usr/bin/env python3
"""
Gmail Alerts Fetcher (Auto-Auth + High Performance)

1. Tries to connect using existing token.
2. If token is dead/missing, OPENS BROWSER to authenticate.
3. Once authenticated, fetches latest 6 alerts and outputs JSON.
"""

import os
import sys
import json
import socket
import base64
import re
import gzip
import concurrent.futures
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import ssl

# --- DEPENDENCIES FOR AUTH ---
# pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# --- CONFIG ---
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SKILL_DIR = Path('/Users/daniel/.claude/skills/gmail-reader') # Adjust if needed
TOKEN_PATH = SKILL_DIR / 'token.json'
CREDENTIALS_PATH = SKILL_DIR / 'credentials.json'
TIMEOUT = 10
MAX_EMAILS = 6


# --- FORCE IPv4 (Fixes macOS/Python Network Hangs) ---
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return socket.orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


if hasattr(socket, 'getaddrinfo'):
    socket.orig_getaddrinfo = socket.getaddrinfo
    socket.getaddrinfo = getaddrinfo_ipv4


# -----------------------------------------------------

def log(msg):
    """Print to stderr so it doesn't mess up JSON output"""
    print(msg, file=sys.stderr)


def get_valid_credentials():
    """
    Handles the Authentication Logic.
    Returns: A valid Access Token string.
    """
    creds = None

    # 1. Load existing token
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            log("⚠️ Token file is corrupt. Re-authenticating...")

    # 2. Check validity
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log("🔄 Token expired. Refreshing...")
            try:
                creds.refresh(GoogleRequest())
            except Exception:
                log("⚠️ Refresh failed. Re-authenticating...")
                creds = None  # Force re-auth

        # 3. If still no valid creds, open browser
        if not creds:
            if not CREDENTIALS_PATH.exists():
                log(f"❌ Error: credentials.json not found at {CREDENTIALS_PATH}")
                log("   Please download it from Google Cloud Console.")
                sys.exit(1)

            log("🔓 Launching browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

            # Save the new token
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
            log(f"✓ New credentials saved to {TOKEN_PATH}")

    return creds.token


# --- FAST API CLIENT (Raw HTTP) ---

def gmail_api_get(endpoint, access_token, params=None):
    if params:
        query_string = urlencode(params)
        url = f'https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}?{query_string}'
    else:
        url = f'https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}'

    req = Request(url)
    req.add_header('Authorization', f'Bearer {access_token}')
    req.add_header('Accept-Encoding', 'gzip')

    context = ssl._create_unverified_context()
    response = urlopen(req, timeout=TIMEOUT, context=context)

    data = response.read()
    if response.info().get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)

    return json.loads(data.decode('utf-8'))


def extract_text_from_payload(payload):
    if not payload: return ""
    if 'body' in payload and 'data' in payload['body']:
        try:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        except:
            pass
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                try:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                except:
                    pass
            text = extract_text_from_payload(part)
            if text: return text
    return ""


def parse_alert_items(text):
    if not text: return []

    # Remove footer
    separator_pattern = r'(- ){5,}.*'
    match = re.search(separator_pattern, text, re.DOTALL)
    if match: text = text[:match.start()]

    items = []
    pattern = re.compile(
        r'(?P<title>\S[^\n]*)\n'  # Title
        r'(?P<source>\S[^\n]*)\n'  # Source
        r'(?P<summary>[\s\S]*?)'  # Summary
        r'\n<(?P<link>https?://[^>]+)>',  # Link
        re.MULTILINE
    )

    for match in pattern.finditer(text):
        title = match.group('title').strip()
        summary = match.group('summary').replace('\n', ' ').strip()
        if len(title) > 3:
            items.append({
                'title': title,
                'source': match.group('source').strip(),
                'summary': summary,
                'link': match.group('link').strip()
            })
    return items


def process_message(msg_id, access_token):
    try:
        raw_msg = gmail_api_get(f'messages/{msg_id}', access_token, {
            'format': 'full',
            'fields': 'id,payload(headers,body,parts)'
        })
        headers = {h['name']: h['value'] for h in raw_msg['payload'].get('headers', [])}
        raw_body = extract_text_from_payload(raw_msg['payload'])
        news_items = parse_alert_items(raw_body)

        if not news_items: return None

        return {
            "id": msg_id,
            "subject": headers.get('Subject', 'No Subject'),
            "date": headers.get('Date', ''),
            "items": news_items
        }
    except Exception as e:
        # log(f"Error processing {msg_id}: {e}")
        return None


# --- MAIN FLOW ---

def main():
    log("--- STARTING SMART FETCH ---")

    # 1. AUTHENTICATE (Auto-Browser if needed)
    log("🔐 Checking credentials...")
    try:
        access_token = get_valid_credentials()
        log("✓ Authenticated")
    except Exception as e:
        log(f"❌ Auth Failed: {e}")
        sys.exit(1)

    # 2. SEARCH
    log(f"📧 Searching latest {MAX_EMAILS} alerts...")
    query = 'from:googlealerts-noreply@google.com'
    try:
        messages_result = gmail_api_get('messages', access_token, {
            'q': query,
            'maxResults': MAX_EMAILS
        })
    except Exception as e:
        log(f"❌ API Call Failed: {e}")
        sys.exit(1)

    messages = messages_result.get('messages', [])
    log(f"   Found {len(messages)} emails")

    if not messages:
        print("[]")
        return

    # 3. FETCH PARALLEL
    log(f"📥 Fetching & Parsing...")
    final_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_EMAILS) as executor:
        future_to_msg = {
            executor.submit(process_message, msg['id'], access_token): msg
            for msg in messages
        }
        for future in concurrent.futures.as_completed(future_to_msg):
            try:
                data = future.result()
                if data: final_data.append(data)
            except Exception:
                pass

    log("✓ Done. Outputting JSON...")
    print(json.dumps(final_data, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log("\n🛑 Script cancelled by user.")
    except Exception as e:
        log(f"Fatal Error: {e}")