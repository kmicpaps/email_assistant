"""
Full Invoice Processing Orchestrator
Runs extraction and organization in sequence.
"""

import os
import sys
import subprocess

def run_script(script_name, args=[]):
    """Run a Python script and handle errors."""
    cmd = [sys.executable, script_name] + args

    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\n⚠️  Warning: {script_name} exited with code {result.returncode}")
        return False

    return True

def main():
    """Main orchestration function."""
    import sys

    # Get invoice directory (optional argument)
    invoice_dir = sys.argv[1] if len(sys.argv) > 1 else os.getenv('INVOICE_DIR', 'invoices')

    print("\n" + "="*60)
    print("FULL INVOICE PROCESSING WORKFLOW")
    print("="*60)
    print(f"Invoice directory: {invoice_dir}")
    print("="*60)

    # Step 1: Extract invoice data
    success = run_script('execution/extract_invoice_data.py', [invoice_dir])
    if not success:
        print("\n❌ Workflow failed at extraction step")
        sys.exit(1)

    # Step 2: Organize invoices
    success = run_script('execution/organize_invoices_by_sender.py')
    if not success:
        print("\n⚠️  Organization step encountered issues, but continuing...")

    print("\n" + "="*60)
    print("FULL INVOICE PROCESSING COMPLETE!")
    print("="*60)
    print("\n📊 Check the following:")
    print("  • invoices_metadata.json - Extracted invoice data")
    print(f"  • {invoice_dir}/by_date/ - Invoices organized by date")
    print(f"  • {invoice_dir}/by_sender/ - Invoices organized by sender")
    print("  • .tmp/invoice_summary_by_sender.json - Spending by vendor")
    print("  • .tmp/invoice_summary_by_month.json - Spending by month")
    print("  • .tmp/invoice_review_queue.json - Invoices needing review")
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
