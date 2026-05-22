#!/usr/bin/env python3
"""
Quick CLI test for the extraction module.

Usage:
    python test_extraction.py path/to/invoice.pdf
    python test_extraction.py path/to/invoice.png

The script reads GROQ_API_KEY from .streamlit/secrets.toml automatically
if it is not already set in the environment.
"""
import json
import mimetypes
import os
import sys
from pathlib import Path


def _load_key_from_secrets() -> None:
    if os.environ.get("GROQ_API_KEY"):
        return
    secrets_path = Path(".streamlit/secrets.toml")
    if not secrets_path.exists():
        return
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        print("tomllib not available — set GROQ_API_KEY in your environment instead.")
        return
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    key = secrets.get("GROQ_API_KEY", "")
    if key:
        os.environ["GROQ_API_KEY"] = key


_MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python test_extraction.py <path/to/invoice>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    _load_key_from_secrets()

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        mime_type = _MIME_MAP.get(path.suffix.lower(), "image/jpeg")

    print(f"File : {path.name}")
    print(f"Type : {mime_type}")
    print("Extracting...\n")

    from extraction import extract_invoice

    result = extract_invoice(path.read_bytes(), mime_type)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
