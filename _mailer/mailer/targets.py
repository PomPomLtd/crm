"""Build a recipients CSV from the scraper's JSONL checkpoint.

Pipeline:
  1. Read every line of `_scrapers/results/clinic_emails_checkpoint.jsonl`.
  2. Optionally filter by section and referral presence.
  3. Expand to one row per (entry, email) using the chosen bucket
     ("priority" only, "priority+general", or "all").
  4. Dedupe by lowercased email, keeping the FIRST occurrence so chain sites
     that cross-list an address don't repeat.
  5. Enrich with canton + profession from Craft DB (one query, one pass).
  6. Write CSV sorted by section then entry_id.

Canton + profession live in the Craft entry's content JSON by UID. Rather
than hard-coding each section's field UID here, we pull the full content
JSON and heuristically pluck the canton (a Swiss 2-letter cantonal code or
recognised canton name) and profession (handled per-section heuristic).
Good enough for initial segmentation; can be replaced with explicit UIDs
once they're documented.
"""

from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

CANTONS_CH: dict[str, str] = {
    "zh": "ZH", "be": "BE", "lu": "LU", "ur": "UR", "sz": "SZ", "ow": "OW",
    "nw": "NW", "gl": "GL", "zg": "ZG", "fr": "FR", "so": "SO", "bs": "BS",
    "bl": "BL", "sh": "SH", "ar": "AR", "ai": "AI", "sg": "SG", "gr": "GR",
    "ag": "AG", "tg": "TG", "ti": "TI", "vd": "VD", "vs": "VS", "ne": "NE",
    "ge": "GE", "ju": "JU",
    "zürich": "ZH", "zuerich": "ZH", "bern": "BE", "luzern": "LU",
    "basel-stadt": "BS", "basel-landschaft": "BL", "st. gallen": "SG",
    "st.gallen": "SG", "sankt gallen": "SG", "graubünden": "GR",
    "graubunden": "GR", "tessin": "TI", "ticino": "TI", "waadt": "VD",
    "vaud": "VD", "wallis": "VS", "valais": "VS", "neuenburg": "NE",
    "neuchâtel": "NE", "neuchatel": "NE", "genf": "GE", "genève": "GE",
    "geneve": "GE", "genf / geneve": "GE",
    "freiburg": "FR", "fribourg": "FR", "schwyz": "SZ", "obwalden": "OW",
    "nidwalden": "NW", "glarus": "GL", "zug": "ZG", "solothurn": "SO",
    "schaffhausen": "SH", "appenzell ausserrhoden": "AR",
    "appenzell innerrhoden": "AI", "aargau": "AG", "thurgau": "TG",
    "uri": "UR", "jura": "JU",
}

BUCKET_CHOICES = ("priority", "priority+general", "all")


@dataclass(frozen=True)
class Recipient:
    email: str
    entry_id: int
    section: str
    title: str
    url: str
    bucket: str
    has_referral: bool
    canton: Optional[str]
    profession: Optional[str]


def _normalize_canton(value: str) -> Optional[str]:
    key = value.strip().lower().rstrip(".").strip()
    return CANTONS_CH.get(key)


def _extract_canton_and_profession(content: Any) -> tuple[Optional[str], Optional[str]]:
    """Heuristic: walk the content JSON and identify canton + profession.

    Craft stores content as a dict keyed by field-layout-element UIDs. Most
    simple fields are raw string/int/bool values; URL and other typed fields
    are dicts like ``{"type": "url", "value": "https://..."}``. We inspect
    both forms, pull the plain string content, and match it against known
    canton tokens for canton, or accept the first sufficiently long, non-URL,
    non-canton, non-phone string value as profession.

    This is a pragmatic extractor; swap it for explicit UID reads once the
    per-section field UIDs are documented.
    """
    if not isinstance(content, dict):
        return None, None

    canton: Optional[str] = None
    profession: Optional[str] = None

    for val in content.values():
        if isinstance(val, str):
            s = val.strip()
        elif isinstance(val, dict):
            if val.get("type") == "url":
                continue
            raw = val.get("value")
            s = raw.strip() if isinstance(raw, str) else ""
        else:
            continue
        if not s:
            continue

        if canton is None:
            guess = _normalize_canton(s)
            if guess:
                canton = guess
                continue

        if profession is None and 3 < len(s) < 200 and any(ch.isalpha() for ch in s):
            if _normalize_canton(s) is None and not s.startswith(("http", "+", "0")):
                # Skip obvious non-profession fields: addresses (contain digits
                # and commas), city-only fields (too short & matches no canton),
                # status enums ("new").
                if "," in s and any(ch.isdigit() for ch in s):
                    continue
                if len(s) < 8:
                    continue
                profession = s

    return canton, profession


def _bucketed_emails(entry: dict, bucket: str) -> Iterator[tuple[str, str]]:
    """Yield (email, bucket_label) pairs for this entry under the chosen rule."""
    emails = entry.get("emails") or {}
    priority = [e for e in (emails.get("priority") or []) if e]
    general = [e for e in (emails.get("general") or []) if e]
    other = [e for e in (emails.get("other") or []) if e]

    if bucket == "priority":
        for e in priority:
            yield e, "priority"
    elif bucket == "priority+general":
        for e in priority:
            yield e, "priority"
        for e in general:
            yield e, "general"
    else:  # "all"
        for e in priority:
            yield e, "priority"
        for e in general:
            yield e, "general"
        for e in other:
            yield e, "other"


