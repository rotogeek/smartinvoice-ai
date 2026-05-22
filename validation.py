from __future__ import annotations

from datetime import date
from typing import Any

REQUIRED_FIELDS = [
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "line_items",
    "subtotal",
    "vat",
    "total_amount",
    "currency",
]

SA_VAT_RATE = 0.15
TOLERANCE = 0.50


def _r(rule: str, severity: str, message: str) -> dict[str, str]:
    return {"rule": rule, "severity": severity, "message": message}


def validate_invoice(
    data: dict[str, Any],
    existing_invoice_numbers: list[str],
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    # Rule 1 — required fields
    missing = [
        f for f in REQUIRED_FIELDS
        if data.get(f) is None
        or data.get(f) == ""
        or (f == "line_items" and data.get(f) == [])
    ]
    if missing:
        results.append(_r(
            "required_fields", "error",
            f"Missing or empty required fields: {', '.join(missing)}",
        ))
    else:
        results.append(_r("required_fields", "pass", "All required fields are present."))

    # Rule 2 — VAT = 15 % of subtotal
    try:
        subtotal = float(data["subtotal"])
        vat = float(data["vat"])
        expected_vat = round(subtotal * SA_VAT_RATE, 2)
        if abs(vat - expected_vat) <= TOLERANCE:
            results.append(_r(
                "vat_rate", "pass",
                f"VAT R{vat:.2f} is within tolerance of expected R{expected_vat:.2f} (15 %).",
            ))
        else:
            results.append(_r(
                "vat_rate", "error",
                f"VAT R{vat:.2f} does not match 15 % of subtotal "
                f"R{subtotal:.2f} (expected R{expected_vat:.2f}).",
            ))
    except (KeyError, TypeError, ValueError):
        results.append(_r("vat_rate", "error", "Could not parse subtotal or VAT values."))

    # Rule 3 — line items sum = subtotal
    try:
        items = data.get("line_items") or []
        items_sum = sum(float(item.get("total", 0)) for item in items)
        subtotal = float(data["subtotal"])
        if abs(items_sum - subtotal) <= TOLERANCE:
            results.append(_r(
                "line_items_sum", "pass",
                f"Line items total R{items_sum:.2f} matches subtotal R{subtotal:.2f}.",
            ))
        else:
            results.append(_r(
                "line_items_sum", "error",
                f"Line items total R{items_sum:.2f} does not match "
                f"subtotal R{subtotal:.2f} (difference R{abs(items_sum - subtotal):.2f}).",
            ))
    except (KeyError, TypeError, ValueError):
        results.append(_r("line_items_sum", "error", "Could not sum line item totals."))

    # Rule 4 — subtotal + VAT = total_amount
    try:
        subtotal = float(data["subtotal"])
        vat = float(data["vat"])
        total = float(data["total_amount"])
        expected_total = subtotal + vat
        if abs(total - expected_total) <= TOLERANCE:
            results.append(_r(
                "total_check", "pass",
                f"Total R{total:.2f} matches subtotal R{subtotal:.2f} + VAT R{vat:.2f}.",
            ))
        else:
            results.append(_r(
                "total_check", "error",
                f"Total R{total:.2f} does not match subtotal R{subtotal:.2f} "
                f"+ VAT R{vat:.2f} = R{expected_total:.2f}.",
            ))
    except (KeyError, TypeError, ValueError):
        results.append(_r("total_check", "error", "Could not verify total amount."))

    # Rule 5 — duplicate invoice number
    inv_num = str(data.get("invoice_number", "")).strip()
    if inv_num in existing_invoice_numbers:
        results.append(_r(
            "duplicate_check", "error",
            f"Invoice number '{inv_num}' already exists — possible duplicate.",
        ))
    else:
        results.append(_r(
            "duplicate_check", "pass",
            f"Invoice number '{inv_num}' is unique.",
        ))

    # Rule 6 — invoice date valid and not in future
    date_str = str(data.get("invoice_date", "")).strip()
    try:
        inv_date = date.fromisoformat(date_str)
        if inv_date > date.today():
            results.append(_r(
                "invoice_date", "warning",
                f"Invoice date {date_str} is in the future.",
            ))
        else:
            results.append(_r(
                "invoice_date", "pass",
                f"Invoice date {date_str} is valid.",
            ))
    except (ValueError, TypeError):
        results.append(_r(
            "invoice_date", "error",
            f"Invoice date '{date_str}' could not be parsed as YYYY-MM-DD.",
        ))

    return results
