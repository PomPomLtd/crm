"""Postmark batch sender.

- Talks to Postmark's REST API directly (requests) — no SDK dependency.
- Uses the `/email/batch` endpoint so we send up to 500 messages per API call.
- Records every attempt (success OR failure) in the `sends` table before moving
  on. If the process dies, a resume picks up from `pending_recipients` which
  excludes anything with a send row already.
- Enforces a per-minute rate cap (default 300/min) to stay well under
  Postmark's 10 req/s = 600/min server-side limit.
- Enforces a daily cap per campaign run.
- Adds List-Unsubscribe + List-Unsubscribe-Post headers for one-click.

Open tracking is enabled at the API level (TrackOpens=true).
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

import requests

from . import db, render
from .config import Config

POSTMARK_BATCH_ENDPOINT = "https://api.postmarkapp.com/email/batch"
BATCH_SIZE = 500
DEFAULT_TIMEOUT = 30
log = logging.getLogger("mailer.sender")


@dataclass(frozen=True)
class CampaignSpec:
    id: int
    name: str
    from_email: str
    from_name: str
    reply_to: Optional[str]
    subjects: dict[str, str]     # {"A": "...", "B": "...", "C": "..."}
    templates: dict[str, str]    # {"A": "01-der-brief", ...}


class RateLimiter:
    """Token-bucket for per-minute rate capping. Blocks until a slot is free."""

    def __init__(self, per_minute: int):
        self.per_minute = max(1, int(per_minute))
        self._timestamps: list[float] = []

    def acquire(self) -> None:
        now = time.monotonic()
        window_start = now - 60.0
        self._timestamps = [t for t in self._timestamps if t >= window_start]
        if len(self._timestamps) >= self.per_minute:
            sleep_for = 60.0 - (now - self._timestamps[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.monotonic()
            window_start = now - 60.0
            self._timestamps = [t for t in self._timestamps if t >= window_start]
        self._timestamps.append(now)


def _build_message(
    *,
    config: Config,
    campaign: CampaignSpec,
    recipient: sqlite3.Row,
) -> dict:
    variant = recipient["variant"]
    template_name = campaign.templates[variant]
    subject = campaign.subjects[variant]
    rec_ctx = {
        "email": recipient["email"],
        "title": recipient["title"] or "",
        "url": recipient["url"] or "",
        "canton": recipient["canton"] or "",
        "section": recipient["section"] or "",
        "profession": recipient["profession"] or "",
        "campaign_name": campaign.name,
    }
    rendered = render.render(
        template_name=template_name,
        subject=subject,
        recipient=rec_ctx,
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        base_url=config.base_url,
        token_secret=config.token_secret,
    )

    message: dict = {
        "From": f"{campaign.from_name} <{campaign.from_email}>",
        "To": recipient["email"],
        "Subject": rendered.subject,
        "HtmlBody": rendered.html,
        "TextBody": rendered.text,
        "MessageStream": config.postmark_stream,
        "TrackOpens": True,
        "TrackLinks": "HtmlOnly",
        "Metadata": {
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "variant": variant,
            "recipient_id": str(recipient["id"]),
        },
        "Headers": [
            {
                "Name": "List-Unsubscribe",
                "Value": f"<{rendered.unsubscribe_url}>, <mailto:{config.sender_reply_to}?subject=unsubscribe>",
            },
            {"Name": "List-Unsubscribe-Post", "Value": "List-Unsubscribe=One-Click"},
        ],
    }
    if campaign.reply_to:
        message["ReplyTo"] = campaign.reply_to
    return message


def _post_batch(token: str, messages: list[dict]) -> list[dict]:
    """POST a batch; returns Postmark's per-message response list."""
    resp = requests.post(
        POSTMARK_BATCH_ENDPOINT,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": token,
        },
        data=json.dumps(messages),
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def send_campaign(
    config: Config,
    campaign: CampaignSpec,
    *,
    limit: Optional[int] = None,
    dry_run: bool = False,
    progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """Run one pass over pending recipients. Returns {sent, failed, skipped}.

    Resumable: re-running picks up where we left off (pending_recipients
    skips recipients that already have a send row OR are opted out).
    The per-campaign daily cap is enforced here, not across runs — if you
    want strict 500-per-day-forever you must schedule one run per day.
    """
    emit = progress or (lambda s: None)
    limiter = RateLimiter(config.rate_per_minute)
    effective_limit = limit if limit is not None else config.daily_cap
    stats = {"sent": 0, "failed": 0, "skipped": 0, "batches": 0}

    with db.connect(config.db_path) as conn:
        pending = db.pending_recipients(conn, campaign_id=campaign.id, limit=effective_limit)
        emit(f"Pending: {len(pending)} recipient(s). limit={effective_limit} dry_run={dry_run}")

        for i in range(0, len(pending), BATCH_SIZE):
            chunk = pending[i : i + BATCH_SIZE]
            messages = [_build_message(config=config, campaign=campaign, recipient=r) for r in chunk]

            if dry_run:
                for rec, msg in zip(chunk, messages):
                    db.record_send(
                        conn,
                        recipient_id=rec["id"],
                        campaign_id=campaign.id,
                        variant=rec["variant"],
                        status="dry_run",
                    )
                    emit(f"[DRY] would send to {rec['email']} (variant={rec['variant']}, subject={msg['Subject']!r})")
                stats["skipped"] += len(chunk)
                stats["batches"] += 1
                continue

            for _ in chunk:
                limiter.acquire()

            try:
                responses = _post_batch(config.postmark_token, messages)
            except requests.RequestException as exc:
                emit(f"Batch POST failed ({type(exc).__name__}): {exc}. Marking {len(chunk)} as failed.")
                for rec in chunk:
                    db.record_send(
                        conn,
                        recipient_id=rec["id"],
                        campaign_id=campaign.id,
                        variant=rec["variant"],
                        status="failed",
                        error=str(exc)[:500],
                    )
                stats["failed"] += len(chunk)
                stats["batches"] += 1
                continue

            for rec, result in zip(chunk, responses):
                error_code = result.get("ErrorCode", 0)
                if error_code == 0:
                    db.record_send(
                        conn,
                        recipient_id=rec["id"],
                        campaign_id=campaign.id,
                        variant=rec["variant"],
                        status="sent",
                        postmark_message_id=result.get("MessageID"),
                    )
                    stats["sent"] += 1
                else:
                    db.record_send(
                        conn,
                        recipient_id=rec["id"],
                        campaign_id=campaign.id,
                        variant=rec["variant"],
                        status="failed",
                        error=f"{error_code}: {result.get('Message', '')}"[:500],
                    )
                    stats["failed"] += 1

            stats["batches"] += 1
            emit(f"Batch {stats['batches']}: sent {stats['sent']} / failed {stats['failed']} so far")

    return stats
