"""
Invoice Processing Script
Downloads invoice PDFs and logs invoice metadata.
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import base64
import re
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

INVOICE_DIR = os.getenv('INVOICE_DIR', 'invoices')

def load_categorized_emails(cache_path='.tmp/categorization_results.json'):
    """Load categorized emails."""
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Categorization results not found at {cache_path}")

    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['emails']

def get_gmail_service():
    """Get authenticated Gmail service."""
    token_path = 'token.json'

    if not os.path.exists(token_path):
        raise FileNotFoundError("Gmail token not found. Run fetch_emails.py first.")

    creds = Credentials.from_authorized_user_file(token_path)
    return build('gmail', 'v1', credentials=creds)

def download_attachment(service, user_id, msg_id, attachment_id, filename, output_dir):
    """Download email attachment."""
    try:
        attachment = service.users().messages().attachments().get(
            userId=user_id,
            messageId=msg_id,
            id=attachment_id
        ).execute()

        file_data = base64.urlsafe_b64decode(attachment['data'])

        # Save file
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        with open(output_path, 'wb') as f:
            f.write(file_data)

        print(f"  Downloaded: {filename}")
        return output_path

    except Exception as e:
        print(f"  Error downloading {filename}: {e}")
        return None

def extract_month_folder(email_date):
    """Extract YYYY-MM from email date for folder organization."""
    try:
        # Parse common date formats
        # Example: "Mon, 15 Jan 2024 10:30:00 +0000"
        date_str = email_date.split(',')[-1].strip() if ',' in email_date else email_date

        # Try to extract date
        for fmt in ['%d %b %Y', '%Y-%m-%d', '%d %B %Y']:
            try:
                dt = datetime.strptime(date_str.split()[0:3].__str__(), fmt)
                return dt.strftime('%Y-%m')
            except:
                continue

        # Fallback to current month
        return datetime.now().strftime('%Y-%m')

    except:
        return datetime.now().strftime('%Y-%m')

def is_invoice_email(email):
    """Check if email is likely an invoice (heuristics)."""
    # Keywords that indicate invoice
    invoice_keywords = [
        'invoice', 'bill', 'payment', 'receipt', 'statement',
        'due', 'amount', 'total', 'paid', 'balance'
    ]

    # Common invoice sender patterns
    invoice_senders = [
        'accounting@', 'billing@', 'invoices@', 'noreply@',
        'payments@', 'finance@', 'ar@'
    ]

    # Check subject and body
    text_to_check = f"{email['subject']} {email['snippet']} {email['from']}".lower()

    has_keyword = any(keyword in text_to_check for keyword in invoice_keywords)
    has_sender = any(sender in email['from'].lower() for sender in invoice_senders)

    return has_keyword or has_sender

def process_invoices(emails):
    """
    Process invoice emails - download PDFs and log metadata.

    Args:
        emails: List of categorized email objects

    Returns:
        Tuple of (invoice_log, dashboard_invoices_log)
    """
    service = get_gmail_service()

    invoice_emails = [e for e in emails if e.get('category') == 'invoice']
    print(f"Found {len(invoice_emails)} invoice emails to process.")

    invoice_log = []
    dashboard_invoices = []

    for i, email in enumerate(invoice_emails, 1):
        print(f"\nProcessing invoice {i}/{len(invoice_emails)}: {email['subject']}")

        # Determine month folder
        month_folder = extract_month_folder(email['date'])
        output_dir = os.path.join(INVOICE_DIR, month_folder)

        # Check for PDF attachments
        pdf_attachments = [
            att for att in email['attachments']
            if att['filename'].lower().endswith('.pdf')
        ]

        invoice_entry = {
            'email_id': email['id'],
            'subject': email['subject'],
            'from': email['from'],
            'date': email['date'],
            'month': month_folder,
            'attachments': []
        }

        if pdf_attachments:
            # Download PDFs
            print(f"  Found {len(pdf_attachments)} PDF attachment(s)")

            for att in pdf_attachments:
                downloaded_path = download_attachment(
                    service,
                    'me',
                    email['id'],
                    att['attachmentId'],
                    att['filename'],
                    output_dir
                )

                if downloaded_path:
                    invoice_entry['attachments'].append({
                        'filename': att['filename'],
                        'path': downloaded_path,
                        'size': att['size']
                    })

            invoice_log.append(invoice_entry)

        else:
            # No PDF - check if it's a dashboard-only invoice
            if is_invoice_email(email):
                print("  No PDF attachment - possible dashboard invoice")

                dashboard_entry = {
                    'email_id': email['id'],
                    'subject': email['subject'],
                    'from': email['from'],
                    'date': email['date'],
                    'snippet': email['snippet'],
                    'requires_manual_download': True
                }

                dashboard_invoices.append(dashboard_entry)
            else:
                print("  No PDF and low invoice confidence - skipping")

    return invoice_log, dashboard_invoices

def save_invoice_logs(invoice_log, dashboard_invoices):
    """Save invoice logs to files."""
    os.makedirs('.tmp', exist_ok=True)

    # Main invoice log
    with open('.tmp/invoice_log.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_invoices': len(invoice_log),
            'invoices': invoice_log
        }, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(invoice_log)} invoice records to .tmp/invoice_log.json")

    # Dashboard invoices log
    if dashboard_invoices:
        with open('.tmp/dashboard_invoices.json', 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_dashboard_invoices': len(dashboard_invoices),
                'message': 'These invoices require manual download from dashboards/portals',
                'invoices': dashboard_invoices
            }, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(dashboard_invoices)} dashboard invoice records to .tmp/dashboard_invoices.json")
        print("\n⚠️  ACTION REQUIRED: Review dashboard_invoices.json for manual downloads")

if __name__ == '__main__':
    # Load categorized emails
    emails = load_categorized_emails()
    print(f"Loaded {len(emails)} categorized emails.")

    # Process invoices
    invoice_log, dashboard_invoices = process_invoices(emails)

    # Save logs
    save_invoice_logs(invoice_log, dashboard_invoices)

    print(f"\n✓ Invoice processing complete!")
    print(f"  PDFs downloaded: {len(invoice_log)}")
    print(f"  Dashboard invoices: {len(dashboard_invoices)}")
