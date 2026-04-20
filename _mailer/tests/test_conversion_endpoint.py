"""Conversion endpoint + attribution + dashboard accounting."""
from pathlib import Path

import pytest

from mailer import db
from mailer.config import Config
from mailer.webhook import create_app


def _config(tmp_path: Path, *, token: str = "conv-secret-123") -> Config:
    return Config(
        postmark_token="tok", postmark_from_email="hello@meditransfer.ch",
        postmark_from_name="MediTransfer", postmark_stream="broadcast",
        postmark_webhook_secret="",
        base_url="https://test.example.com", token_secret="t",
        db_path=tmp_path / "mailer.db",
        sender_legal_name="x", sender_legal_address="x", sender_reply_to="x@x.ch",
        rate_per_minute=300, daily_cap=500,
        dashboard_user="", dashboard_pass="",
        conversion_token=token,
    )


def _seed_campaign(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(conn, name="test-06", from_email="a@b.ch", from_name="A",
                                 subject_a="s", subject_b="s", subject_c="s")
        conn.execute("UPDATE campaigns SET template_a=?, template_b=?, template_c=? WHERE id=?",
                     ("01-der-brief", "02-hero-cta", "03-stunden-zu-minuten", cid))
        rid = db.upsert_recipient(conn, campaign_id=cid, email="user@clinic.ch", variant="C")
        return cid, rid


def test_returns_404_when_no_token_configured(tmp_path: Path):
    cfg = _config(tmp_path, token="")
    app = create_app(cfg)
    rv = app.test_client().post("/api/conversion", json={"type": "signup"})
    assert rv.status_code == 404


def test_returns_401_with_wrong_token(tmp_path: Path):
    cfg = _config(tmp_path)
    app = create_app(cfg)
    rv = app.test_client().post(
        "/api/conversion",
        json={"type": "signup"},
        headers={"X-Conversion-Token": "wrong"},
    )
    assert rv.status_code == 401


def test_full_attribution_via_email(tmp_path: Path):
    cfg = _config(tmp_path)
    app = create_app(cfg)
    cid, rid = _seed_campaign(cfg.db_path)
    rv = app.test_client().post(
        "/api/conversion",
        json={
            "utm_campaign": "test-06",
            "utm_content": "03-stunden-zu-minuten",
            "email": "USER@CLINIC.CH",
            "type": "signup",
            "value_cents": 4900,
        },
        headers={"X-Conversion-Token": "conv-secret-123"},
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert body["attributed"]["campaign_id"] == cid
    assert body["attributed"]["recipient_id"] == rid
    assert body["attributed"]["variant"] == "C"

    with db.connect(cfg.db_path) as conn:
        row = conn.execute("SELECT * FROM conversions").fetchone()
        assert row["campaign_id"] == cid
        assert row["recipient_id"] == rid
        assert row["variant"] == "C"
        assert row["email"] == "user@clinic.ch"
        assert row["value_cents"] == 4900
        assert row["conversion_type"] == "signup"


def test_variant_falls_back_to_utm_content_when_email_missing(tmp_path: Path):
    cfg = _config(tmp_path)
    app = create_app(cfg)
    cid, _ = _seed_campaign(cfg.db_path)
    rv = app.test_client().post(
        "/api/conversion",
        json={
            "utm_campaign": "test-06",
            "utm_content": "01-der-brief",
            "type": "signup",
        },
        headers={"X-Conversion-Token": "conv-secret-123"},
    )
    body = rv.get_json()
    assert body["attributed"]["campaign_id"] == cid
    assert body["attributed"]["recipient_id"] is None
    assert body["attributed"]["variant"] == "A"


def test_unknown_campaign_still_recorded(tmp_path: Path):
    cfg = _config(tmp_path)
    app = create_app(cfg)
    rv = app.test_client().post(
        "/api/conversion",
        json={"utm_campaign": "ghost-campaign", "type": "signup"},
        headers={"X-Conversion-Token": "conv-secret-123"},
    )
    assert rv.status_code == 200
    with db.connect(cfg.db_path) as conn:
        row = conn.execute("SELECT * FROM conversions").fetchone()
        assert row is not None
        assert row["campaign_id"] is None
        assert row["utm_campaign"] == "ghost-campaign"


def test_stats_include_conversion_count(tmp_path: Path):
    cfg = _config(tmp_path)
    app = create_app(cfg)
    cid, rid = _seed_campaign(cfg.db_path)

    # Two conversions on same recipient → counted as 1 unique converted, summed value
    client = app.test_client()
    for _ in range(2):
        client.post(
            "/api/conversion",
            json={"utm_campaign": "test-06", "email": "user@clinic.ch", "value_cents": 4900},
            headers={"X-Conversion-Token": "conv-secret-123"},
        )

    with db.connect(cfg.db_path) as conn:
        stats = db.campaign_stats(conn, cid)
    assert stats["C"]["converted"] == 1
    assert stats["C"]["conversion_value_cents"] == 9800
