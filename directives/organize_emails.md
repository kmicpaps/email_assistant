# Email Organization Workflow

## Purpose
Automatically categorize, process, and organize emails within a specified time range. Creates draft responses for client communications, downloads invoices, and maintains context for ongoing projects.

## Inputs
- **Time Range**: Start date and end date (format: YYYY-MM-DD)
- **Email Status**: Include read/unread/all emails (default: all)

## Tools/Scripts to Use

### 1. Gmail Authentication & Fetching
**Script**: `execution/fetch_emails.py`
- Authenticates using OAuth 2.0 (credentials.json → token.json)
- Fetches emails within specified date range
- Returns email metadata (id, subject, sender, date, body, attachments)

### 2. Email Categorization
**Script**: `execution/categorize_emails.py`
- Uses LLM (OpenAI or Anthropic fallback) to categorize each email
- Categories:
  - `advertising` - Marketing, promotional content
  - `invoice` - Bills, invoices, payment requests
  - `important_update` - Product updates, service changes, critical notifications
  - `new_client_inquiry` - First-time contact, new business opportunities
  - `existing_client` - Ongoing conversations with known clients/projects
  - `other` - Everything else

### 3. Invoice Processing
**Script**: `execution/process_invoices.py`
- Downloads PDF attachments from invoice emails
- Saves to `invoices/YYYY-MM/` organized by month
- Logs invoice metadata to `.tmp/invoice_log.json`
- Creates separate log for "dashboard-only" invoices (no direct PDF)
- Applies Gmail label: `Invoice/Processed`

### 4. Draft Response Generator
**Script**: `execution/generate_draft_responses.py`
- For `new_client_inquiry`: Creates professional, welcoming response draft
- For `existing_client`: Loads context from `client_contexts/`, generates contextual response
- Saves drafts to `.tmp/drafts/` as JSON with email_id reference
- Uses OpenAI API for response generation

### 5. Client Context Manager
**Script**: `execution/manage_client_context.py`
- Maintains context files in `client_contexts/{client_email}/`
- Each context file contains:
  - Client name and email
  - Project summary
  - Communication history (timestamps, topics)
  - Action items and status
- Updates context after each client email processed

### 6. Gmail Label Manager
**Script**: `execution/apply_gmail_labels.py`
- Creates labels if they don't exist:
  - `Email-Assistant/Advertising`
  - `Email-Assistant/Invoice`
  - `Email-Assistant/Important-Update`
  - `Email-Assistant/New-Client`
  - `Email-Assistant/Existing-Client`
- Applies appropriate labels to categorized emails

## Outputs

### Deliverables (Cloud/Persistent)
1. **Gmail Labels**: All emails labeled in Gmail interface
2. **Invoice PDFs**: Saved to `invoices/YYYY-MM/filename.pdf`
3. **Client Context Files**: Updated in `client_contexts/{client_email}/context.json`

### Intermediates (.tmp/ - regenerable)
1. **Email Cache**: `.tmp/emails_cache.json` - Raw email data
2. **Categorization Results**: `.tmp/categorization_results.json`
3. **Invoice Log**: `.tmp/invoice_log.json` - All invoices with metadata
4. **Dashboard Invoices Log**: `.tmp/dashboard_invoices.json` - Invoices requiring manual download
5. **Draft Responses**: `.tmp/drafts/{email_id}.json` - Generated response drafts
6. **Processing Report**: `.tmp/processing_report.json` - Summary of run

## Workflow Steps

1. **Authenticate & Fetch**
   - Run `fetch_emails.py` with date range
   - Cache results in `.tmp/emails_cache.json`

2. **Categorize**
   - Run `categorize_emails.py` on cached emails
   - Save results to `.tmp/categorization_results.json`

3. **Process by Category**
   - **Invoices**: Run `process_invoices.py`
     - Download PDFs
     - Log metadata
     - Flag dashboard-only invoices

   - **Client Inquiries/Communications**: Run `generate_draft_responses.py`
     - Load or create client context
     - Generate appropriate response
     - Save draft

   - **All Categories**: Run `apply_gmail_labels.py`
     - Apply category labels

4. **Update Client Contexts**
   - Run `manage_client_context.py`
   - Update context files for all client communications

5. **Generate Report**
   - Summary of emails processed
   - Count by category
   - List of dashboard invoices requiring manual action
   - Drafts ready for review

## Edge Cases & Learnings

### API Constraints
- Gmail API: 250 quota units/user/second, 1 billion/day
- Batch requests recommended for >10 emails
- Use `messages.list()` then `messages.get()` for efficiency

### Invoice Detection
- Check for PDF attachments first
- Keywords: "invoice", "bill", "payment", "receipt", "statement"
- If no PDF but invoice content: log to dashboard_invoices.json
- Common senders: accounting@, billing@, invoices@, noreply@

### Client Identification
- Match sender email against existing `client_contexts/` folders
- Heuristics for new client:
  - No prior context file
  - Email contains: "interested in", "quote", "inquiry", "services"
  - Not from known marketing domains

### Draft Response Guidelines
- New clients: Professional, warm, ask clarifying questions
- Existing clients: Reference project context, be specific
- Keep drafts concise (2-3 paragraphs max)
- Always end with clear next steps or questions

### Label Management
- Use hierarchical labels: `Email-Assistant/Category`
- Don't remove existing user labels
- Skip if email already has Email-Assistant label (avoid reprocessing)

### Error Handling
- If Gmail API fails: retry with exponential backoff (max 3 attempts)
- If LLM categorization fails: mark as "other" and log for manual review
- If PDF download fails: log to dashboard_invoices.json
- If context file corrupted: backup and create fresh

## Configuration (from .env)
- `OPENAI_API_KEY` - Primary LLM for categorization and draft generation
- `ANTHROPIC_API_KEY` - Fallback if OpenAI fails
- Gmail OAuth - `credentials.json` and `token.json`
- `INVOICE_DIR=invoices` - Invoice storage location
- `TMP_DIR=.tmp` - Intermediate files

## Success Criteria
- All emails in range are categorized
- Invoice PDFs downloaded or logged
- Client contexts updated
- Draft responses generated for inquiries
- Gmail labels applied
- Processing report shows summary

## Manual Review Required
- Dashboard invoices (no direct PDF)
- Draft responses before sending
- New client context files (verify accuracy)
