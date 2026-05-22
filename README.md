# SmartInvoice AI

AI-powered invoice processor: upload a PDF or image, extract structured data
with a Groq vision model, validate with business rules, log to Google Sheets,
and receive an email summary.

_Full documentation coming in Step 8._

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill in secrets.toml with your real keys
streamlit run app.py
```

## Deployment

Deploys to [Streamlit Community Cloud](https://streamlit.io/cloud) (free tier).
Set secrets via the Streamlit Cloud dashboard — never commit `secrets.toml`.
