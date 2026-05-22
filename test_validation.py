"""
Run with:  python test_validation.py
All cases should report PASS.
"""
from validation import validate_invoice


def severities(results: list) -> dict:
    """Return {rule: severity} for easy assertions."""
    return {r["rule"]: r["severity"] for r in results}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _clean_invoice() -> dict:
    """A well-formed SA VAT invoice: subtotal=100, vat=15, total=115."""
    return {
        "vendor_name": "Acme Supplies",
        "invoice_number": "INV-001",
        "invoice_date": "2024-03-15",
        "line_items": [
            {"description": "Widget A", "quantity": 2, "unit_price": 30.00, "total": 60.00},
            {"description": "Widget B", "quantity": 1, "unit_price": 40.00, "total": 40.00},
        ],
        "subtotal": 100.00,
        "vat": 15.00,
        "total_amount": 115.00,
        "currency": "ZAR",
    }


# ---------------------------------------------------------------------------
# Test 1 — clean valid invoice: all rules should pass
# ---------------------------------------------------------------------------
def test_clean_invoice():
    results = validate_invoice(_clean_invoice(), existing_invoice_numbers=[])
    s = severities(results)
    assert s["required_fields"] == "pass", s
    assert s["vat_rate"] == "pass", s
    assert s["line_items_sum"] == "pass", s
    assert s["total_check"] == "pass", s
    assert s["duplicate_check"] == "pass", s
    assert s["invoice_date"] == "pass", s
    print("PASS  test_clean_invoice")


# ---------------------------------------------------------------------------
# Test 2 — wrong VAT (R10 instead of R15)
# ---------------------------------------------------------------------------
def test_wrong_vat():
    inv = _clean_invoice()
    inv["vat"] = 10.00
    inv["total_amount"] = 110.00  # consistent with wrong vat
    results = validate_invoice(inv, existing_invoice_numbers=[])
    s = severities(results)
    assert s["vat_rate"] == "error", s
    # total_check passes because subtotal+vat still adds up (100+10=110)
    assert s["total_check"] == "pass", s
    print("PASS  test_wrong_vat")


# ---------------------------------------------------------------------------
# Test 3 — line items don't add up to subtotal
# ---------------------------------------------------------------------------
def test_mismatched_line_items():
    inv = _clean_invoice()
    # Corrupt one line item total without touching subtotal
    inv["line_items"][0]["total"] = 50.00  # was 60.00, now off by R10
    results = validate_invoice(inv, existing_invoice_numbers=[])
    s = severities(results)
    assert s["line_items_sum"] == "error", s
    print("PASS  test_mismatched_line_items")


# ---------------------------------------------------------------------------
# Test 4 — duplicate invoice number
# ---------------------------------------------------------------------------
def test_duplicate_invoice():
    inv = _clean_invoice()
    existing = ["INV-001", "INV-002", "INV-003"]
    results = validate_invoice(inv, existing_invoice_numbers=existing)
    s = severities(results)
    assert s["duplicate_check"] == "error", s
    print("PASS  test_duplicate_invoice")


# ---------------------------------------------------------------------------
# Test 5 — future invoice date (warning, not error)
# ---------------------------------------------------------------------------
def test_future_date():
    inv = _clean_invoice()
    inv["invoice_date"] = "2099-12-31"
    results = validate_invoice(inv, existing_invoice_numbers=[])
    s = severities(results)
    assert s["invoice_date"] == "warning", s
    print("PASS  test_future_date")


# ---------------------------------------------------------------------------
# Test 6 — missing required field
# ---------------------------------------------------------------------------
def test_missing_field():
    inv = _clean_invoice()
    del inv["vendor_name"]
    results = validate_invoice(inv, existing_invoice_numbers=[])
    s = severities(results)
    assert s["required_fields"] == "error", s
    print("PASS  test_missing_field")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_clean_invoice,
        test_wrong_vat,
        test_mismatched_line_items,
        test_duplicate_invoice,
        test_future_date,
        test_missing_field,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failed += 1
    print()
    print(f"{'All tests passed.' if failed == 0 else f'{failed} test(s) failed.'}")