def iter_checkpoint(checkpoint_path: Path) -> Iterator[dict]:
    with checkpoint_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def enrich_from_db(
    entry_ids: Iterable[int], repo_root: Path
) -> dict[int, tuple[Optional[str], Optional[str]]]:
    """Bulk-query Craft DB: returns {entry_id: (canton, profession)}."""
    ids = sorted(set(int(i) for i in entry_ids))
    if not ids:
        return {}

    out: dict[int, tuple[Optional[str], Optional[str]]] = {}
    CHUNK = 1000
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i : i + CHUNK]
        id_list = ",".join(str(x) for x in chunk)
        query = (
            "SELECT CONCAT('{\"id\":', e.id, ',\"content\":', es.content, '}') AS j "
            "FROM entries e "
            "JOIN elements_sites es ON es.elementId = e.id AND es.siteId = 1 "
            f"WHERE e.id IN ({id_list})"
        )
        proc = subprocess.run(
            ["ddev", "mysql", "db", "--skip-column-names", "--raw", "-e", query],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        if proc.returncode != 0:
            raise RuntimeError(f"ddev mysql failed:\n{proc.stderr}")
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            eid = int(row["id"])
            canton, profession = _extract_canton_and_profession(row.get("content"))
            out[eid] = (canton, profession)
    return out


def build_recipients(
    *,
    checkpoint_path: Path,
    repo_root: Path,
    sections: Optional[Iterable[str]] = None,
    cantons: Optional[Iterable[str]] = None,
    profession_contains: Optional[str] = None,
    has_referral: Optional[bool] = None,
    bucket: str = "priority",
    enrich: bool = True,
    one_per_domain: bool = False,
) -> list[Recipient]:
    if bucket not in BUCKET_CHOICES:
        raise ValueError(f"bucket must be one of {BUCKET_CHOICES}")

    section_filter = set(sections) if sections else None
    canton_filter = {c.upper() for c in cantons} if cantons else None
    profession_needle = profession_contains.lower() if profession_contains else None

    # First pass: gather eligible (entry, email, bucket) tuples from the checkpoint.
    by_email: dict[str, Recipient] = {}
    entries_needing_enrich: set[int] = set()

    for entry in iter_checkpoint(checkpoint_path):
        if entry.get("status") not in ("success", "success_via_root"):
            continue
        section = entry.get("section") or ""
        if section_filter and section not in section_filter:
            continue
        referral = bool((entry.get("referral") or {}).get("found"))
        if has_referral is not None and referral != has_referral:
            continue

        entry_id = int(entry.get("entry_id", 0))
        for email, bkt in _bucketed_emails(entry, bucket):
            key = email.strip().lower()
            if not key or key in by_email:
                continue
            by_email[key] = Recipient(
                email=key,
                entry_id=entry_id,
                section=section,
                title=(entry.get("title") or ""),
                url=(entry.get("url") or ""),
                bucket=bkt,
                has_referral=referral,
                canton=None,
                profession=None,
            )
            entries_needing_enrich.add(entry_id)

    if enrich and entries_needing_enrich:
        enrichment = enrich_from_db(entries_needing_enrich, repo_root)
        for email_key, rec in list(by_email.items()):
            canton, profession = enrichment.get(rec.entry_id, (None, None))
            by_email[email_key] = Recipient(
                email=rec.email,
                entry_id=rec.entry_id,
                section=rec.section,
                title=rec.title,
                url=rec.url,
                bucket=rec.bucket,
                has_referral=rec.has_referral,
                canton=canton,
                profession=profession,
            )

    # Post-enrichment filters (canton, profession)
    recipients: list[Recipient] = []
    for rec in by_email.values():
        if canton_filter and (rec.canton or "").upper() not in canton_filter:
            continue
        if profession_needle and profession_needle not in (rec.profession or "").lower():
            continue
        recipients.append(rec)

    if one_per_domain:
        # Priority emails already win over general/other because _bucketed_emails
        # yields in priority→general→other order, so first-occurrence dedup by
        # domain keeps the best-bucket address.
        seen: set[str] = set()
        kept: list[Recipient] = []
        for rec in recipients:
            domain = rec.email.rsplit("@", 1)[-1].lower()
            if domain in seen:
                continue
            seen.add(domain)
            kept.append(rec)
        recipients = kept

    recipients.sort(key=lambda r: (r.section, r.entry_id, r.email))
    return recipients


CSV_COLUMNS = (
    "email", "entry_id", "section", "title", "url",
    "bucket", "has_referral", "canton", "profession",
)


def write_recipients_csv(path: Path, recipients: Iterable[Recipient]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for r in recipients:
            writer.writerow([
                r.email, r.entry_id, r.section, r.title, r.url,
                r.bucket, "yes" if r.has_referral else "no",
                r.canton or "", r.profession or "",
            ])
            count += 1
    return count


def read_recipients_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
