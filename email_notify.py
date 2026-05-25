from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Any

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

logger = logging.getLogger(__name__)


def _status_label(flags: list[dict]) -> str:
    severities = {f["severity"] for f in flags}
    if "error" in severities:
        return "ERRORS"
    if "warning" in severities:
        return "WARNINGS"
    return "CLEAN"


def _build_body(data: dict[str, Any], flags: list[dict]) -> str:
    line_items = data.get("line_items") or []
    issues = [f for f in flags if f["severity"] != "pass"]

    lines = [
        "SmartInvoice AI — Invoice Summary",
        "=" * 40,
        f"Vendor       : {data.get('vendor_name', 'N/A')}",
        f"Invoice No.  : {data.get('invoice_number', 'N/A')}",
        f"Invoice Date : {data.get('invoice_date', 'N/A')}",
        f"Currency     : {data.get('currency', 'N/A')}",
        "",
        f"Subtotal     : {data.get('subtotal', 0):.2f}",
        f"VAT          : {data.get('vat', 0):.2f}",
        f"Total        : {data.get('total_amount', 0):.2f}",
        f"Line items   : {len(line_items)}",
        "",
        "Validation Results",
        "-" * 40,
    ]

    if not issues:
        lines.append("All checks passed.")
    else:
        for f in issues:
            lines.append(f"[{f['severity'].upper()}] {f['rule']}: {f['message']}")

    lines += ["", "— SmartInvoice AI"]
    return "\n".join(lines)


def send_invoice_summary(
    data: dict[str, Any],
    flags: list[dict],
    gmail_address: str | None = None,
    gmail_app_password: str | None = None,
    notification_email: str | None = None,
) -> None:
    sender = gmail_address or os.environ.get("GMAIL_ADDRESS", "")
    password = gmail_app_password or os.environ.get("GMAIL_APP_PASSWORD", "")
    recipient = notification_email or os.environ.get("NOTIFICATION_EMAIL", "")

    if not all([sender, password, recipient]):
        logger.warning(
            "Email not sent — GMAIL_ADDRESS, GMAIL_APP_PASSWORD, or "
            "NOTIFICATION_EMAIL is missing."
        )
        return

    status = _status_label(flags)
    vendor = data.get("vendor_name", "Unknown Vendor")
    inv_num = data.get("invoice_number", "N/A")

    msg = MIMEText(_build_body(data, flags))
    msg["Subject"] = f"Invoice {inv_num} from {vendor} - {status}"
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(sender, password)
            smtp.sendmail(sender, recipient, msg.as_string())
        logger.info("Invoice summary email sent to %s", recipient)
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail authentication failed — make sure you're using an App Password, "
            "not your account password. Generate one at myaccount.google.com/apppasswords."
        )
    except Exception as exc:
        logger.error("Failed to send invoice summary email: %s", exc)
