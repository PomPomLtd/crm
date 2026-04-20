"""Env-driven configuration.

Loads .env from the _mailer/ directory, then exposes a Config dataclass.
Anything secret (tokens, signing keys) lives only in .env — never in code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

MAILER_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = MAILER_ROOT.parent


def load_env(env_path: Optional[Path] = None) -> None:
    path = env_path or (MAILER_ROOT / ".env")
    if path.exists():
        load_dotenv(path)


@dataclass(frozen=True)
class Config:
    postmark_token: str
    postmark_from_email: str
    postmark_from_name: str
    postmark_stream: str
    postmark_webhook_secret: str

    base_url: str
    token_secret: str

    db_path: Path

    sender_legal_name: str
    sender_legal_address: str
    sender_reply_to: str

    rate_per_minute: int
    daily_cap: int

    dashboard_user: str
    dashboard_pass: str

    conversion_token: str

    @classmethod
    def from_env(cls) -> "Config":
        def req(name: str) -> str:
            v = os.environ.get(name, "").strip()
            if not v:
                raise SystemExit(
                    f"Missing required env var {name}. Copy _mailer/.env.example to _mailer/.env and fill it in."
                )
            return v

        def opt(name: str, default: str = "") -> str:
            return os.environ.get(name, default).strip()

        db_path = Path(opt("MAILER_DB_PATH", str(MAILER_ROOT / "state" / "mailer.db")))
        if not db_path.is_absolute():
            db_path = (MAILER_ROOT / db_path).resolve()

        return cls(
            postmark_token=req("POSTMARK_SERVER_TOKEN"),
            postmark_from_email=req("POSTMARK_FROM_EMAIL"),
            postmark_from_name=opt("POSTMARK_FROM_NAME", "Pom Pom GmbH"),
            postmark_stream=opt("POSTMARK_STREAM", "outbound"),
            postmark_webhook_secret=opt("POSTMARK_WEBHOOK_SECRET", ""),
            base_url=req("MAILER_BASE_URL").rstrip("/"),
            token_secret=req("MAILER_TOKEN_SECRET"),
            db_path=db_path,
            sender_legal_name=opt("SENDER_LEGAL_NAME", "Pom Pom GmbH"),
            sender_legal_address=opt("SENDER_LEGAL_ADDRESS", ""),
            sender_reply_to=opt("SENDER_REPLY_TO", ""),
            rate_per_minute=int(opt("MAILER_RATE_PER_MINUTE", "300")),
            daily_cap=int(opt("MAILER_DAILY_CAP", "500")),
            dashboard_user=opt("MAILER_DASHBOARD_USER", ""),
            dashboard_pass=opt("MAILER_DASHBOARD_PASS", ""),
            conversion_token=opt("MAILER_CONVERSION_TOKEN", ""),
        )
