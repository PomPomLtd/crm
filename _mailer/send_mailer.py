#!/usr/bin/env python3
"""Entry shim for the mailer CLI (mirrors the scraper's find_clinic_emails.py pattern)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailer.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
