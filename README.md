# Email Assistant - Agentic Workflow System

This workspace implements a 3-layer architecture for reliable AI-powered automation, designed to handle email processing and invoice management with maximum reliability.

## Quick Start for Collaborators

### Prerequisites
- Python 3.10 or higher
- Git
- Gmail account with API access
- OpenAI or Anthropic API key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd email_assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your API keys
   # - ANTHROPIC_API_KEY or OPENAI_API_KEY (required)
   # - Configure other settings as needed
   ```

4. **Set up Gmail OAuth credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download the credentials file
   - Save as `credentials.json` in the project root

   Example structure (see `credentials.json.example`):
   ```json
   {
     "installed": {
       "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
       "project_id": "your-project-id",
       ...
     }
   }
   ```

5. **First run - Authenticate**
   ```bash
   # This will open a browser for Gmail OAuth
   python execution/fetch_emails.py 2025-12-01 2025-12-12 all

   # A token.json will be created automatically
   ```

6. **Run workflows**
   ```bash
   # Organize emails
   python -X utf8 execution/organize_emails.py 2025-12-01 2025-12-12 all

   # Process invoices
   python execution/process_invoices_full.py
   ```

## Architecture Overview

### Layer 1: Directives (What to do)
- **Location**: [`directives/`](directives/)
- **Purpose**: SOPs written in Markdown that define goals, inputs, tools, outputs, and edge cases
- **Format**: Natural language instructions, like you'd give a mid-level employee

### Layer 2: Orchestration (Decision making)
- **Who**: AI agents (Claude, Gemini, etc.)
- **Purpose**: Intelligent routing, error handling, and decision-making
- **Role**: Read directives, call execution tools in the right order, handle errors, ask for clarification

### Layer 3: Execution (Doing the work)
- **Location**: [`execution/`](execution/)
- **Purpose**: Deterministic Python scripts that handle API calls, data processing, file operations
- **Characteristics**: Reliable, testable, fast, well-commented

## Directory Structure

```
email_assistant/
├── .tmp/                  # Temporary files (never committed)
├── execution/             # Python scripts (deterministic tools)
│   ├── organize_emails.py          # Main email organization orchestrator
│   ├── fetch_emails.py              # Gmail email fetching
│   ├── categorize_emails.py         # LLM-based categorization
│   ├── process_invoices.py          # Invoice PDF download
│   ├── extract_invoice_data.py      # Invoice data extraction
│   ├── organize_invoices_by_sender.py  # Invoice organization
│   ├── generate_draft_responses.py  # Draft response generation
│   ├── manage_client_context.py     # Client context tracking
│   └── apply_gmail_labels.py        # Gmail label management
├── directives/            # Markdown SOPs (instruction set)
│   ├── organize_emails.md           # Email organization workflow
│   └── process_invoice_pdfs.md      # Invoice processing workflow
├── invoices/              # Generated invoices (gitignored)
│   ├── by_date/          # Organized by YYYY-MM/sender/
│   └── by_sender/        # Organized by sender/YYYY-MM-DD_
├── client_contexts/       # Client context files (gitignored)
├── .env                   # Environment variables (gitignored)
├── .env.example          # Environment template
├── credentials.json       # Google OAuth credentials (gitignored)
├── credentials.json.example  # Credentials template
├── token.json            # Google OAuth token (gitignored)
├── requirements.txt      # Python dependencies
├── CLAUDE.md             # Agent instructions
├── AGENTS.md             # Agent instructions (mirror)
├── GEMINI.md             # Agent instructions (mirror)
├── QUICK_START.md        # Quick reference guide
└── USAGE_GUIDE.md        # Detailed usage documentation
```

## Features

### Email Organization
- **Auto-categorization**: Uses LLM to categorize emails into:
  - Advertising
  - Invoices
  - Important updates
  - New client inquiries
  - Existing client communications
  - Other

- **Gmail labels**: Automatically applies hierarchical labels
- **Invoice download**: Extracts PDF attachments from invoice emails
- **Draft responses**: Generates professional draft replies for client emails
- **Client context**: Maintains conversation history and project details

### Invoice Processing
- **PDF extraction**: Reads invoice PDFs and extracts:
  - Invoice date
  - Sender/vendor name
  - Invoice number
  - Amount and currency

- **Dual organization**:
  - By date: `invoices/by_date/YYYY-MM/sender/`
  - By sender: `invoices/by_sender/sender/YYYY-MM-DD_`

- **Spending analytics**: Automatic summaries by vendor and month
- **High accuracy**: 100% confidence on most invoices with LLM extraction

## Key Principles

1. **Deliverables vs Intermediates**
   - Deliverables: Gmail labels, organized invoices, client contexts
   - Intermediates: Temporary files in `.tmp/` (can be deleted and regenerated)

2. **Self-Annealing**
   - When errors occur: fix it, update the tool, test it, update the directive
   - System continuously improves through learning

3. **Tool-First Approach**
   - Check `execution/` for existing scripts before creating new ones
   - Push complexity into deterministic code

## Available Workflows

### 1. Email Organization
**Directive**: [`directives/organize_emails.md`](directives/organize_emails.md)

**Usage**:
```bash
python -X utf8 execution/organize_emails.py START_DATE END_DATE [STATUS]

