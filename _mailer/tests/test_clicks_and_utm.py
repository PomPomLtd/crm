"""Click tracking + UTM CTA URL tests."""
from pathlib import Path

import pytest

from mailer import db
from mailer.render import KNOWN_TEMPLATES, cta_url_for, render


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    p = tmp_path / "mailer.db"
    db.init_schema(p)
    return p


def test_cta_url_includes_utm_params():
    url = cta_url_for(campaign_name="cold-2026-04", template_name="01-der-brief")
    assert "utm_source=meditransfer-mailer" in url
    assert "utm_medium=email" in url
    assert "utm_campaign=cold-2026-04" in url
    assert "utm_content=01-der-brief" in url
    assert url.startswith("https://meditransfer.ch/?code=WELCOME30")


def test_cta_url_url_encodes_unsafe_campaign_name():
    url = cta_url_for(campaign_name="space test", template_name="01-der-brief")
    assert "utm_campaign=space+test" in url or "utm_campaign=space%20test" in url


@pytest.mark.parametrize("template_name", KNOWN_TEMPLATES)
def test_cta_url_appears_in_rendered_template(template_name: str):
    r = render(
        template_name=template_name,
        subject="s",
        recipient={"email": "x@x.ch"},
        campaign_id=1,
        campaign_name="test-camp",
        base_url="https://example.com",
        token_secret="s",
    )
    assert "utm_campaign=test-camp" in r.html
    assert f"utm_content={template_name}" in r.html
    assert "utm_campaign=test-camp" in r.text
    assert f"utm_content={template_name}" in r.text


def test_record_click_then_aggregate(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(conn, name="c", from_email="a@b.ch", from_name="A",
                                 subject_a="s", subject_b="s", subject_c="s")
        rid = db.upsert_recipient(conn, campaign_id=cid, email="x@x.ch", variant="A")
        db.record_send(conn, recipient_id=rid, campaign_id=cid, variant="A", status="sent",
                       postmark_message_id="m1")
        send = db.send_by_message_id(conn, "m1")
        db.record_click(conn, send_id=send["id"],
                        url="https://meditransfer.ch/?code=WELCOME30",
                        click_location="HTML", user_agent="ua", ip="1.2.3.4", raw_json="{}")
        db.record_click(conn, send_id=send["id"],
                        url="https://meditransfer.ch/?code=WELCOME30",
                        click_location="HTML", user_agent="ua", ip="1.2.3.4", raw_json="{}")

        stats = db.campaign_stats(conn, cid)
        assert stats["A"]["clicked"] == 1
        # Two raw clicks but unique recipient count is 1
        rows = conn.execute("SELECT COUNT(*) AS n FROM clicks").fetchone()
        assert rows["n"] == 2
