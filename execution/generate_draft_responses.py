"""
Draft Response Generator
Creates draft responses for client inquiries and communications.
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_categorized_emails(cache_path='.tmp/categorization_results.json'):
    """Load categorized emails."""
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Categorization results not found at {cache_path}")

    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['emails']

def extract_sender_email(from_field):
    """Extract email address from 'From' field."""
    # Extract email from formats like: "John Doe <john@example.com>" or "john@example.com"
    match = re.search(r'<(.+?)>', from_field)
    if match:
        return match.group(1).strip().lower()
    return from_field.strip().lower()

def load_client_context(sender_email):
    """Load existing client context if available."""
    context_dir = f"client_contexts/{sender_email}"
    context_file = os.path.join(context_dir, 'context.json')

    if os.path.exists(context_file):
        with open(context_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    return None

def generate_new_client_response(email, openai_key):
    """Generate response for new client inquiry."""
    client = OpenAI(api_key=openai_key)

    email_context = f"""
Subject: {email['subject']}
From: {email['from']}
Date: {email['date']}

Email body:
{email['body'][:2000]}
"""

    prompt = f"""You are a professional business assistant drafting a response to a new client inquiry.

The client sent this email:
{email_context}

Write a professional, warm, and helpful response that:
1. Thanks them for reaching out
2. Acknowledges their specific inquiry or question
3. Asks 1-2 clarifying questions to better understand their needs
4. Suggests next steps (e.g., scheduling a call, providing more information)
5. Keeps it concise (2-3 paragraphs max)

Draft the email response (do not include subject line or greeting with their name - just the body):"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"  Error generating response: {e}")
        return None

def generate_existing_client_response(email, context, openai_key):
    """Generate response for existing client communication."""
    client = OpenAI(api_key=openai_key)

    # Build context summary
    context_summary = f"""
Client: {context.get('client_name', 'Unknown')}
Project: {context.get('project_summary', 'No project info')}

Recent communications:
"""

    # Add last 3 communications
    for comm in context.get('communications', [])[-3:]:
        context_summary += f"- {comm.get('date', 'N/A')}: {comm.get('topic', 'N/A')}\n"

    if context.get('action_items'):
        context_summary += f"\nPending action items:\n"
        for item in context['action_items']:
            if item.get('status') != 'completed':
                context_summary += f"- {item.get('description', 'N/A')}\n"

    email_context = f"""
Subject: {email['subject']}
From: {email['from']}
Date: {email['date']}

Email body:
{email['body'][:2000]}
"""

    prompt = f"""You are a professional business assistant drafting a response to an existing client.

Client context:
{context_summary}

They sent this email:
{email_context}

Write a professional response that:
1. References relevant project context
2. Addresses their specific message or question
3. Provides clear next steps or updates
4. Mentions any pending action items if relevant
5. Keeps it concise and focused

Draft the email response (do not include subject line or greeting - just the body):"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"  Error generating response: {e}")
        return None

def generate_draft_responses(emails):
    """
    Generate draft responses for client inquiries and communications.

    Args:
        emails: List of categorized email objects

    Returns:
        List of draft objects
    """
    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    # Filter emails that need responses
    client_emails = [
        e for e in emails
        if e.get('category') in ['new_client_inquiry', 'existing_client']
    ]

    print(f"Found {len(client_emails)} client emails requiring draft responses.")

    drafts = []

    for i, email in enumerate(client_emails, 1):
        print(f"\nGenerating draft {i}/{len(client_emails)}: {email['subject'][:50]}...")

        sender_email = extract_sender_email(email['from'])
        is_new_client = email['category'] == 'new_client_inquiry'

        # Load context for existing clients
        context = None
        if not is_new_client:
            context = load_client_context(sender_email)
            if context:
                print(f"  Loaded context for {context.get('client_name', sender_email)}")
            else:
                print(f"  Warning: No context found for {sender_email}, treating as new client")
                is_new_client = True

        # Generate response
        if is_new_client:
            response_body = generate_new_client_response(email, openai_key)
        else:
            response_body = generate_existing_client_response(email, context, openai_key)

        if response_body:
            draft = {
                'email_id': email['id'],
                'in_reply_to_subject': email['subject'],
                'sender': email['from'],
                'sender_email': sender_email,
                'category': email['category'],
                'draft_response': response_body,
                'generated_at': datetime.now().isoformat(),
                'has_context': context is not None
            }

            drafts.append(draft)
            print(f"  ✓ Draft generated ({len(response_body)} chars)")

        else:
            print(f"  ✗ Failed to generate draft")

    return drafts

def save_draft_responses(drafts):
    """Save draft responses to files."""
    os.makedirs('.tmp/drafts', exist_ok=True)

    # Save individual drafts
    for draft in drafts:
        draft_file = f".tmp/drafts/{draft['email_id']}.json"
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft, f, indent=2, ensure_ascii=False)

    # Save summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_drafts': len(drafts),
        'new_clients': len([d for d in drafts if d['category'] == 'new_client_inquiry']),
        'existing_clients': len([d for d in drafts if d['category'] == 'existing_client']),
        'drafts': [
            {
                'email_id': d['email_id'],
                'subject': d['in_reply_to_subject'],
                'sender': d['sender_email'],
                'category': d['category']
            }
            for d in drafts
        ]
    }

    with open('.tmp/draft_responses_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved {len(drafts)} draft responses to .tmp/drafts/")
    print(f"  New client inquiries: {summary['new_clients']}")
    print(f"  Existing client communications: {summary['existing_clients']}")

if __name__ == '__main__':
    # Load categorized emails
    emails = load_categorized_emails()
    print(f"Loaded {len(emails)} categorized emails.")

    # Generate drafts
    drafts = generate_draft_responses(emails)

    # Save drafts
    save_draft_responses(drafts)

    print("\n📝 Review drafts in .tmp/drafts/ before sending!")
