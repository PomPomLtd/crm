"""SQLite state store.

One file, idempotent schema. Every write that matters (sends, opens, bounces,
opt_outs) is durable so a crash never double-sends.

Schema summary:
  campaigns    — one row per campaign, holds subjects + template names
  recipients   — per-campaign recipient list with assigned variant
  sends        — one row per Postmark message attempt
  opens        — open events (may receive multiple, we track first_open + count)
  bounces      — bounce/spam complaint events
  opt_outs     — global suppression list (unique email)
"""

from __future__ import annotations

import contextlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    from_email TEXT NOT NULL,
    from_name TEXT NOT NULL,
    subject_a TEXT NOT NULL,
    subject_b TEXT NOT NULL,
    subject_c TEXT NOT NULL,
    template_a TEXT NOT NULL DEFAULT 'A',
    template_b TEXT NOT NULL DEFAULT 'B',
    template_c TEXT NOT NULL DEFAULT 'C',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    entry_id INTEGER,
    section TEXT,
    canton TEXT,
    profession TEXT,
    has_referral INTEGER,
    title TEXT,
    url TEXT,
    bucket TEXT,
    variant TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE(campaign_id, email)
);

CREATE INDEX IF NOT EXISTS idx_recipients_campaign ON recipients(campaign_id);
CREATE INDEX IF NOT EXISTS idx_recipients_variant ON recipients(campaign_id, variant);

CREATE TABLE IF NOT EXISTS sends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id INTEGER NOT NULL REFERENCES recipients(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    variant TEXT NOT NULL,
    postmark_message_id TEXT,
    status TEXT NOT NULL,
    sent_at TEXT,
    error TEXT,
    UNIQUE(recipient_id)
);

CREATE INDEX IF NOT EXISTS idx_sends_campaign ON sends(campaign_id);
CREATE INDEX IF NOT EXISTS idx_sends_message ON sends(postmark_message_id);
CREATE INDEX IF NOT EXISTS idx_sends_status ON sends(campaign_id, status);

CREATE TABLE IF NOT EXISTS opens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    send_id INTEGER NOT NULL REFERENCES sends(id) ON DELETE CASCADE,
    received_at TEXT NOT NULL,
    user_agent TEXT,
    ip TEXT,
    platform TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_opens_send ON opens(send_id);

CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    send_id INTEGER NOT NULL REFERENCES sends(id) ON DELETE CASCADE,
    url TEXT,
    click_location TEXT,
    received_at TEXT NOT NULL,
    user_agent TEXT,
    ip TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_clicks_send ON clicks(send_id);