# Example: Process last 30 days
python -X utf8 execution/organize_emails.py 2025-11-12 2025-12-12 all
```

**What it does**:
1. Fetches emails from Gmail
2. Categorizes using LLM
3. Downloads invoice PDFs
4. Generates draft responses for client emails
5. Creates/updates client context files
6. Applies Gmail labels

### 2. Invoice Processing
**Directive**: [`directives/process_invoice_pdfs.md`](directives/process_invoice_pdfs.md)

**Usage**:
```bash
# Full processing (extract + organize)
python execution/process_invoices_full.py

# Or run individually:
python execution/extract_invoice_data.py      # Extract data from PDFs
python execution/organize_invoices_by_sender.py  # Organize by date & sender
```

**What it does**:
1. Reads all PDF invoices
2. Extracts structured data (date, sender, amount, currency)
3. Organizes by date and sender
4. Generates spending summaries

## Output Files

### Deliverables (Persistent)
- **Gmail Labels**: Applied in your Gmail interface
- **Organized Invoices**: `invoices/by_date/` and `invoices/by_sender/`
- **Client Contexts**: `client_contexts/{email}/context.json`
- **Invoice Metadata**: `invoices_metadata.json`

### Reports (Temporary - `.tmp/`)
- `categorization_results.json` - Email categorization results
- `invoice_log.json` - Downloaded invoice metadata
- `dashboard_invoices.json` - Invoices requiring manual download
- `draft_responses_summary.json` - Generated draft summary
- `invoice_summary_by_sender.json` - Spending by vendor
- `invoice_summary_by_month.json` - Spending by month
- `invoice_review_queue.json` - Low-confidence extractions

## Environment Variables

See [`.env.example`](.env.example) for all configuration options:

**Required**:
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - For email categorization and invoice extraction

**Optional**:
- `INVOICE_DIR` - Invoice storage location (default: `invoices`)
- `TMP_DIR` - Temporary files location (default: `.tmp`)
- `MAX_SEARCH_RESULTS` - Gmail search limit (default: 10)
- `USE_OCR` - Enable OCR for scanned PDFs (default: false)

## Troubleshooting

### Gmail Authentication Issues
If you get authentication errors:
1. Delete `token.json`
2. Run any email script again
3. Complete the OAuth flow in your browser

### API Key Issues
Verify your API keys in `.env`:
```bash
# Check if keys are set
cat .env | grep API_KEY
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Update the relevant directive in `directives/`
4. Test your changes
5. Submit a pull request

## Security Notes

**Never commit these files**:
- `.env` - Contains API keys
- `credentials.json` - Google OAuth credentials
- `token.json` - Google OAuth token
- `invoices/` - Contains sensitive financial data
- `client_contexts/` - Contains client information
- `.tmp/` - May contain sensitive intermediate data

These are all in `.gitignore` and should never be pushed to the repository.

## Documentation

- [`QUICK_START.md`](QUICK_START.md) - Quick reference for common tasks
- [`USAGE_GUIDE.md`](USAGE_GUIDE.md) - Detailed usage instructions
- [`directives/`](directives/) - Workflow SOPs and implementation details

## Architecture Philosophy

**Why 3 layers?**
- LLMs are probabilistic (90% accuracy per step)
- 5 steps at 90% = 59% success rate
- Solution: Push complexity into deterministic code
- AI layer focuses only on decision-making

This separation maximizes reliability while leveraging AI for intelligent routing and categorization.

## License

Private repository - For authorized collaborators only.
