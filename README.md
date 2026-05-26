# SmartInvoice AI

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rotogeek-smartinvoice-ai-app-XXXXXX.streamlit.app)

> **Cut invoice processing from 15 minutes to 15 seconds** — upload a PDF, get structured data, SA VAT validation, a Google Sheets log, and an email summary with one click.

---

## The Problem

Processing supplier invoices manually means retyping fields from PDFs, running your own VAT arithmetic, maintaining spreadsheet logs by hand, and chasing colleagues with email updates. A medium-sized business can process hundreds of invoices a month — that's hours of error-prone admin every week, and a single wrong subtotal can mean a SARS audit finding.

## The Solution

SmartInvoice AI accepts a scanned or digital invoice (PDF or image), uses a Groq Llama 4 Scout vision model to extract every field, checks the numbers against South African VAT rules (15 %), writes a timestamped record to Google Sheets, and emails a plain-English summary — in under 30 seconds.

---

## Live Demo

🔗 **[smartinvoice-ai.streamlit.app](https://rotogeek-smartinvoice-ai-app-XXXXXX.streamlit.app)**

> _Screenshot placeholder — replace with a real screenshot before sharing_
>
> ![App screenshot](docs/screenshot.png)

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| UI + backend | Streamlit | Single-file Python web app, free cloud hosting |
| Vision AI | Groq + Llama 4 Scout | Free tier, fast inference, JSON mode |
| Storage | Google Sheets + gspread | Zero-cost, shareable, no database to manage |
| Email | Gmail SMTP + smtplib | No third-party email service needed |
| Deployment | Streamlit Community Cloud | Free, GitHub-connected, secrets management |

---

## How It Works

```
1. Upload     →  User drops a PDF or image invoice into the app
2. Extract    →  Groq Llama 4 Scout vision model reads the invoice and
                 returns structured JSON (vendor, amounts, line items, dates)
3. Validate   →  Business rules engine checks:
                   • All required fields present
                   • VAT = 15% of subtotal (±R0.50 tolerance)
                   • Line items sum = subtotal
                   • Subtotal + VAT = total
                   • Invoice number not already in the sheet (duplicate guard)
                   • Invoice date is valid and not in the future
4. Review     →  Colour-coded results shown: ✅ pass  ⚠️ warning  ❌ error
5. Approve    →  One click logs the invoice to Google Sheets
6. Notify     →  Email summary sent with CLEAN / WARNINGS / ERRORS status
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Streamlit UI                   │
│              app.py  (single page)              │
└────────┬──────────────┬──────────────┬──────────┘
         │              │              │
         ▼              ▼              ▼
  extraction.py   validation.py   sheets.py
  ┌──────────┐   ┌───────────┐   ┌──────────┐
  │ Groq API │   │ Pure      │   │ gspread  │
  │ Llama 4  │   │ Python    │   │ Google   │
  │ Scout    │   │ rules     │   │ Sheets   │
  └──────────┘   └───────────┘   └──────────┘
                                      │
                               email_notify.py
                               ┌──────────────┐
                               │ Gmail SMTP   │
                               │ smtplib      │
                               └──────────────┘

  All secrets via Streamlit secrets (locally: .streamlit/secrets.toml)
  Local cache: .cache/<sha256>.json  (avoids repeat API calls)
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- A [Groq API key](https://console.groq.com) (free)
- A Google Cloud project with Sheets + Drive APIs enabled and a service account key
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords)

### Steps

```bash
# 1. Clone and install
git clone https://github.com/rotogeek/smartinvoice-ai.git
cd smartinvoice-ai
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Open secrets.toml and fill in your real values

# 3. Run
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Secrets reference

See `.streamlit/secrets.toml.example` for the full template.
The `[gcp_service_account]` section must match your downloaded Google service account JSON exactly — use `\n` escape sequences in the `private_key` field, not real newlines.

---

## Deploying to Streamlit Community Cloud

1. Fork or push to a public GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Point at `app.py` on the `main` branch
4. Paste your `secrets.toml` contents into **Settings → Secrets**
5. Deploy — the app boots in ~60 seconds

---

## Project Structure

```
smartinvoice-ai/
├── app.py                        # Streamlit UI + orchestration
├── extraction.py                 # Groq vision extraction
├── validation.py                 # SA VAT business rules
├── sheets.py                     # Google Sheets logging
├── email_notify.py               # Gmail SMTP notifications
├── requirements.txt              # Pinned dependencies
├── .streamlit/
│   └── secrets.toml.example      # Secrets template (safe to commit)
└── sample_invoices/              # Test invoices (gitignored)
```

---

## What I Learned

Building this end-to-end in a weekend forced a few interesting decisions:

- **Groq's `response_format=json_object`** makes structured extraction reliable — without it, the model sometimes wraps JSON in markdown code fences
- **PDFs need a rendering step** before sending to a vision model — PyMuPDF renders each page to PNG at 2× zoom, which gives the model clean text to read
- **Streamlit secrets use TOML** — Google's PEM private keys have `\n` sequences that corrupt silently if a text editor substitutes Unicode characters during copy-paste
- **`st.cache_resource`** is the right tool for the Sheets connection — it survives reruns without re-authenticating

---

_Built in one weekend by Rotondwa Mukwevho_
