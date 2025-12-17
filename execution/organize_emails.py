"""
Email Organization Orchestrator
Orchestrates the full email organization workflow.
"""

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import sys
import json
from datetime import datetime
import subprocess

def run_script(script_name, args=[]):
    """

import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

Run a Python script and handle errors."""
    cmd = [sys.executable, script_name] + args

    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\n⚠️  Warning: {script_name} exited with code {result.returncode}")
        return False

    return True

def generate_final_report():
    """Generate final processing report."""
    report = {
        'workflow_completed_at': datetime.now().isoformat(),
        'status': 'success'
    }

    # Load categorization results
    if os.path.exists('.tmp/categorization_results.json'):
        with open('.tmp/categorization_results.json', 'r') as f:
            cat_data = json.load(f)
            report['total_emails'] = cat_data.get('total_emails', 0)
            report['category_counts'] = cat_data.get('category_counts', {})

    # Load invoice log
    if os.path.exists('.tmp/invoice_log.json'):
        with open('.tmp/invoice_log.json', 'r') as f:
            inv_data = json.load(f)
            report['invoices_downloaded'] = inv_data.get('total_invoices', 0)

    # Load dashboard invoices
    if os.path.exists('.tmp/dashboard_invoices.json'):
        with open('.tmp/dashboard_invoices.json', 'r') as f:
            dash_data = json.load(f)
            report['dashboard_invoices'] = dash_data.get('total_dashboard_invoices', 0)

    # Load draft responses
    if os.path.exists('.tmp/draft_responses_summary.json'):
        with open('.tmp/draft_responses_summary.json', 'r') as f:
            draft_data = json.load(f)
            report['drafts_generated'] = draft_data.get('total_drafts', 0)
            report['new_client_drafts'] = draft_data.get('new_clients', 0)
            report['existing_client_drafts'] = draft_data.get('existing_clients', 0)

    # Save report
    with open('.tmp/processing_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report

def print_final_summary(report):
    """Print final summary to console."""
    print("\n" + "="*60)
    print("EMAIL ORGANIZATION WORKFLOW COMPLETE")
    print("="*60 + "\n")

    print(f"📧 Total emails processed: {report.get('total_emails', 0)}")

    if 'category_counts' in report:
        print("\n📊 Category breakdown:")
        for category, count in sorted(report['category_counts'].items()):
            print(f"   • {category}: {count}")

    if 'invoices_downloaded' in report:
        print(f"\n💰 Invoices:")
        print(f"   • PDFs downloaded: {report['invoices_downloaded']}")

        if report.get('dashboard_invoices', 0) > 0:
            print(f"   • ⚠️  Dashboard invoices (manual download needed): {report['dashboard_invoices']}")
            print(f"       See: .tmp/dashboard_invoices.json")

    if 'drafts_generated' in report:
        print(f"\n✏️  Draft responses generated: {report['drafts_generated']}")
        print(f"   • New client inquiries: {report.get('new_client_drafts', 0)}")
        print(f"   • Existing client communications: {report.get('existing_client_drafts', 0)}")
        print(f"       Review drafts in: .tmp/drafts/")

    print(f"\n📁 Deliverables:")
    print(f"   • Gmail labels applied in your inbox")
    print(f"   • Invoice PDFs: invoices/")
    print(f"   • Client contexts: client_contexts/")

    print(f"\n📄 Full report: .tmp/processing_report.json")
    print("\n" + "="*60 + "\n")

def main():
    """Main orchestration function."""
    if len(sys.argv) < 3:
        print("Usage: python organize_emails.py START_DATE END_DATE [STATUS]")
        print("Example: python organize_emails.py 2024-01-01 2024-01-31 all")
        print("\nSTATUS options: all (default), read, unread")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    status = sys.argv[3] if len(sys.argv) > 3 else 'all'

    print("\n" + "="*60)
    print("EMAIL ORGANIZATION WORKFLOW")
    print("="*60)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Email status: {status}")
    print("="*60)

    # Step 1: Fetch emails
    success = run_script('execution/fetch_emails.py', [start_date, end_date, status])
    if not success:
        print("\n❌ Workflow failed at email fetching step")
        sys.exit(1)

    # Step 2: Categorize emails
    success = run_script('execution/categorize_emails.py')
    if not success:
        print("\n❌ Workflow failed at categorization step")
        sys.exit(1)

    # Step 3: Process invoices
    success = run_script('execution/process_invoices.py')
    if not success:
        print("\n⚠️  Invoice processing encountered issues, continuing...")

    # Step 4: Manage client contexts
    success = run_script('execution/manage_client_context.py')
    if not success:
        print("\n⚠️  Client context management encountered issues, continuing...")

    # Step 5: Generate draft responses
    success = run_script('execution/generate_draft_responses.py')
    if not success:
        print("\n⚠️  Draft generation encountered issues, continuing...")

    # Step 6: Apply Gmail labels
    success = run_script('execution/apply_gmail_labels.py')
    if not success:
        print("\n⚠️  Label application encountered issues, continuing...")

    # Generate and display final report
    report = generate_final_report()
    print_final_summary(report)

if __name__ == '__main__':
    main()
