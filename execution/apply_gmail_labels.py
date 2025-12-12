"""
nimport sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
Gmail Label Manager
Creates and applies labels to categorized emails.
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Label mapping
LABEL_MAP = {
    'advertising': 'Email-Assistant/Advertising',
    'invoice': 'Email-Assistant/Invoice',
    'important_update': 'Email-Assistant/Important-Update',
    'new_client_inquiry': 'Email-Assistant/New-Client',
    'existing_client': 'Email-Assistant/Existing-Client',
    'other': 'Email-Assistant/Other'
}

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

def get_or_create_label(service, label_path):
    """
    Get existing label or create if it doesn't exist.

    Args:
        service: Gmail API service
        label_path: Hierarchical label path (e.g., 'Email-Assistant/Invoice')

    Returns:
        Label ID
    """
    try:
        # List all labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        # Check if label exists
        for label in labels:
            if label['name'] == label_path:
                return label['id']

        # Label doesn't exist, create it
        print(f"  Creating label: {label_path}")

        label_object = {
            'name': label_path,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }

        created_label = service.users().labels().create(
            userId='me',
            body=label_object
        ).execute()

        return created_label['id']

    except HttpError as error:
        print(f"  Error with label '{label_path}': {error}")
        return None

def apply_label_to_email(service, email_id, label_id):
    """Apply label to an email."""
    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'addLabelIds': [label_id]}
        ).execute()

        return True

    except HttpError as error:
        print(f"  Error applying label to email {email_id}: {error}")
        return False

def apply_gmail_labels(emails):
    """
    Apply Gmail labels to categorized emails.

    Args:
        emails: List of categorized email objects

    Returns:
        Summary of labeling operations
    """
    service = get_gmail_service()

    # Get or create all label IDs
    print("Setting up Gmail labels...")
    label_ids = {}

    for category, label_path in LABEL_MAP.items():
        label_id = get_or_create_label(service, label_path)
        if label_id:
            label_ids[category] = label_id

    print(f"✓ {len(label_ids)} labels ready\n")

    # Apply labels to emails
    label_counts = {cat: 0 for cat in LABEL_MAP.keys()}
    errors = []

    for i, email in enumerate(emails, 1):
        category = email.get('category', 'other')
        subject = email['subject'][:50]

        print(f"Labeling {i}/{len(emails)}: {subject}...", end='\r')

        # Skip if already has Email-Assistant label (avoid reprocessing)
        existing_labels = email.get('labelIds', [])
        has_assistant_label = any(
            'Email-Assistant' in label for label in existing_labels
        )

        if has_assistant_label:
            print(f"Labeling {i}/{len(emails)}: {subject} [SKIP - already labeled]")
            continue

        # Apply label
        label_id = label_ids.get(category)

        if label_id:
            success = apply_label_to_email(service, email['id'], label_id)

            if success:
                label_counts[category] += 1
            else:
                errors.append({
                    'email_id': email['id'],
                    'subject': email['subject'],
                    'category': category
                })

    print(f"\n\n✓ Label application complete!")

    summary = {
        'total_processed': len(emails),
        'labels_applied': sum(label_counts.values()),
        'errors': len(errors),
        'by_category': label_counts
    }

    return summary, errors

def save_labeling_report(summary, errors):
    """Save labeling report."""
    os.makedirs('.tmp', exist_ok=True)

    report = {
        'summary': summary,
        'errors': errors
    }

    with open('.tmp/labeling_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nLabeling summary:")
    for category, count in summary['by_category'].items():
        if count > 0:
            print(f"  {LABEL_MAP[category]}: {count}")

    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred (see .tmp/labeling_report.json)")

if __name__ == '__main__':
    # Load categorized emails
    emails = load_categorized_emails()
    print(f"Loaded {len(emails)} categorized emails.\n")

    # Apply labels
    summary, errors = apply_gmail_labels(emails)

    # Save report
    save_labeling_report(summary, errors)
