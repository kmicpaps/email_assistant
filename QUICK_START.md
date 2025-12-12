# Quick Start Guide

## Setup (One Time)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify credentials:**
   - ✓ `credentials.json` is already in place
   - ✓ API keys are configured in `.env`

## Run the Workflow

**Process emails from a specific date range:**

```bash
python execution/organize_emails.py 2024-12-01 2024-12-12 all
```

Replace dates with your desired range.

## What Happens

The workflow will:
1. Fetch emails from Gmail
2. Categorize them using AI (advertising, invoices, client inquiries, etc.)
3. Download invoice PDFs to `invoices/`
4. Generate draft responses for client emails
5. Create/update client context files
6. Apply Gmail labels to organize your inbox

## View Results

**Check your Gmail inbox** - all emails will have labels applied

**Review draft responses:**
```bash
cat .tmp/draft_responses_summary.json
ls .tmp/drafts/
```

**Check downloaded invoices:**
```bash
ls invoices/
```

**View client contexts:**
```bash
ls client_contexts/
```

**See full report:**
```bash
cat .tmp/processing_report.json
```

## Manual Actions Required

1. **Dashboard Invoices** - Some invoices can't be auto-downloaded:
   ```bash
   cat .tmp/dashboard_invoices.json
   ```

2. **Review Drafts** - Check AI-generated responses before sending:
   ```bash
   ls .tmp/drafts/
   ```

## Need Help?

- See [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed documentation
- See [directives/organize_emails.md](directives/organize_emails.md) for workflow details
- See [README.md](README.md) for architecture overview

## Quick Examples

**Process last 7 days:**
```bash
python execution/organize_emails.py 2024-12-05 2024-12-12 all
```

**Process only unread emails:**
```bash
python execution/organize_emails.py 2024-12-01 2024-12-12 unread
```

**Process a single day:**
```bash
python execution/organize_emails.py 2024-12-12 2024-12-12 all
```

## First Time Running?

On first run, you'll be prompted to authenticate with Google:
1. A browser window will open
2. Sign in with your Google account
3. Grant permissions to the app
4. `token.json` will be created automatically
5. Subsequent runs will use the saved token
