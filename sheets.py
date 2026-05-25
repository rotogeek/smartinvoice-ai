from __future__ import annotations

from datetime import datetime
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "timestamp",
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "subtotal",
    "vat",
    "total_amount",
    "currency",
    "status",
    "flags_summary",
]


def get_worksheet(creds_info: dict, sheet_id: str) -> gspread.Worksheet:
    try:
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client.open_by_key(sheet_id).sheet1
    except gspread.exceptions.APIError as exc:
        raise RuntimeError(
            f"Google Sheets API error — verify the sheet ID and that the service "
            f"account has Editor access to the sheet.\n{exc}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Could not authenticate with Google Sheets — verify the service account "
            f"JSON in secrets.toml is complete and correct.\n{exc}"
        ) from exc


def get_existing_invoice_numbers(ws: gspread.Worksheet) -> list[str]:
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return []
    col = HEADERS.index("invoice_number")
    return [row[col] for row in rows[1:] if len(row) > col and row[col]]


def _status(flags: list[dict]) -> str:
    severities = {f["severity"] for f in flags}
    if "error" in severities:
        return "INVALID"
    if "warning" in severities:
        return "WARNING"
    return "VALID"


def _flags_summary(flags: list[dict]) -> str:
    issues = [f for f in flags if f["severity"] != "pass"]
    if not issues:
        return "All checks passed"
    return " | ".join(f"[{f['severity'].upper()}] {f['message']}" for f in issues)


def append_invoice(
    ws: gspread.Worksheet,
    data: dict[str, Any],
    flags: list[dict],
) -> None:
    if not ws.get_all_values():
        ws.append_row(HEADERS)

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(data.get("vendor_name", "")),
        str(data.get("invoice_number", "")),
        str(data.get("invoice_date", "")),
        data.get("subtotal", ""),
        data.get("vat", ""),
        data.get("total_amount", ""),
        str(data.get("currency", "")),
        _status(flags),
        _flags_summary(flags),
    ]
    ws.append_row(row)
