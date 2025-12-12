# Email Organization Workflow - Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Gmail OAuth

You already have `credentials.json` in place. On first run, you'll be prompted to authenticate:

```bash
python execution/fetch_emails.py 2024-12-01 2024-12-12 all
```

This will open a browser window for Google OAuth authentication and create `token.json`.

### 3. Run the Complete Workflow

```bash
python execution/organize_emails.py 2024-12-01 2024-12-12 all
```

**Parameters:**
- `START_DATE`: Start date (YYYY-MM-DD)
- `END_DATE`: End date (YYYY-MM-DD)
- `STATUS`: `all` (default), `read`, or `unread`

## What the Workflow Does

### Step 1: Fetch Emails
- Authenticates with Gmail using OAuth 2.0
- Fetches all emails in the specified date range
- Saves to `.tmp/emails_cache.json`

### Step 2: Categorize Emails
- Uses Claude AI to categorize each email into:
  - **Advertising**: Marketing, promotions, newsletters
  - **Invoice**: Bills, payment requests, receipts
  - **Important Update**: Service changes, critical notifications
  - **New Client Inquiry**: First-time contact, new business
  - **Existing Client**: Ongoing client communications
  - **Other**: Everything else
- Saves to `.tmp/categorization_results.json`

### Step 3: Process Invoices
- Downloads PDF invoices to `invoices/YYYY-MM/`
- Logs all invoices to `.tmp/invoice_log.json`
- Identifies "dashboard-only" invoices requiring manual download
- Saves dashboard invoices to `.tmp/dashboard_invoices.json`

### Step 4: Manage Client Contexts
- Creates/updates context files in `client_contexts/{email}/`
- Uses AI to extract key information:
  - Project summary
  - Communication history
  - Action items
  - Client details

### Step 5: Generate Draft Responses
- Creates draft responses for:
  - **New clients**: Professional welcome, clarifying questions
  - **Existing clients**: Context-aware replies with project references
- Saves drafts to `.tmp/drafts/{email_id}.json`
- Summary in `.tmp/draft_responses_summary.json`

### Step 6: Apply Gmail Labels
- Creates hierarchical labels:
  - `Email-Assistant/Advertising`
  - `Email-Assistant/Invoice`
  - `Email-Assistant/Important-Update`
  - `Email-Assistant/New-Client`
  - `Email-Assistant/Existing-Client`
  - `Email-Assistant/Other`
- Applies labels to all categorized emails

## Output Files

### Deliverables (Permanent)
- **Gmail Labels**: Applied directly in your Gmail inbox
- **Invoice PDFs**: `invoices/YYYY-MM/filename.pdf`
- **Client Contexts**: `client_contexts/{email}/context.json`

### Intermediates (Regenerable - in `.tmp/`)
- `emails_cache.json` - Raw email data
- `categorization_results.json` - Categorized emails
- `invoice_log.json` - Invoice metadata
- `dashboard_invoices.json` - Invoices needing manual download
- `drafts/{email_id}.json` - Generated draft responses
- `draft_responses_summary.json` - Draft summary
- `labeling_report.json` - Label application report
- `processing_report.json` - Final workflow summary

## Running Individual Scripts

You can run scripts independently for testing or specific tasks:

### Fetch Emails Only
```bash
python execution/fetch_emails.py 2024-12-01 2024-12-12 all
```

### Categorize Existing Cache
```bash
python execution/categorize_emails.py
```

Use OpenAI instead of Anthropic:
```bash
python execution/categorize_emails.py openai
```

### Process Invoices Only
```bash
python execution/process_invoices.py
```

### Manage Client Contexts
```bash
python execution/manage_client_context.py
```

### Generate Draft Responses
```bash
python execution/generate_draft_responses.py
```

### Apply Gmail Labels
```bash
python execution/apply_gmail_labels.py
```

## Example Workflow

```bash
# Process last month's emails
python execution/organize_emails.py 2024-11-01 2024-11-30 all

# Process only unread emails from this week
python execution/organize_emails.py 2024-12-08 2024-12-12 unread

# Process a single day
python execution/organize_emails.py 2024-12-12 2024-12-12 all
```

## Reviewing Results

### 1. Check Gmail
Your emails will now have labels applied. Check your Gmail inbox to see the categorization.

### 2. Review Dashboard Invoices
If any invoices require manual download:

```bash
cat .tmp/dashboard_invoices.json
```

### 3. Review Draft Responses
Check generated drafts before sending:

```bash
# List all drafts
ls .tmp/drafts/

# View a specific draft
cat .tmp/drafts/{email_id}.json

# View summary
cat .tmp/draft_responses_summary.json
```

### 4. Check Invoice PDFs
```bash
ls invoices/
```

### 5. Review Client Contexts
```bash
# List all clients
ls client_contexts/

# View a specific client context
cat client_contexts/{client_email}/context.json
```

### 6. View Final Report
```bash
cat .tmp/processing_report.json
```

## Troubleshooting

### Gmail Authentication Issues
If you get authentication errors:
1. Delete `token.json`
2. Run `python execution/fetch_emails.py 2024-12-01 2024-12-12 all` again
3. Complete the OAuth flow in your browser

### API Key Issues
Verify your API keys in `.env`:
```bash
cat .env | grep API_KEY
```

### Script Errors
Each script can be run independently for debugging:
```bash
python execution/fetch_emails.py 2024-12-01 2024-12-12 all
python execution/categorize_emails.py
# etc.
```

## Tips

1. **Start Small**: Test with a short date range first (e.g., one day)
2. **Review Drafts**: Always review AI-generated drafts before sending
3. **Context Files**: Manually edit `client_contexts/` files to improve accuracy
4. **Dashboard Invoices**: Set aside time to manually download these
5. **Labels**: You can modify label names in `execution/apply_gmail_labels.py`

## Customization

### Change Categories
Edit the `CATEGORIES` dict in [`execution/categorize_emails.py`](execution/categorize_emails.py:15)

### Adjust Label Names
Edit the `LABEL_MAP` dict in [`execution/apply_gmail_labels.py`](execution/apply_gmail_labels.py:12)

### Invoice Storage Location
Update `INVOICE_DIR` in [`.env`](.env)

### Use Different AI Model
Change the model in categorization and draft generation scripts:
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
- OpenAI: `gpt-4o`, `gpt-4o-mini`

## Architecture Reminder

This follows the 3-layer architecture:

1. **Directive**: [`directives/organize_emails.md`](directives/organize_emails.md) - Instructions
2. **Orchestration**: You (or the AI agent) - Decision making
3. **Execution**: [`execution/*.py`](execution/) - Deterministic code

When things break, the system self-anneals by updating both the execution scripts and the directive.
