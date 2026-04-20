from pathlib import Path

import pytest

from mailer import db


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    p = tmp_path / "mailer.db"
    db.init_schema(p)
    return p


def test_create_and_get_campaign(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(
            conn, name="c1", from_email="a@b.ch", from_name="A",
            subject_a="sA", subject_b="sB", subject_c="sC",
        )
        assert cid > 0
        row = db.get_campaign(conn, "c1")
        assert row is not None
        assert row["name"] == "c1"


def test_recipient_unique_per_campaign(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(conn, name="c", from_email="a@b.ch",
                                 from_name="A", subject_a="s", subject_b="s", subject_c="s")
        rid1 = db.upsert_recipient(conn, campaign_id=cid, email="x@x.ch", variant="A")
        rid2 = db.upsert_recipient(conn, campaign_id=cid, email="x@x.ch", variant="B")
        assert rid1 == rid2  # same row
        row = conn.execute("SELECT variant FROM recipients WHERE id=?", (rid1,)).fetchone()
        assert row["variant"] == "A"  # original variant kept


def test_pending_excludes_already_sent(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(conn, name="c", from_email="a@b.ch",
                                 from_name="A", subject_a="s", subject_b="s", subject_c="s")
        rid = db.upsert_recipient(conn, campaign_id=cid, email="x@x.ch", variant="A")
        assert len(db.pending_recipients(conn, campaign_id=cid)) == 1
        db.record_send(conn, recipient_id=rid, campaign_id=cid, variant="A", status="sent", postmark_message_id="m1")
        assert len(db.pending_recipients(conn, campaign_id=cid)) == 0


def test_pending_excludes_opted_out(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(conn, name="c", from_email="a@b.ch",
                                 from_name="A", subject_a="s", subject_b="s", subject_c="s")
        db.upsert_recipient(conn, campaign_id=cid, email="x@x.ch", variant="A")
        db.add_opt_out(conn, email="X@X.CH", reason="user", source="web")
        assert len(db.pending_recipients(conn, campaign_id=cid)) == 0


def test_opt_out_is_case_insensitive(db_path: Path):
    with db.connect(db_path) as conn:
        db.add_opt_out(conn, email="Foo@Bar.ch", reason="user", source="web")
        assert db.is_opted_out(conn, "foo@bar.ch")
        assert db.is_opted_out(conn, "FOO@BAR.CH")


def test_sends_unique_per_recipient(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(conn, name="c", from_email="a@b.ch",
                                 from_name="A", subject_a="s", subject_b="s", subject_c="s")
        rid = db.upsert_recipient(conn, campaign_id=cid, email="x@x.ch", variant="A")
        db.record_send(conn, recipient_id=rid, campaign_id=cid, variant="A", status="sent", postmark_message_id="m1")
        db.record_send(conn, recipient_id=rid, campaign_id=cid, variant="A", status="sent", postmark_message_id="m2")
        rows = conn.execute("SELECT postmark_message_id FROM sends WHERE recipient_id=?", (rid,)).fetchall()
        assert len(rows) == 1
        assert rows[0]["postmark_message_id"] == "m1"


def test_stats_counts(db_path: Path):
    with db.connect(db_path) as conn:
        cid = db.create_campaign(conn, name="c", from_email="a@b.ch",
                                 from_name="A", subject_a="s", subject_b="s", subject_c="s")
        r1 = db.upsert_recipient(conn, campaign_id=cid, email="a@x.ch", variant="A")
        r2 = db.upsert_recipient(conn, campaign_id=cid, email="b@x.ch", variant="A")
        r3 = db.upsert_recipient(conn, campaign_id=cid, email="c@x.ch", variant="B")

        db.record_send(conn, recipient_id=r1, campaign_id=cid, variant="A", status="sent", postmark_message_id="m1")
        db.record_send(conn, recipient_id=r2, campaign_id=cid, variant="A", status="failed", error="bad")
        db.record_send(conn, recipient_id=r3, campaign_id=cid, variant="B", status="sent", postmark_message_id="m3")

        # one open on r1
        send_row = db.send_by_message_id(conn, "m1")
        db.record_open(conn, send_id=send_row["id"], user_agent="ua", ip="1.2.3.4", platform="desktop", raw_json="{}")

    with db.connect(db_path) as conn:
        stats = db.campaign_stats(conn, cid)

    assert stats["A"]["sent"] == 1
    assert stats["A"]["failed"] == 1
    assert stats["A"]["opened"] == 1
    assert stats["B"]["sent"] == 1
    assert stats["B"]["opened"] == 0
