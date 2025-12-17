"""
Gmail Email Fetcher
Authenticat with Gmail API and fetches emails within a date range.
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import base64
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth 2.0."""
    creds = None
    token_path = 'token.json'
    credentials_path = 'credentials.json'

    # Load existing token if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds

def build_date_query(start_date, end_date, include_status='all'):
    """
    Build Gmail search query for date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        include_status: 'all', 'read', or 'unread'

    Returns:
        Gmail query string
    """
    query_parts = [
        f'after:{start_date}',
        f'before:{end_date}'
    ]

    if include_status == 'read':
        query_parts.append('is:read')
    elif include_status == 'unread':
        query_parts.append('is:unread')

    return ' '.join(query_parts)

def get_email_body(payload):
    """Extract email body from message payload."""
    body = ""

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

    return body

def get_attachments_info(payload):
    """Extract attachment information from message payload."""
    attachments = []

    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('filename'):
                attachment = {
                    'filename': part['filename'],
                    'mimeType': part['mimeType'],
                    'attachmentId': part['body'].get('attachmentId'),
                    'size': part['body'].get('size', 0)
                }
                attachments.append(attachment)

    return attachments

def fetch_emails(start_date, end_date, include_status='all', max_results=500):
    """
    Fetch emails from Gmail within date range.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        include_status: 'all', 'read', or 'unread'
        max_results: Maximum number of emails to fetch

    Returns:
        List of email objects with metadata
    """
    print(f"Authenticating with Gmail...")
    creds = authenticate_gmail()

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Build search query
        query = build_date_query(start_date, end_date, include_status)
        print(f"Search query: {query}")

        # Get list of message IDs
        print(f"Fetching message IDs...")
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            print("No messages found.")
            return []

        print(f"Found {len(messages)} messages. Fetching details...")

        # Fetch full message details
        emails = []
        for i, msg in enumerate(messages, 1):
            print(f"Fetching message {i}/{len(messages)}...", end='\r')

            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            # Build email object
            email_obj = {
                'id': message['id'],
                'threadId': message['threadId'],
                'labelIds': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
                'subject': headers.get('Subject', '(No Subject)'),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'date': headers.get('Date', ''),
                'body': get_email_body(message['payload']),
                'attachments': get_attachments_info(message['payload'])
            }

            emails.append(email_obj)

        print(f"\nSuccessfully fetched {len(emails)} emails.")
        return emails

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def save_emails_cache(emails, output_path='.tmp/emails_cache.json'):
    """Save fetched emails to cache file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'count': len(emails),
            'emails': emails
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(emails)} emails to {output_path}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python fetch_emails.py START_DATE END_DATE [STATUS]")
        print("Example: python fetch_emails.py 2024-01-01 2024-01-31 all")
        sys.exit(1)

    start = sys.argv[1]
    end = sys.argv[2]
    status = sys.argv[3] if len(sys.argv) > 3 else 'all'

    emails = fetch_emails(start, end, status)
    save_emails_cache(emails)
