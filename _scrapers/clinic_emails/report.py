"""Build CSV + summary from the JSONL checkpoint."""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from .checkpoint import Checkpoint
from .patterns import NOISE_EMAIL_DOMAINS, NOISE_EMAIL_DOMAIN_SUFFIXES


CSV_FIELDS = (
    "entry_id",
    "section",
    "title",
    "url",
    "priority_emails",
    "general_emails",
    "other_emails",
    "all_emails",
    "sources_json",
    "pages_crawled",
    "status",
    # referral characterization
    "has_referral",
    "referral_methods",
    "referral_pages",
    "referral_emails",
    "referral_faxes",
    "referral_documents_json",
    "error",
    "ts",
)


def _is_noise_email(email: str) -> bool:
    """Retroactive noise check — applied at report time so the noise list
    can evolve without needing to rescrape already-processed entries."""
    if "@" not in email:
        return True
    domain = email.split("@", 1)[1].lower()
    if domain in NOISE_EMAIL_DOMAINS:
        return True
    if any(domain.endswith(sfx) for sfx in NOISE_EMAIL_DOMAIN_SUFFIXES):
        return True
    return False


def _filter_record_inplace(r: Dict[str, Any]) -> int:
    """Strip noise emails from a checkpoint record. Returns count removed."""
    removed = 0
    emails = r.get("emails") or {}
    for bucket in ("priority", "general", "other"):
        kept = [e for e in emails.get(bucket, []) if not _is_noise_email(e)]
        removed += len(emails.get(bucket, [])) - len(kept)
        emails[bucket] = kept
    r["emails"] = emails
    sources = r.get("sources") or {}
    r["sources"] = {e: src for e, src in sources.items() if not _is_noise_email(e)}
    return removed


