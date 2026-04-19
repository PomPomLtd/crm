"""Build CSV + summary from the JSONL checkpoint."""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from .checkpoint import Checkpoint


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
    "error",
    "ts",
)


def write_report(checkpoint: Checkpoint, results_dir: str, logger) -> Dict[str, str]:
    """Write timestamped CSV + summary .txt. Returns file paths."""
    records: List[Dict[str, Any]] = list(checkpoint.iter_records())
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
                    r.get("error") or "",
                    r.get("ts", ""),
                ]
            )

    # summary
    total = len(records)
    status_counts: Dict[str, int] = defaultdict(int)
    by_section = defaultdict(lambda: {"total": 0, "success": 0, "emails": 0})
    domains: Dict[str, int] = defaultdict(int)
    total_emails = 0
    with_emails = 0
    priority_count = 0
    unique_emails = set()
    unique_priority = set()

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

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Clinic Email Scraper — Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"Entries in checkpoint: {total}\n")
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
            f.write(
                f"  {sec}: {c['success']}/{c['total']} success "
                f"({rate:.1f}%), {c['emails']} emails\n"
            )
        f.write("\nTop 25 email domains:\n")
        for d, n in sorted(domains.items(), key=lambda kv: -kv[1])[:25]:
            f.write(f"  {d}: {n}\n")

    logger.info(f"CSV:     {csv_path}")
    logger.info(f"Summary: {summary_path}")
    return {"csv": csv_path, "summary": summary_path}