CREATE TABLE IF NOT EXISTS bounces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    send_id INTEGER REFERENCES sends(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    bounce_type TEXT,
    inactive INTEGER,
    received_at TEXT NOT NULL,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_bounces_email ON bounces(email);

CREATE TABLE IF NOT EXISTS opt_outs (
    email TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    reason TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
    recipient_id INTEGER REFERENCES recipients(id) ON DELETE SET NULL,
    variant TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    email TEXT,
    conversion_type TEXT,
    value_cents INTEGER,
    received_at TEXT NOT NULL,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_conversions_campaign ON conversions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_conversions_recipient ON conversions(recipient_id);
CREATE INDEX IF NOT EXISTS idx_conversions_email ON conversions(email);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextlib.contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


# ---- campaigns ----

def create_campaign(
    conn: sqlite3.Connection,
    *,
    name: str,
    from_email: str,
    from_name: str,
    subject_a: str,
    subject_b: str,
    subject_c: str,
    notes: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO campaigns (name, created_at, from_email, from_name,
                                  subject_a, subject_b, subject_c, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, _now(), from_email, from_name, subject_a, subject_b, subject_c, notes),
    )
    return int(cur.lastrowid)


def get_campaign(conn: sqlite3.Connection, name: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM campaigns WHERE name = ?", (name,)).fetchone()


# ---- recipients ----

def upsert_recipient(
    conn: sqlite3.Connection,
    *,
    campaign_id: int,
    email: str,
    variant: str,
    entry_id: Optional[int] = None,
    section: Optional[str] = None,
    canton: Optional[str] = None,
    profession: Optional[str] = None,
    has_referral: Optional[bool] = None,
    title: Optional[str] = None,
    url: Optional[str] = None,
    bucket: Optional[str] = None,
) -> int:
    """Insert if new; otherwise leave existing row (and its variant) alone.

    Returns the recipient id. We never re-bucket an existing recipient — once
    they've been assigned a variant, that's the variant they stay on for the
    whole campaign, even if the target list is rebuilt mid-flight.
    """
    existing = conn.execute(
        "SELECT id FROM recipients WHERE campaign_id = ? AND email = ?",
        (campaign_id, email),
    ).fetchone()
    if existing:
        return int(existing["id"])

    cur = conn.execute(
        """INSERT INTO recipients
           (campaign_id, email, entry_id, section, canton, profession,
            has_referral, title, url, bucket, variant, added_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            campaign_id, email, entry_id, section, canton, profession,
            1 if has_referral else 0 if has_referral is not None else None,
            title, url, bucket, variant, _now(),
        ),
    )
    return int(cur.lastrowid)


def pending_recipients(
    conn: sqlite3.Connection,
    *,
    campaign_id: int,
    limit: Optional[int] = None,
    variant: Optional[str] = None,
) -> list[sqlite3.Row]:
    """Recipients with no send row yet AND no opt-out. Ordered by id."""
    sql = """
        SELECT r.*
        FROM recipients r
        LEFT JOIN sends s ON s.recipient_id = r.id
        LEFT JOIN opt_outs o ON LOWER(o.email) = LOWER(r.email)
        WHERE r.campaign_id = ?
          AND s.id IS NULL
          AND o.email IS NULL
    """
    params: list = [campaign_id]
    if variant:
        sql += " AND r.variant = ?"
        params.append(variant)
    sql += " ORDER BY r.id"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    return list(conn.execute(sql, params).fetchall())


# ---- sends ----

def record_send(
    conn: sqlite3.Connection,
    *,
    recipient_id: int,
    campaign_id: int,
    variant: str,
    status: str,
    postmark_message_id: Optional[str] = None,
    error: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """INSERT OR IGNORE INTO sends
           (recipient_id, campaign_id, variant, status, postmark_message_id, sent_at, error)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (recipient_id, campaign_id, variant, status, postmark_message_id,
         _now() if status == "sent" else None, error),
    )
    return int(cur.lastrowid)


def send_by_message_id(
    conn: sqlite3.Connection, message_id: str
) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM sends WHERE postmark_message_id = ?", (message_id,)
    ).fetchone()


# ---- opens ----

def record_open(
    conn: sqlite3.Connection,
    *,
    send_id: int,
    user_agent: Optional[str],
    ip: Optional[str],
    platform: Optional[str],
    raw_json: Optional[str],
) -> None:
    conn.execute(
        """INSERT INTO opens (send_id, received_at, user_agent, ip, platform, raw_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (send_id, _now(), user_agent, ip, platform, raw_json),
    )


# ---- clicks ----

def record_click(
    conn: sqlite3.Connection,
    *,
    send_id: int,
    url: Optional[str],
    click_location: Optional[str],
    user_agent: Optional[str],
    ip: Optional[str],
    raw_json: Optional[str],
) -> None:
    conn.execute(
        """INSERT INTO clicks (send_id, url, click_location, received_at, user_agent, ip, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (send_id, url, click_location, _now(), user_agent, ip, raw_json),
    )


# ---- bounces ----

def record_bounce(
    conn: sqlite3.Connection,
    *,
    send_id: Optional[int],
    email: str,
    bounce_type: Optional[str],
    inactive: bool,
    raw_json: Optional[str],
) -> None:
    conn.execute(
        """INSERT INTO bounces (send_id, email, bounce_type, inactive, received_at, raw_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (send_id, email.lower(), bounce_type, 1 if inactive else 0, _now(), raw_json),
    )


# ---- opt_outs ----

def add_opt_out(
    conn: sqlite3.Connection, *, email: str, reason: str, source: str
) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO opt_outs (email, created_at, reason, source)
           VALUES (?, ?, ?, ?)""",
        (email.strip().lower(), _now(), reason, source),
    )


def is_opted_out(conn: sqlite3.Connection, email: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM opt_outs WHERE LOWER(email) = LOWER(?)", (email,)
    ).fetchone()
    return row is not None


def remove_opt_out(conn: sqlite3.Connection, email: str) -> bool:
    cur = conn.execute(
        "DELETE FROM opt_outs WHERE LOWER(email) = LOWER(?)", (email,)
    )
    return cur.rowcount > 0


def list_opt_outs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT email, created_at, reason, source FROM opt_outs ORDER BY created_at DESC"
        ).fetchall()
    )


# ---- conversions ----

def record_conversion(
    conn: sqlite3.Connection,
    *,
    campaign_id: Optional[int],
    recipient_id: Optional[int],
    variant: Optional[str],
    utm_campaign: Optional[str],
    utm_content: Optional[str],
    email: Optional[str],
    conversion_type: Optional[str],
    value_cents: Optional[int],
    raw_json: Optional[str],
) -> int:
    cur = conn.execute(
        """INSERT INTO conversions
           (campaign_id, recipient_id, variant, utm_campaign, utm_content, email,
            conversion_type, value_cents, received_at, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (campaign_id, recipient_id, variant, utm_campaign, utm_content,
         (email or "").lower() or None, conversion_type, value_cents, _now(), raw_json),
    )
    return int(cur.lastrowid)


def find_recipient_for_conversion(
    conn: sqlite3.Connection,
    *,
    campaign_id: Optional[int],
    email: Optional[str],
) -> Optional[sqlite3.Row]:
    """Look up the recipient row for a conversion event."""
    if not campaign_id or not email:
        return None
    return conn.execute(
        "SELECT * FROM recipients WHERE campaign_id = ? AND LOWER(email) = LOWER(?)",
        (campaign_id, email),
    ).fetchone()


def find_campaign_by_name(conn: sqlite3.Connection, name: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM campaigns WHERE name = ?", (name,)).fetchone()


# ---- stats ----

def campaign_stats(conn: sqlite3.Connection, campaign_id: int) -> dict:
    """Per-variant sent / delivered / opened / bounced / unsubscribed counts."""
    rows = conn.execute(
        """
        SELECT
          r.variant,
          COUNT(r.id) AS total,
          SUM(CASE WHEN s.status = 'sent' THEN 1 ELSE 0 END) AS sent,
          SUM(CASE WHEN s.status = 'failed' THEN 1 ELSE 0 END) AS failed,
          SUM(CASE WHEN EXISTS (SELECT 1 FROM opens o WHERE o.send_id = s.id) THEN 1 ELSE 0 END) AS opened,
          SUM(CASE WHEN EXISTS (SELECT 1 FROM clicks c WHERE c.send_id = s.id) THEN 1 ELSE 0 END) AS clicked,
          SUM(CASE WHEN EXISTS (SELECT 1 FROM conversions cv WHERE cv.recipient_id = r.id) THEN 1 ELSE 0 END) AS converted,
          SUM((SELECT COALESCE(SUM(value_cents), 0) FROM conversions cv WHERE cv.recipient_id = r.id)) AS conversion_value_cents,
          SUM(CASE WHEN EXISTS (SELECT 1 FROM bounces b WHERE b.send_id = s.id) THEN 1 ELSE 0 END) AS bounced,
          SUM(CASE WHEN EXISTS (SELECT 1 FROM opt_outs oo WHERE LOWER(oo.email) = LOWER(r.email)) THEN 1 ELSE 0 END) AS unsubscribed
        FROM recipients r
        LEFT JOIN sends s ON s.recipient_id = r.id
        WHERE r.campaign_id = ?
        GROUP BY r.variant
        ORDER BY r.variant
        """,
        (campaign_id,),
    ).fetchall()
    return {r["variant"]: dict(r) for r in rows}
