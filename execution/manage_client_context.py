"""
nimport sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
Client Context Manager
Maintains context files for client communications and projects.
"""

import os
import json
import re
from datetime import datetime
from anthropic import Anthropic
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
    match = re.search(r'<(.+?)>', from_field)
    if match:
        return match.group(1).strip().lower()
    return from_field.strip().lower()

def extract_sender_name(from_field):
    """Extract name from 'From' field."""
    # Format: "John Doe <john@example.com>"
    if '<' in from_field:
        name = from_field.split('<')[0].strip().strip('"')
        return name if name else "Unknown"
    return "Unknown"

def load_context(sender_email):
    """Load existing context for a client."""
    context_dir = f"client_contexts/{sender_email}"
    context_file = os.path.join(context_dir, 'context.json')

    if os.path.exists(context_file):
        with open(context_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    return None

def create_new_context(email, anthropic_key):
    """Create new context for a client using LLM analysis."""
    client = Anthropic(api_key=anthropic_key)

    sender_email = extract_sender_email(email['from'])
    sender_name = extract_sender_name(email['from'])

    email_content = f"""
Subject: {email['subject']}
From: {email['from']}
Date: {email['date']}

Body:
{email['body'][:2000]}
"""

    prompt = f"""Analyze this client inquiry and extract key information for a context file.

Email:
{email_content}

Provide a JSON response with these fields:
- "inquiry_type": Brief description of what they're asking about (e.g., "Website development quote", "Support request")
- "key_points": List of 2-3 key points from their message
- "project_summary": One sentence summary of their needs/project
- "urgency": "high", "medium", or "low"

Respond with ONLY valid JSON, no other text."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse LLM response
        analysis = json.loads(message.content[0].text.strip())

        # Build context structure
        context = {
            'client_email': sender_email,
            'client_name': sender_name,
            'first_contact': email['date'],
            'last_contact': email['date'],
            'project_summary': analysis.get('project_summary', 'No summary available'),
            'inquiry_type': analysis.get('inquiry_type', 'General inquiry'),
            'status': 'active',
            'communications': [
                {
                    'email_id': email['id'],
                    'date': email['date'],
                    'subject': email['subject'],
                    'topic': analysis.get('inquiry_type', 'Initial contact'),
                    'key_points': analysis.get('key_points', [])
                }
            ],
            'action_items': [
                {
                    'description': 'Respond to initial inquiry',
                    'status': 'pending',
                    'created': datetime.now().isoformat(),
                    'urgency': analysis.get('urgency', 'medium')
                }
            ],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        return context

    except Exception as e:
        print(f"  Error creating context with LLM: {e}")

        # Fallback: basic context without LLM analysis
        return {
            'client_email': sender_email,
            'client_name': sender_name,
            'first_contact': email['date'],
            'last_contact': email['date'],
            'project_summary': email['subject'],
            'inquiry_type': 'General inquiry',
            'status': 'active',
            'communications': [
                {
                    'email_id': email['id'],
                    'date': email['date'],
                    'subject': email['subject'],
                    'topic': 'Initial contact',
                    'key_points': []
                }
            ],
            'action_items': [
                {
                    'description': 'Respond to initial inquiry',
                    'status': 'pending',
                    'created': datetime.now().isoformat(),
                    'urgency': 'medium'
                }
            ],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

def update_existing_context(context, email, anthropic_key):
    """Update existing context with new email."""
    client = Anthropic(api_key=anthropic_key)

    email_content = f"""
Subject: {email['subject']}
Date: {email['date']}
Body:
{email['body'][:1500]}
"""

    context_summary = f"""
Project: {context.get('project_summary', 'Unknown')}
Last communication: {context.get('last_contact', 'Unknown')}
"""

    prompt = f"""Analyze this follow-up email from an existing client.

Current project context:
{context_summary}

New email:
{email_content}

Provide a JSON response with:
- "topic": Brief topic of this email (e.g., "Project update request", "Bug report")
- "key_points": List of 2-3 key points from this message
- "new_action_items": List of any new action items mentioned (can be empty list)

Respond with ONLY valid JSON, no other text."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        analysis = json.loads(message.content[0].text.strip())

        # Add new communication
        new_comm = {
            'email_id': email['id'],
            'date': email['date'],
            'subject': email['subject'],
            'topic': analysis.get('topic', 'Follow-up'),
            'key_points': analysis.get('key_points', [])
        }

        context['communications'].append(new_comm)

        # Add new action items
        for item_desc in analysis.get('new_action_items', []):
            context['action_items'].append({
                'description': item_desc,
                'status': 'pending',
                'created': datetime.now().isoformat(),
                'urgency': 'medium'
            })

        # Update timestamps
        context['last_contact'] = email['date']
        context['updated_at'] = datetime.now().isoformat()

        return context

    except Exception as e:
        print(f"  Error updating context with LLM: {e}")

        # Fallback: basic update
        context['communications'].append({
            'email_id': email['id'],
            'date': email['date'],
            'subject': email['subject'],
            'topic': 'Follow-up',
            'key_points': []
        })

        context['last_contact'] = email['date']
        context['updated_at'] = datetime.now().isoformat()

        return context

def save_context(context):
    """Save context to file."""
    sender_email = context['client_email']
    context_dir = f"client_contexts/{sender_email}"
    context_file = os.path.join(context_dir, 'context.json')

    os.makedirs(context_dir, exist_ok=True)

    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=2, ensure_ascii=False)

def manage_client_contexts(emails):
    """
    Create or update client contexts for relevant emails.

    Args:
        emails: List of categorized email objects

    Returns:
        Summary of context operations
    """
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    if not anthropic_key:
        raise ValueError("ANTHROPIC_API_KEY not found in .env file")

    # Filter client emails
    client_emails = [
        e for e in emails
        if e.get('category') in ['new_client_inquiry', 'existing_client']
    ]

    print(f"Found {len(client_emails)} client emails to process.")

    contexts_created = 0
    contexts_updated = 0

    for i, email in enumerate(client_emails, 1):
        sender_email = extract_sender_email(email['from'])
        print(f"\nProcessing {i}/{len(client_emails)}: {sender_email}")

        # Load or create context
        context = load_context(sender_email)

        if context:
            print(f"  Updating existing context for {context.get('client_name', sender_email)}")
            context = update_existing_context(context, email, anthropic_key)
            contexts_updated += 1
        else:
            print(f"  Creating new context")
            context = create_new_context(email, anthropic_key)
            contexts_created += 1

        # Save context
        save_context(context)
        print(f"  ✓ Context saved")

    summary = {
        'total_processed': len(client_emails),
        'contexts_created': contexts_created,
        'contexts_updated': contexts_updated
    }

    return summary

if __name__ == '__main__':
    # Load categorized emails
    emails = load_categorized_emails()
    print(f"Loaded {len(emails)} categorized emails.")

    # Manage contexts
    summary = manage_client_contexts(emails)

    print(f"\n✓ Client context management complete!")
    print(f"  New contexts created: {summary['contexts_created']}")
    print(f"  Existing contexts updated: {summary['contexts_updated']}")
