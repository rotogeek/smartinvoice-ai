#!/usr/bin/env python3
"""
Smoke-test for Google Sheets integration.

Run with:  python test_sheets.py

Appends a timestamped fake invoice row, then reads all rows back and
confirms the row was written. Safe to run multiple times — each run
uses a unique invoice number so it won't trigger the duplicate check.
"""
import sys
from datetime import datetime
from pathlib import Path


def _load_secrets() -> dict:
    path = Path(".streamlit/secrets.toml")
    if not path.exists():
        print("ERROR: .streamlit/secrets.toml not found.")
        sys.exit(1)
    try:
        import tomllib
    except ImportError:
        print("ERROR: tomllib requires Python 3.11+. Upgrade or export secrets manually.")
        sys.exit(1)
    with open(path, "rb") as f:
        import tomllib
        return tomllib.load(f)


def main() -> None:
    secrets = _load_secrets()

    creds_info = dict(secrets.get("gcp_service_account", {}))
    sheet_id = secrets.get("GOOGLE_SHEET_ID", "")

    if not creds_info:
        print("ERROR: [gcp_service_account] section missing from secrets.toml")
        sys.exit(1)
    if not sheet_id:
        print("ERROR: GOOGLE_SHEET_ID missing from secrets.toml")
        sys.exit(1)

    from sheets import append_invoice, get_existing_invoice_numbers, get_worksheet

    print("Connecting to Google Sheets...")
    ws = get_worksheet(creds_info, sheet_id)
    print(f"Connected to worksheet: '{ws.title}'")

    existing = get_existing_invoice_numbers(ws)
    print(f"Existing invoice numbers: {existing if existing else '(none yet)'}")

    inv_number = f"TEST-{datetime.now().strftime('%H%M%S')}"
    fake_data = {
        "vendor_name": "Test Vendor Ltd",
        "invoice_number": inv_number,
        "invoice_date": "2024-03-15",
        "subtotal": 100.00,
        "vat": 15.00,
        "total_amount": 115.00,
        "currency": "ZAR",
    }
    fake_flags = [
        {"rule": "required_fields", "severity": "pass", "message": "All required fields are present."},
        {"rule": "vat_rate", "severity": "pass", "message": "VAT R15.00 matches expected R15.00 (15%)."},
        {"rule": "line_items_sum", "severity": "pass", "message": "Line items total matches subtotal."},
        {"rule": "total_check", "severity": "pass", "message": "Total matches subtotal + VAT."},
        {"rule": "duplicate_check", "severity": "pass", "message": f"Invoice number '{inv_number}' is unique."},
        {"rule": "invoice_date", "severity": "pass", "message": "Invoice date 2024-03-15 is valid."},
    ]

    print(f"Appending test row for invoice '{inv_number}'...")
    append_invoice(ws, fake_data, fake_flags)

    # Verify the row landed
    all_rows = ws.get_all_values()
    last_row = all_rows[-1]
    assert inv_number in last_row, f"Invoice number not found in last row: {last_row}"

    print(f"Row verified: {last_row}")
    print("\nGoogle Sheets integration is working correctly.")


if __name__ == "__main__":
    main()