def write_report(checkpoint: Checkpoint, results_dir: str, logger) -> Dict[str, str]:
    """Write timestamped CSV + summary .txt. Returns file paths."""
    records: List[Dict[str, Any]] = list(checkpoint.iter_records())
    # Retroactive noise filter — applies the current NOISE_EMAIL_DOMAINS
    # list to already-scraped records, so adding new template placeholders
    # cleans up historical data without re-scraping.
    noise_removed = sum(_filter_record_inplace(r) for r in records)
    if noise_removed:
        logger.info(f"Retroactive noise filter removed {noise_removed} email(s).")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(results_dir, f"clinic_emails_{ts}.csv")
    summary_path = csv_path.replace(".csv", "_summary.txt")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_FIELDS)
        for r in records:
            emails = r.get("emails") or {"priority": [], "general": [], "other": []}
            all_e = (
                list(emails.get("priority", []))
                + list(emails.get("general", []))
                + list(emails.get("other", []))
            )
            ref = r.get("referral") or {"found": False}
            w.writerow(
                [
                    r.get("entry_id"),
                    r.get("section", ""),
                    r.get("title", ""),
                    r.get("url", ""),
                    "; ".join(emails.get("priority", [])),
                    "; ".join(emails.get("general", [])),
                    "; ".join(emails.get("other", [])),
                    "; ".join(all_e),
                    json.dumps(r.get("sources", {}), ensure_ascii=False),
                    "; ".join(r.get("pages", [])),
                    r.get("status", ""),
                    "yes" if ref.get("found") else "no",
                    "; ".join(ref.get("methods", [])),
                    "; ".join(ref.get("pages", [])),
                    "; ".join(ref.get("emails", [])),
                    "; ".join(ref.get("faxes", [])),
                    json.dumps(ref.get("documents", []), ensure_ascii=False),
                    r.get("error") or "",
                    r.get("ts", ""),
                ]
            )

    # summary
    total = len(records)
    status_counts: Dict[str, int] = defaultdict(int)
    by_section = defaultdict(lambda: {
        "total": 0, "success": 0, "emails": 0, "referral": 0,
    })
    domains: Dict[str, int] = defaultdict(int)
    total_emails = 0
    with_emails = 0
    priority_count = 0
    unique_emails = set()
    unique_priority = set()
    # referral stats
    referral_total = 0
    referral_methods: Dict[str, int] = defaultdict(int)
    referral_doc_types: Dict[str, int] = defaultdict(int)
    referral_emails_count = 0
    referral_fax_count = 0

    for r in records:
        status_counts[r.get("status", "unknown")] += 1
        sec = r.get("section", "")
        by_section[sec]["total"] += 1
        is_success = r.get("status", "").startswith("success")
        if is_success:
            by_section[sec]["success"] += 1
        bucket_total = 0
        for bucket_name, bucket in (r.get("emails") or {}).items():
            for email in bucket:
                total_emails += 1
                bucket_total += 1
                by_section[sec]["emails"] += 1
                unique_emails.add(email)
                if bucket_name == "priority":
                    priority_count += 1
                    unique_priority.add(email)
                try:
                    domains[email.split("@", 1)[1].lower()] += 1
                except IndexError:
                    pass
        if bucket_total > 0:
            with_emails += 1

        ref = r.get("referral") or {}
        if ref.get("found"):
            referral_total += 1
            by_section[sec]["referral"] += 1
            for m in ref.get("methods", []):
                referral_methods[m] += 1
            for d in ref.get("documents", []):
                referral_doc_types[d.get("type", "?")] += 1
            referral_emails_count += len(ref.get("emails", []))
            referral_fax_count += len(ref.get("faxes", []))

    unique_urls = {r.get("url") for r in records if r.get("url")}

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Clinic Email Scraper — Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"Entries in checkpoint: {total}\n")
        f.write(
            f"Unique practice URLs:  {len(unique_urls)}  "
            f"(DB has {total - len(unique_urls)} duplicate entries pointing to the same sites)\n"
        )
        if total:
            f.write(
                f"Entries with >=1 email: {with_emails} ({100 * with_emails / total:.1f}%)\n"
            )
        f.write(
            f"Total emails collected: {total_emails} "
            f"(unique: {len(unique_emails)})\n"
        )
        f.write(
            f"Priority emails: {priority_count} "
            f"(unique: {len(unique_priority)})\n\n"
        )
        if total_emails and len(unique_emails):
            dup_ratio = total_emails / len(unique_emails)
            f.write(
                f"Note: chain sites (same domain across multiple DB entries) "
                f"cross-list emails. Avg duplication factor: {dup_ratio:.1f}x. "
                f"Dedupe by email address before outreach.\n\n"
            )
        f.write("Status:\n")
        for k, v in sorted(status_counts.items(), key=lambda kv: -kv[1]):
            f.write(f"  {k}: {v}\n")
        f.write("\nBy section:\n")
        for sec, c in sorted(by_section.items()):
            rate = 100 * c["success"] / c["total"] if c["total"] else 0
            ref_pct = 100 * c["referral"] / c["total"] if c["total"] else 0
            f.write(
                f"  {sec}: {c['success']}/{c['total']} success "
                f"({rate:.1f}%), {c['emails']} emails, "
                f"{c['referral']} referral sections ({ref_pct:.1f}%)\n"
            )
        f.write(f"\nReferral sections: {referral_total}/{total}")
        if total:
            f.write(f"  ({100 * referral_total / total:.1f}%)")
        f.write("\n")
        if referral_total:
            f.write("  Methods:\n")
            for m, n in sorted(referral_methods.items(), key=lambda kv: -kv[1]):
                f.write(f"    {m}: {n}\n")
            if referral_doc_types:
                f.write("  Document types:\n")
                for t, n in sorted(referral_doc_types.items(), key=lambda kv: -kv[1]):
                    f.write(f"    .{t}: {n}\n")
            f.write(f"  Referral emails extracted: {referral_emails_count}\n")
            f.write(f"  Fax numbers extracted: {referral_fax_count}\n")
        f.write("\nTop 25 email domains:\n")
        for d, n in sorted(domains.items(), key=lambda kv: -kv[1])[:25]:
            f.write(f"  {d}: {n}\n")

    logger.info(f"CSV:     {csv_path}")
    logger.info(f"Summary: {summary_path}")
    return {"csv": csv_path, "summary": summary_path}
