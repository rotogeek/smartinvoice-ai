#!/usr/bin/env python3
"""
Sends a test invoice summary email using credentials from secrets.toml.

Run with:  python test_email.py

Check your NOTIFICATION_EMAIL inbox — the email should arrive within
a few seconds. If it doesn't, check the error printed below.
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _load_secrets() -> dict:
    path = Path(".streamlit/secrets.toml")
    if not path.exists():
        print("ERROR: .streamlit/secrets.toml not found.")
        sys.exit(1)
    try:
        import tomllib
    except ImportError:
        print("ERROR: tomllib requires Python 3.11+")
        sys.exit(1)
    with open(path, "rb") as f:
        return tomllib.load(f)


def main() -> None:
    secrets = _load_secrets()

    from email_notify import send_invoice_summary

    fake_data = {
        "vendor_name": "Acme Pharmaceuticals",
        "invoice_number": "ACME-TEST-001",
        "invoice_date": "2024-03-15",
        "line_items": [
            {"description": "Paracetamol 500mg", "quantity": 100, "unit_price": 0.50, "total": 50.00},
            {"description": "Ibuprofen 200mg",   "quantity": 50,  "unit_price": 1.00, "total": 50.00},
        ],
        "subtotal": 100.00,
        "vat": 15.00,
        "total_amount": 115.00,
        "currency": "ZAR",
    }
    fake_flags = [
        {"rule": "required_fields", "severity": "pass",    "message": "All required fields are present."},
        {"rule": "vat_rate",        "severity": "pass",    "message": "VAT R15.00 matches expected 15%."},
        {"rule": "line_items_sum",  "severity": "pass",    "message": "Line items total R100.00 matches subtotal."},
        {"rule": "total_check",     "severity": "pass",    "message": "Total R115.00 matches subtotal + VAT."},
        {"rule": "duplicate_check", "severity": "pass",    "message": "Invoice number is unique."},
        {"rule": "invoice_date",    "severity": "warning", "message": "Invoice date 2024-03-15 is valid."},
    ]

    print(f"Sending test email to {secrets.get('NOTIFICATION_EMAIL', '(not set)')} ...")

    send_invoice_summary(
        fake_data,
        fake_flags,
        gmail_address=secrets.get("GMAIL_ADDRESS"),
        gmail_app_password=secrets.get("GMAIL_APP_PASSWORD"),
        notification_email=secrets.get("NOTIFICATION_EMAIL"),
    )

    print("Done — check your inbox.")


if __name__ == "__main__":
    main()
