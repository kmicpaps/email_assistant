"""
Invoice Organization Script
Organizes invoices by date and sender based on extracted metadata.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

INVOICE_DIR = os.getenv('INVOICE_DIR', 'invoices')

def load_invoice_metadata(metadata_path='invoices_metadata.json'):
    """Load invoice metadata."""
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data['invoices']

def create_organized_structure(invoices_data, base_dir=INVOICE_DIR):
    """
    Create organized directory structure and copy files.

    Organization:
    - invoices/by_date/YYYY-MM/sender/filename.pdf
    - invoices/by_sender/sender/YYYY-MM-DD_filename.pdf
    """
    by_date_dir = Path(base_dir) / 'by_date'
    by_sender_dir = Path(base_dir) / 'by_sender'

    by_date_dir.mkdir(parents=True, exist_ok=True)
    by_sender_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'total_organized': 0,
        'by_sender': defaultdict(int),
        'by_month': defaultdict(int),
        'skipped': 0
    }

    for i, invoice in enumerate(invoices_data, 1):
        filename = invoice['filename']
        original_path = Path(invoice['original_path'])

        if not original_path.exists():
            print(f"  ⚠️  File not found: {original_path}")
            stats['skipped'] += 1
            continue

        # Extract date and sender
        invoice_date = invoice.get('date')
        sender = invoice.get('sender_normalized', 'unknown')

        if not invoice_date:
            # Fallback: use file modification date
            invoice_date = datetime.fromtimestamp(original_path.stat().st_mtime).strftime('%Y-%m-%d')
            print(f"  ⚠️  Using file date for {filename}: {invoice_date}")

        # Extract year-month
        year_month = invoice_date[:7]  # YYYY-MM

        # Create paths
        # 1. By date: invoices/by_date/YYYY-MM/sender/filename.pdf
        date_dir = by_date_dir / year_month / sender
        date_dir.mkdir(parents=True, exist_ok=True)
        date_path = date_dir / filename

        # 2. By sender: invoices/by_sender/sender/YYYY-MM-DD_filename.pdf
        sender_dir = by_sender_dir / sender
        sender_dir.mkdir(parents=True, exist_ok=True)
        sender_filename = f"{invoice_date}_{filename}"
        sender_path = sender_dir / sender_filename

        # Copy files
        try:
            # Copy to by_date
            if not date_path.exists():
                shutil.copy2(original_path, date_path)

            # Copy to by_sender
            if not sender_path.exists():
                shutil.copy2(original_path, sender_path)

            stats['total_organized'] += 1
            stats['by_sender'][sender] += 1
            stats['by_month'][year_month] += 1

            print(f"  ✓ {i}/{len(invoices_data)}: {filename} → {sender}/{year_month}")

        except Exception as e:
            print(f"  ✗ Error copying {filename}: {e}")
            stats['skipped'] += 1

    return stats

def generate_summary_reports(invoices_data):
    """Generate summary reports by sender and month."""

    # By sender summary
    by_sender = defaultdict(lambda: {'count': 0, 'total_amount': 0, 'currencies': set()})

    for invoice in invoices_data:
        sender = invoice.get('sender_normalized', 'unknown')
        amount = invoice.get('amount')
        currency = invoice.get('currency')

        by_sender[sender]['count'] += 1

        if amount is not None and currency:
            by_sender[sender]['total_amount'] += amount
            by_sender[sender]['currencies'].add(currency)

    # Convert sets to lists for JSON serialization
    sender_summary = {}
    for sender, data in by_sender.items():
        sender_summary[sender] = {
            'count': data['count'],
            'total_amount': round(data['total_amount'], 2),
            'currencies': list(data['currencies'])
        }

    # Save sender summary
    with open('.tmp/invoice_summary_by_sender.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_senders': len(sender_summary),
            'summary': sender_summary
        }, f, indent=2, ensure_ascii=False)

    # By month summary
    by_month = defaultdict(lambda: {'count': 0, 'total_amount': 0, 'currencies': set()})

    for invoice in invoices_data:
        date = invoice.get('date')
        if not date:
            continue

        month = date[:7]  # YYYY-MM
        amount = invoice.get('amount')
        currency = invoice.get('currency')

        by_month[month]['count'] += 1

        if amount is not None and currency:
            by_month[month]['total_amount'] += amount
            by_month[month]['currencies'].add(currency)

    # Convert sets to lists for JSON serialization
    month_summary = {}
    for month, data in by_month.items():
        month_summary[month] = {
            'count': data['count'],
            'total_amount': round(data['total_amount'], 2),
            'currencies': list(data['currencies'])
        }

    # Save month summary
    with open('.tmp/invoice_summary_by_month.json', 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_months': len(month_summary),
            'summary': month_summary
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Generated summary reports:")
    print(f"  - By sender: .tmp/invoice_summary_by_sender.json")
    print(f"  - By month: .tmp/invoice_summary_by_month.json")

    return sender_summary, month_summary

if __name__ == '__main__':
    print("="*60)
    print("INVOICE ORGANIZATION")
    print("="*60)

    # Load metadata
    print("\nLoading invoice metadata...")
    invoices_data = load_invoice_metadata()
    print(f"Loaded {len(invoices_data)} invoices.\n")

    # Organize files
    print("Organizing invoices...")
    stats = create_organized_structure(invoices_data)

    # Generate reports
    print("\nGenerating summary reports...")
    sender_summary, month_summary = generate_summary_reports(invoices_data)

    # Print summary
    print("\n" + "="*60)
    print("ORGANIZATION SUMMARY")
    print("="*60)
    print(f"Total organized: {stats['total_organized']}")
    print(f"Skipped: {stats['skipped']}")

    print(f"\nBy Sender ({len(stats['by_sender'])} vendors):")
    for sender, count in sorted(stats['by_sender'].items(), key=lambda x: x[1], reverse=True):
        total = sender_summary.get(sender, {}).get('total_amount', 0)
        currencies = sender_summary.get(sender, {}).get('currencies', [])
        curr_str = '/'.join(currencies) if currencies else 'N/A'
        print(f"  • {sender}: {count} invoices, Total: {total} {curr_str}")

    print(f"\nBy Month ({len(stats['by_month'])} months):")
    for month in sorted(stats['by_month'].keys(), reverse=True):
        count = stats['by_month'][month]
        total = month_summary.get(month, {}).get('total_amount', 0)
        currencies = month_summary.get(month, {}).get('currencies', [])
        curr_str = '/'.join(currencies) if currencies else 'N/A'
        print(f"  • {month}: {count} invoices, Total: {total} {curr_str}")

    print("\n" + "="*60)
    print("Organization complete!")
    print(f"  📁 By date: {INVOICE_DIR}/by_date/")
    print(f"  📁 By sender: {INVOICE_DIR}/by_sender/")
    print("="*60)
