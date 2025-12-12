# Invoice PDF Processing & Organization

## Purpose
Extract structured data from invoice PDFs (date, sender, amount, currency) and organize them by date and sender for better financial tracking and management.

## Inputs
- **Invoice Directory**: Path to folder containing invoice PDFs (default: `invoices/`)
- **Processing Mode**: `extract`, `organize`, or `full` (both)

## Tools/Scripts to Use

### 1. Invoice Data Extraction
**Script**: `execution/extract_invoice_data.py`
- Reads PDF files using pdfplumber and PyPDF2
- Extracts text content from invoices
- Uses LLM (Claude/OpenAI) to intelligently parse:
  - Invoice date
  - Sender/vendor name
  - Invoice number (if available)
  - Total amount
  - Currency
- Saves extracted data to `invoices_metadata.json`

### 2. Invoice Organization
**Script**: `execution/organize_invoices_by_sender.py`
- Reads `invoices_metadata.json`
- Creates organized directory structure:
  ```
  invoices/
  ├── by_date/
  │   ├── 2025-12/
  │   │   ├── anthropic/
  │   │   ├── google/
  │   │   └── loom/
  │   └── 2025-11/
  │       └── fiverr/
  └── by_sender/
      ├── anthropic/
      ├── google/
      ├── loom/
      └── apify/
  ```
- Creates symlinks or copies files to both organizational views
- Generates summary reports by sender and by month

### 3. Invoice Verification
**Script**: `execution/verify_invoice_data.py`
- Validates extracted data
- Flags invoices with missing or uncertain data
- Creates review queue for manual verification

## Outputs

### Deliverables
1. **Organized Invoices**:
   - `invoices/by_date/YYYY-MM/sender/` - Organized by date, then sender
   - `invoices/by_sender/sender_name/` - Organized by sender

2. **Invoice Database**: `invoices_metadata.json` - Structured data for all invoices
   ```json
   {
     "invoice_id": "unique_id",
     "filename": "original.pdf",
     "sender": "Anthropic",
     "invoice_number": "2324-5265-4991",
     "date": "2025-12-01",
     "amount": 100.50,
     "currency": "USD",
     "confidence": 0.95,
     "file_paths": {
       "by_date": "invoices/by_date/2025-12/anthropic/Receipt-2324.pdf",
       "by_sender": "invoices/by_sender/anthropic/2025-12-01_Receipt-2324.pdf"
     }
   }
   ```

3. **Summary Reports**:
   - `.tmp/invoice_summary_by_sender.json` - Total spending by vendor
   - `.tmp/invoice_summary_by_month.json` - Monthly spending breakdown
   - `.tmp/invoice_review_queue.json` - Invoices needing manual review

### Intermediates (.tmp/)
1. **Extracted Text**: `.tmp/invoice_texts/` - Raw text from each PDF
2. **Processing Log**: `.tmp/invoice_processing_log.json`
3. **Error Log**: `.tmp/invoice_errors.json` - Failed extractions

## Workflow Steps

### Full Processing Mode

1. **Extract Data**
   - Run `extract_invoice_data.py` on all PDFs in `invoices/`
   - For each PDF:
     - Extract text using pdfplumber
     - If text extraction fails, use OCR (pytesseract)
     - Send extracted text to LLM with structured prompt
     - Parse LLM response for: date, sender, amount, currency
     - Validate extracted data
     - Save to `invoices_metadata.json`

2. **Organize Files**
   - Run `organize_invoices_by_sender.py`
   - Create directory structure
   - Copy/symlink files to organized locations
   - Update metadata with new file paths

3. **Generate Reports**
   - Calculate totals by sender
   - Calculate totals by month
   - Identify invoices needing review
   - Save summary reports

4. **Verification**
   - Run `verify_invoice_data.py`
   - Flag low-confidence extractions
   - Create review queue

## Edge Cases & Learnings

### PDF Text Extraction
- Some PDFs are scanned images: use OCR (pytesseract + Tesseract)
- Multi-page invoices: extract from all pages, focus on first page
- Tables in PDFs: pdfplumber handles tables well
- Encrypted PDFs: skip and log error

### LLM Extraction Prompt
Use structured prompt for consistency:
```
Extract invoice data from this text in JSON format:
{
  "date": "YYYY-MM-DD format",
  "sender": "Company name",
  "invoice_number": "Invoice/receipt number",
  "amount": numeric value only,
  "currency": "USD/EUR/etc"
}

Invoice text:
[EXTRACTED_TEXT]

Respond with ONLY valid JSON.
```

### Date Parsing
- Multiple date formats: use dateutil.parser
- Common formats: "Dec 1, 2025", "2025-12-01", "01/12/2025"
- If multiple dates found, prefer:
  1. "Invoice Date" or "Date"
  2. Latest date on document
  3. Flag for manual review

### Sender Identification
- Extract from "From:", "Bill From:", "Vendor:", etc.
- Normalize names: "Anthropic, PBC" → "anthropic"
- Common senders: anthropic, google, loom, apify, adobe
- Unknown senders: use "unknown_vendor"

### Amount Extraction
- Look for keywords: "Total", "Amount Due", "Paid", "Balance"
- Handle multiple currencies in one doc (use primary)
- Parse formats: "$100.50", "100,50 EUR", "100.50 USD"
- Decimal vs thousand separators vary by locale

### Currency Detection
- From symbol: $→USD, €→EUR, £→GBP
- From text: "USD", "EUR", "GBP"
- Default to USD if uncertain

### File Organization
- Use lowercase, no spaces for folder names
- Date format in filenames: YYYY-MM-DD
- Handle duplicate filenames: append counter
- Preserve original files in `invoices/original/`

### Confidence Scoring
- High confidence (>0.9): All fields extracted with clear values
- Medium confidence (0.7-0.9): Some fields unclear but parseable
- Low confidence (<0.7): Missing or ambiguous data → review queue

## Error Handling
- PDF read errors: log and skip, add to error report
- LLM API failures: retry with exponential backoff (max 3)
- Invalid JSON from LLM: parse with fallback regex
- File permission errors: log and continue
- Duplicate invoices: flag and add to review queue

## Configuration (from .env)
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - For intelligent extraction
- `INVOICE_DIR=invoices` - Invoice directory
- `USE_OCR=false` - Enable OCR for scanned PDFs (requires Tesseract)

## Success Criteria
- All invoices have extracted metadata
- Invoices organized by date and sender
- Summary reports generated
- Review queue created for uncertain extractions
- Less than 10% of invoices require manual review

## Dependencies
```
pdfplumber>=0.10.0
PyPDF2>=3.0.0
pytesseract>=0.3.10  # Optional, for OCR
Pillow>=10.0.0       # For image processing
python-dateutil>=2.8.2
anthropic>=0.39.0
openai>=1.54.0
```

## Manual Review Required
- Invoices in `.tmp/invoice_review_queue.json`
- Low-confidence extractions
- Duplicate invoice numbers
- Unusual amounts or currencies
