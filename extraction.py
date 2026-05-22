import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from openai import OpenAI

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
CACHE_DIR = Path(".cache")

_PROMPT = (
    "Extract all invoice data from this image and return ONLY a valid JSON object "
    "with exactly these keys:\n"
    "- vendor_name (string)\n"
    "- invoice_number (string)\n"
    "- invoice_date (string, ISO format YYYY-MM-DD)\n"
    "- line_items (array of objects, each with: description, quantity, unit_price, total)\n"
    "- subtotal (number)\n"
    "- vat (number, use 0 if not present)\n"
    "- total_amount (number)\n"
    "- currency (string, e.g. USD, EUR, GBP)\n\n"
    "Return ONLY the JSON object. No markdown, no explanation, no code fences."
)


def _file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:20]


def _load_cache(h: str) -> dict | None:
    p = CACHE_DIR / f"{h}.json"
    return json.loads(p.read_text()) if p.exists() else None


def _save_cache(h: str, data: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / f"{h}.json").write_text(json.dumps(data, indent=2))


def _pdf_first_page_as_png(pdf_bytes: bytes) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    # 2× zoom gives enough resolution for clean OCR without hitting the 4 MB limit
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    return pix.tobytes("png")


def extract_invoice(
    file_bytes: bytes,
    mime_type: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    h = _file_hash(file_bytes)
    cached = _load_cache(h)
    if cached is not None:
        return cached

    if mime_type == "application/pdf":
        image_bytes = _pdf_first_page_as_png(file_bytes)
        image_mime = "image/png"
    else:
        image_bytes = file_bytes
        image_mime = mime_type

    b64 = base64.b64encode(image_bytes).decode()
    size_mb = len(b64) / (1024 * 1024)
    if size_mb > 4:
        raise ValueError(
            f"Encoded image is {size_mb:.1f} MB — Groq limit is 4 MB base64. "
            "Try a lower-resolution scan."
        )

    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not set in environment or passed as argument.")

    client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{image_mime};base64,{b64}"},
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned malformed JSON.\nError: {exc}\nRaw output:\n{raw}"
        ) from exc

    _save_cache(h, result)
    return result
