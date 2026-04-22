import json
from pathlib import Path

from mailer import targets


def _write_checkpoint(path: Path, entries: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def test_dedupes_by_email(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "A", "url": "https://a/",
         "status": "success",
         "emails": {"priority": ["info@chain.ch"], "general": [], "other": []},
         "referral": {"found": False}},
        {"entry_id": 2, "section": "clinics", "title": "B", "url": "https://b/",
         "status": "success",
         "emails": {"priority": ["info@chain.ch"], "general": [], "other": []},
         "referral": {"found": False}},
    ])
    out = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, bucket="priority", enrich=False,
    )
    assert len(out) == 1
    assert out[0].email == "info@chain.ch"
    assert out[0].entry_id == 1  # first wins


def test_filters_by_section(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "A", "url": "",
         "status": "success",
         "emails": {"priority": ["a@x.ch"], "general": [], "other": []},
         "referral": {"found": False}},
        {"entry_id": 2, "section": "hospitals", "title": "B", "url": "",
         "status": "success",
         "emails": {"priority": ["b@x.ch"], "general": [], "other": []},
         "referral": {"found": False}},
    ])
    only_hosp = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, sections=["hospitals"],
        bucket="priority", enrich=False,
    )
    assert [r.email for r in only_hosp] == ["b@x.ch"]


def test_filters_by_has_referral(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "", "url": "",
         "status": "success",
         "emails": {"priority": ["a@x.ch"], "general": [], "other": []},
         "referral": {"found": True, "methods": ["form"]}},
        {"entry_id": 2, "section": "clinics", "title": "", "url": "",
         "status": "success",
         "emails": {"priority": ["b@x.ch"], "general": [], "other": []},
         "referral": {"found": False}},
    ])
    refs = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, has_referral=True,
        bucket="priority", enrich=False,
    )
    assert [r.email for r in refs] == ["a@x.ch"]
    assert refs[0].has_referral is True


def test_bucket_priority_only(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "", "url": "",
         "status": "success",
         "emails": {"priority": ["info@x.ch"], "general": ["dr.meier@x.ch"], "other": ["random@x.ch"]},
         "referral": {"found": False}},
    ])
    out = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, bucket="priority", enrich=False,
    )
    assert [r.email for r in out] == ["info@x.ch"]


def test_bucket_priority_plus_general(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "", "url": "",
         "status": "success",
         "emails": {"priority": ["info@x.ch"], "general": ["dr.meier@x.ch"], "other": ["random@x.ch"]},
         "referral": {"found": False}},
    ])
    out = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, bucket="priority+general", enrich=False,
    )
    assert {r.email for r in out} == {"info@x.ch", "dr.meier@x.ch"}


def test_skips_no_emails(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "", "url": "",
         "status": "no_emails", "emails": {"priority": [], "general": [], "other": []},
         "referral": {"found": False}},
    ])
    out = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, bucket="priority", enrich=False,
    )
    assert out == []


def test_one_per_domain_collapses_multiple_addresses_at_same_domain(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "A", "url": "",
         "status": "success",
         "emails": {"priority": ["info@praxis.ch", "kontakt@praxis.ch"],
                    "general": ["dr.meier@praxis.ch"], "other": []},
         "referral": {"found": False}},
        {"entry_id": 2, "section": "clinics", "title": "B", "url": "",
         "status": "success",
         "emails": {"priority": ["info@other.ch"], "general": [], "other": []},
         "referral": {"found": False}},
    ])
    out = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path,
        bucket="priority+general", enrich=False, one_per_domain=True,
    )
    # One address per domain: priority wins over general (iteration order),
    # first priority address wins over later priority at same domain.
    assert {r.email for r in out} == {"info@praxis.ch", "info@other.ch"}


def test_one_per_domain_off_by_default_keeps_everything(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "", "url": "",
         "status": "success",
         "emails": {"priority": ["info@praxis.ch", "kontakt@praxis.ch"],
                    "general": [], "other": []},
         "referral": {"found": False}},
    ])
    out = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, bucket="priority", enrich=False,
    )
    assert {r.email for r in out} == {"info@praxis.ch", "kontakt@praxis.ch"}


def test_write_read_roundtrip(tmp_path: Path):
    cp = tmp_path / "cp.jsonl"
    _write_checkpoint(cp, [
        {"entry_id": 1, "section": "clinics", "title": "Praxis Muster", "url": "https://p.ch",
         "status": "success",
         "emails": {"priority": ["info@p.ch"], "general": [], "other": []},
         "referral": {"found": True, "methods": ["email"]}},
    ])
    out = targets.build_recipients(
        checkpoint_path=cp, repo_root=tmp_path, bucket="priority", enrich=False,
    )
    csv_path = tmp_path / "recipients.csv"
    written = targets.write_recipients_csv(csv_path, out)
    assert written == 1
    rows = targets.read_recipients_csv(csv_path)
    assert rows[0]["email"] == "info@p.ch"
    assert rows[0]["title"] == "Praxis Muster"
    assert rows[0]["has_referral"] == "yes"
