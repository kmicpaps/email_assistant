"""
Invoice Data Extraction Script
Extracts structured data from invoice PDFs using PDF parsing and LLM.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)

INVOICE_DIR = os.getenv('INVOICE_DIR', 'invoices')

def extract_text_from_pdf(pdf_path, max_pages=3):
    """Extract text from PDF using pdfplumber."""
    text_content = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract from first few pages (invoices usually on first page)
            pages_to_read = min(len(pdf.pages), max_pages)

            for i in range(pages_to_read):
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    text_content.append(text)

        return "\n\n--- PAGE BREAK ---\n\n".join(text_content)

    except Exception as e:
        print(f"  Error extracting text from {pdf_path}: {e}")
        return None

def extract_invoice_data_with_llm(text, filename, api_key):
    """Use LLM to extract structured invoice data."""
    client = OpenAI(api_key=api_key)

    # Limit text length for API
    text_sample = text[:4000] if len(text) > 4000 else text

    prompt = f"""Extract invoice data from this text and respond with ONLY valid JSON in this exact format:
{{
  "date": "YYYY-MM-DD format or null if not found",
  "sender": "Company/vendor name or null if not found",
  "invoice_number": "Invoice/receipt number or null if not found",
  "amount": numeric value only (e.g., 100.50) or null if not found,
  "currency": "USD/EUR/GBP/etc or null if not found"
}}

Important:
- For date: convert any date format to YYYY-MM-DD
- For sender: use the company/vendor name (e.g., "Anthropic", "Google", "Loom")
- For amount: extract the TOTAL amount or amount paid (numeric only, no symbols)
- For currency: use 3-letter code (USD, EUR, etc.) from symbols ($=USD, €=EUR) or text

Invoice filename: {filename}

Invoice text:
{text_sample}

Respond with ONLY the JSON object, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0
        )

        json_text = response.choices[0].message.content.strip()

        # Try to extract JSON if wrapped in markdown
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()

        data = json.loads(json_text)

        # Calculate confidence based on how many fields were extracted
        fields_found = sum(1 for v in data.values() if v is not None)
        confidence = fields_found / 5.0  # 5 fields total

        data['confidence'] = round(confidence, 2)

        return data

    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  LLM response: {json_text[:200]}")
        return None
    except Exception as e:
        print(f"  LLM API error: {e}")
        return None

def normalize_sender_name(sender):
    """Normalize sender name for folder organization."""
    if not sender:
        return "unknown"

    # Convert to lowercase, remove special chars
    normalized = re.sub(r'[^a-z0-9]+', '_', sender.lower())
    normalized = normalized.strip('_')

    # Common mappings
    mappings = {
        'anthropic_pbc': 'anthropic',
        'google_workspace': 'google',
        'loom_inc': 'loom',
        'apify_technologies': 'apify'
    }

    return mappings.get(normalized, normalized)

def process_invoice_pdfs(invoice_dir=INVOICE_DIR):
    """
    Process all invoice PDFs and extract structured data.

    Returns:
        List of invoice data dictionaries
    """
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    # Find all PDFs recursively
    pdf_files = list(Path(invoice_dir).rglob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {invoice_dir}")
        return []

    print(f"Found {len(pdf_files)} invoice PDFs to process.\n")

    invoices_data = []
    errors = []

    for i, pdf_path in enumerate(pdf_files, 1):
        filename = pdf_path.name
        relative_path = str(pdf_path.relative_to(invoice_dir))

        print(f"Processing {i}/{len(pdf_files)}: {filename}")

        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)

        if not text or len(text.strip()) < 50:
            print(f"  ⚠️  Insufficient text extracted (possibly scanned image)")
            errors.append({
                'filename': filename,
                'path': str(pdf_path),
                'error': 'Insufficient text extracted - may need OCR'
            })
            continue

        # Save extracted text
        text_dir = Path('.tmp/invoice_texts')
        text_dir.mkdir(parents=True, exist_ok=True)

        text_file = text_dir / f"{pdf_path.stem}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)

        # Extract structured data with LLM
        invoice_data = extract_invoice_data_with_llm(text, filename, api_key)

        if not invoice_data:
            print(f"  ✗ Failed to extract data")
            errors.append({
                'filename': filename,
                'path': str(pdf_path),
                'error': 'LLM extraction failed'
            })
            continue

        # Add metadata
        invoice_data['filename'] = filename
        invoice_data['original_path'] = str(pdf_path)
        invoice_data['relative_path'] = relative_path
        invoice_data['processed_at'] = datetime.now().isoformat()

        # Normalize sender
        if invoice_data.get('sender'):
            invoice_data['sender_normalized'] = normalize_sender_name(invoice_data['sender'])
        else:
            invoice_data['sender_normalized'] = 'unknown'

        invoices_data.append(invoice_data)

        # Print summary
        conf_icon = "✓" if invoice_data['confidence'] >= 0.8 else "⚠️"
        print(f"  {conf_icon} Extracted: {invoice_data.get('sender', 'N/A')} | "
              f"{invoice_data.get('date', 'N/A')} | "
              f"{invoice_data.get('amount', 'N/A')} {invoice_data.get('currency', 'N/A')} | "
              f"Confidence: {invoice_data['confidence']}")

    return invoices_data, errors

def save_invoice_metadata(invoices_data, output_path='invoices_metadata.json'):
    """Save extracted invoice data to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_invoices': len(invoices_data),
            'invoices': invoices_data
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved metadata for {len(invoices_data)} invoices to {output_path}")

def save_error_log(errors, output_path='.tmp/invoice_errors.json'):
    """Save processing errors to log file."""
    os.makedirs('.tmp', exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_errors': len(errors),
            'errors': errors
        }, f, indent=2, ensure_ascii=False)

    if errors:
        print(f"⚠️  {len(errors)} errors logged to {output_path}")

def generate_review_queue(invoices_data, threshold=0.7):
    """Generate review queue for low-confidence extractions."""
    review_queue = [
        inv for inv in invoices_data
        if inv.get('confidence', 0) < threshold
    ]

    if review_queue:
        output_path = '.tmp/invoice_review_queue.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_for_review': len(review_queue),
                'message': 'These invoices have low confidence and should be manually reviewed',
                'invoices': review_queue
            }, f, indent=2, ensure_ascii=False)

        print(f"📋 {len(review_queue)} invoices flagged for review → {output_path}")

if __name__ == '__main__':
    import sys

    # Optional: specify invoice directory
    invoice_dir = sys.argv[1] if len(sys.argv) > 1 else INVOICE_DIR

    print("="*60)
    print("INVOICE DATA EXTRACTION")
    print("="*60)
    print(f"Invoice directory: {invoice_dir}\n")

    # Process invoices
    invoices_data, errors = process_invoice_pdfs(invoice_dir)

    # Save results
    save_invoice_metadata(invoices_data)
    save_error_log(errors)
    generate_review_queue(invoices_data)

    # Print summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total processed: {len(invoices_data)}")
    print(f"Errors: {len(errors)}")

    high_conf = len([inv for inv in invoices_data if inv.get('confidence', 0) >= 0.8])
    print(f"High confidence (≥0.8): {high_conf}")

    needs_review = len([inv for inv in invoices_data if inv.get('confidence', 0) < 0.7])
    print(f"Needs review (<0.7): {needs_review}")

    print("="*60)
