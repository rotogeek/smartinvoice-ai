from pathlib import Path

import streamlit as st

from email_notify import send_invoice_summary
from extraction import extract_invoice
from sheets import append_invoice, get_existing_invoice_numbers, get_worksheet
from validation import validate_invoice

st.set_page_config(page_title="SmartInvoice AI", page_icon="🧾", layout="wide")

MIME_MAP = {
    ".pdf":  "application/pdf",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
}

# ── Cached resources ────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _worksheet():
    return get_worksheet(
        dict(st.secrets["gcp_service_account"]),
        st.secrets["GOOGLE_SHEET_ID"],
    )


def _secret(key: str, default=None):
    try:
        return st.secrets[key]
    except KeyError:
        return default


# ── Session state ────────────────────────────────────────────────────────────

for _k, _v in [("file_key", None), ("extracted", None), ("flags", None), ("logged", False)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🧾 SmartInvoice AI")
    st.markdown(
        "Upload a supplier invoice and this app will:\n\n"
        "- **Extract** structured data with Groq Llama 4 Scout vision\n"
        "- **Validate** against South African VAT rules (15 %)\n"
        "- **Log** approved invoices to Google Sheets\n"
        "- **Email** you a summary"
    )
    st.divider()
    st.markdown("[View source on GitHub](https://github.com/rotogeek/smartinvoice-ai)")
    st.divider()
    demo_mode = st.toggle(
        "Demo Mode",
        help="Auto-loads a sample invoice from sample_invoices/ — no upload needed.",
    )

# ── Header ───────────────────────────────────────────────────────────────────

st.title("🧾 SmartInvoice AI")
st.caption("Upload a PDF or image invoice to extract, validate, and log it automatically.")
st.divider()

# ── File input ───────────────────────────────────────────────────────────────

file_bytes: bytes | None = None
file_name: str | None = None

if demo_mode:
    sample_dir = Path("sample_invoices")
    samples = (
        sorted(sample_dir.glob("*.pdf"))
        + sorted(sample_dir.glob("*.png"))
        + sorted(sample_dir.glob("*.jpg"))
    )
    if samples:
        sample_path = samples[0]
        st.info(f"Demo mode — loaded **{sample_path.name}**")
        file_bytes = sample_path.read_bytes()
        file_name = sample_path.name
    else:
        st.warning("No sample invoices found in `sample_invoices/`. Add a PDF to use Demo Mode.")
else:
    uploaded = st.file_uploader(
        "Upload an invoice",
        type=["pdf", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )
    if uploaded:
        file_bytes = uploaded.read()
        file_name = uploaded.name

# ── Processing ───────────────────────────────────────────────────────────────

if file_bytes and file_name:
    file_key = f"{file_name}:{len(file_bytes)}"

    # New file — reset state and process
    if file_key != st.session_state.file_key:
        st.session_state.file_key = file_key
        st.session_state.extracted = None
        st.session_state.flags = None
        st.session_state.logged = False

        mime = MIME_MAP.get(Path(file_name).suffix.lower(), "image/jpeg")

        with st.spinner("Extracting invoice data..."):
            try:
                st.session_state.extracted = extract_invoice(
                    file_bytes, mime, api_key=_secret("GROQ_API_KEY")
                )
            except Exception as exc:
                st.error(f"Extraction failed: {exc}")
                st.stop()

        try:
            ws = _worksheet()
            existing = get_existing_invoice_numbers(ws)
        except Exception:
            existing = []
            st.warning("Could not reach Google Sheets — duplicate check skipped.")

        st.session_state.flags = validate_invoice(st.session_state.extracted, existing)

    data: dict = st.session_state.extracted
    flags: list = st.session_state.flags

    # ── Extracted fields ─────────────────────────────────────────────────────

    st.subheader("Extracted Data")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Vendor", data.get("vendor_name", "—"))
        st.metric("Invoice Number", data.get("invoice_number", "—"))
        st.metric("Invoice Date", data.get("invoice_date", "—"))
        st.metric("Currency", data.get("currency", "—"))
    with col2:
        currency = data.get("currency", "")
        st.metric("Subtotal", f"{currency} {data.get('subtotal', 0):,.2f}")
        st.metric("VAT", f"{currency} {data.get('vat', 0):,.2f}")
        st.metric("Total Amount", f"{currency} {data.get('total_amount', 0):,.2f}")

    # ── Line items ───────────────────────────────────────────────────────────

    line_items = data.get("line_items") or []
    if line_items:
        st.subheader("Line Items")
        st.dataframe(line_items, use_container_width=True, hide_index=True)

    # ── Validation ───────────────────────────────────────────────────────────

    st.subheader("Validation")
    has_errors = any(f["severity"] == "error" for f in flags)

    for flag in flags:
        rule_label = flag["rule"].replace("_", " ").title()
        msg = f"**{rule_label}** — {flag['message']}"
        if flag["severity"] == "pass":
            st.success(f"✅ {msg}")
        elif flag["severity"] == "warning":
            st.warning(f"⚠️ {msg}")
        else:
            st.error(f"❌ {msg}")

    # ── Actions ──────────────────────────────────────────────────────────────

    st.divider()

    if has_errors:
        st.error("❌ Cannot log this invoice — resolve the errors above first.")
    elif st.session_state.logged:
        st.success("✅ Invoice logged to Google Sheets and summary email sent.")
    else:
        if st.button("✅ Approve & Log", type="primary", use_container_width=True):
            with st.spinner("Logging to Google Sheets..."):
                try:
                    ws = _worksheet()
                    append_invoice(ws, data, flags)
                except Exception as exc:
                    st.error(f"Failed to log to Google Sheets: {exc}")
                    st.stop()

            with st.spinner("Sending email summary..."):
                try:
                    send_invoice_summary(
                        data,
                        flags,
                        gmail_address=_secret("GMAIL_ADDRESS"),
                        gmail_app_password=_secret("GMAIL_APP_PASSWORD"),
                        notification_email=_secret("NOTIFICATION_EMAIL"),
                    )
                except Exception as exc:
                    st.warning(f"Invoice logged but email failed: {exc}")

            st.session_state.logged = True
            st.rerun()
