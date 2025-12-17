"""
Email Categorization Script
Categorizes emails using LLM.
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import sys
import json
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

CATEGORIES = {
    'advertising': 'Marketing, promotional content, newsletters, spam',
    'invoice': 'Bills, invoices, payment requests, receipts, financial statements',
    'important_update': 'Product updates, service changes, critical notifications, account alerts',
    'new_client_inquiry': 'First-time contact, new business opportunities, quote requests',
    'existing_client': 'Ongoing conversations with known clients, project communications',
    'other': 'Everything else that doesn\'t fit the above categories'
}

def load_emails_cache(cache_path='.tmp/emails_cache.json'):
    """

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

Load cached emails."""
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Email cache not found at {cache_path}")

    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['emails']

def categorize_with_anthropic(email_data, api_key):
    """Categorize email using Anthropic Claude."""
    client = Anthropic(api_key=api_key)

    # Build email context
    email_text = f"""
Subject: {email_data['subject']}
From: {email_data['from']}
Date: {email_data['date']}
Snippet: {email_data['snippet']}

Body (first 1000 chars):
{email_data['body'][:1000]}

Attachments: {', '.join([att['filename'] for att in email_data['attachments']])}
"""

    categories_list = '\n'.join([f"- {k}: {v}" for k, v in CATEGORIES.items()])

    prompt = f"""You are an email categorization assistant. Categorize the following email into ONE of these categories:

{categories_list}

Email to categorize:
{email_text}

Respond with ONLY the category name (e.g., "invoice" or "new_client_inquiry"). No explanations."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )

        category = message.content[0].text.strip().lower()

        # Validate category
        if category not in CATEGORIES:
            print(f"Warning: Invalid category '{category}', defaulting to 'other'")
            category = 'other'

        return category

    except Exception as e:
        print(f"Anthropic API error: {e}")
        return None

def categorize_with_openai(email_data, api_key):
    """Categorize email using OpenAI (fallback)."""
    client = OpenAI(api_key=api_key)

    # Build email context
    email_text = f"""
Subject: {email_data['subject']}
From: {email_data['from']}
Date: {email_data['date']}
Snippet: {email_data['snippet']}

Body (first 1000 chars):
{email_data['body'][:1000]}

Attachments: {', '.join([att['filename'] for att in email_data['attachments']])}
"""

    categories_list = '\n'.join([f"- {k}: {v}" for k, v in CATEGORIES.items()])

    prompt = f"""You are an email categorization assistant. Categorize the following email into ONE of these categories:

{categories_list}

Email to categorize:
{email_text}

Respond with ONLY the category name (e.g., "invoice" or "new_client_inquiry"). No explanations."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )

        category = response.choices[0].message.content.strip().lower()

        # Validate category
        if category not in CATEGORIES:
            print(f"Warning: Invalid category '{category}', defaulting to 'other'")
            category = 'other'

        return category

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def categorize_emails(emails, use_anthropic=False):
    """
    Categorize all emails using LLM.

    Args:
        emails: List of email objects
        use_anthropic: Use Anthropic Claude (True) or OpenAI (False)

    Returns:
        List of emails with 'category' field added
    """
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    if use_anthropic and not anthropic_key:
        print("Warning: ANTHROPIC_API_KEY not found, falling back to OpenAI")
        use_anthropic = False

    if not use_anthropic and not openai_key:
        raise ValueError("No valid API keys found in .env file")

    categorized = []
    total = len(emails)

    for i, email in enumerate(emails, 1):
        print(f"Categorizing email {i}/{total}: {email['subject'][:50]}...", end='\r')

        # Try primary LLM
        if use_anthropic:
            category = categorize_with_anthropic(email, anthropic_key)
        else:
            category = categorize_with_openai(email, openai_key)

        # Fallback to other LLM if primary fails
        if category is None:
            print(f"\nPrimary LLM failed, trying fallback...")
            if use_anthropic and openai_key:
                category = categorize_with_openai(email, openai_key)
            elif not use_anthropic and anthropic_key:
                category = categorize_with_anthropic(email, anthropic_key)

        # Last resort: mark as 'other'
        if category is None:
            print(f"\nWarning: Could not categorize email {email['id']}, marking as 'other'")
            category = 'other'

        email['category'] = category
        categorized.append(email)

    print(f"\nSuccessfully categorized {len(categorized)} emails.")
    return categorized

def save_categorization_results(emails, output_path='.tmp/categorization_results.json'):
    """Save categorized emails to file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate category counts
    category_counts = {}
    for email in emails:
        cat = email.get('category', 'other')
        category_counts[cat] = category_counts.get(cat, 0) + 1

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_emails': len(emails),
            'category_counts': category_counts,
            'emails': emails
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved categorization results to {output_path}")
    print("\nCategory breakdown:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")

if __name__ == '__main__':
    import sys

    # Load cached emails
    emails = load_emails_cache()
    print(f"Loaded {len(emails)} emails from cache.")

    # Categorize (default to OpenAI)
    use_anthropic = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'openai':
        use_anthropic = False

    categorized_emails = categorize_emails(emails, use_anthropic=use_anthropic)

    # Save results
    save_categorization_results(categorized_emails)
