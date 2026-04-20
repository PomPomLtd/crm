"""Dashboard + canvas Basic Auth gate."""
import base64
import os
from pathlib import Path

import pytest

from mailer.config import Config
from mailer.webhook import create_app


def _config(tmp_path: Path, *, user: str = "", pw: str = "") -> Config:
    return Config(
        postmark_token="tok",
        postmark_from_email="hello@meditransfer.ch",
        postmark_from_name="MediTransfer",
        postmark_stream="broadcast",
        postmark_webhook_secret="",
        base_url="https://test.example.com",
        token_secret="t",
        db_path=tmp_path / "mailer.db",
        sender_legal_name="x",
        sender_legal_address="x",
        sender_reply_to="x@x.ch",
        rate_per_minute=300,
        daily_cap=500,
        dashboard_user=user,
        dashboard_pass=pw,
        conversion_token="",
    )


def _basic(user: str, pw: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()


@pytest.mark.parametrize("path", ["/dashboard", "/dashboard/c/1", "/canvas", "/canvas/preview/01-der-brief"])
def test_returns_404_when_no_creds_configured(tmp_path: Path, path: str):
    app = create_app(_config(tmp_path))
    rv = app.test_client().get(path)
    assert rv.status_code == 404


@pytest.mark.parametrize("path", ["/dashboard", "/canvas"])
def test_returns_401_with_no_auth_header(tmp_path: Path, path: str):
    app = create_app(_config(tmp_path, user="admin", pw="secret123"))
    rv = app.test_client().get(path)
    assert rv.status_code == 401
    assert rv.headers.get("WWW-Authenticate", "").startswith("Basic")


def test_returns_401_with_wrong_password(tmp_path: Path):
    app = create_app(_config(tmp_path, user="admin", pw="secret123"))
    rv = app.test_client().get("/dashboard", headers={"Authorization": _basic("admin", "wrong")})
    assert rv.status_code == 401


def test_accepts_valid_credentials(tmp_path: Path):
    app = create_app(_config(tmp_path, user="admin", pw="secret123"))
    rv = app.test_client().get("/dashboard", headers={"Authorization": _basic("admin", "secret123")})
    assert rv.status_code == 200


def test_public_routes_unaffected(tmp_path: Path):
    app = create_app(_config(tmp_path, user="admin", pw="secret123"))
    client = app.test_client()
    assert client.get("/").status_code == 200
    # /unsubscribe with bad token still renders the error page (200), not a 401
    assert client.get("/unsubscribe?t=garbage").status_code == 200
