#!/usr/bin/env python3
"""Re-run classify() against an existing clinic_emails checkpoint.

Rationale: the historical checkpoint.jsonl holds ~16k entries that were
classified under the old rules (no tier system, no agency filter, no
compound-prefix matching, no ROT13). A fresh crawl to pick up the new
classifications would cost hours of network I/O for zero new HTTP
value — the emails are already extracted and recorded.

This tool takes the existing checkpoint and writes a reclassified copy:

  1. For each entry, flatten `emails.priority + emails.general + emails.other`
     into a single set.
  2. Re-run each email through clean_email() (drops new noise patterns +
     agency domains + media garbage + Sentry ingest + template samples).
  3. Re-run classify() with tier-aware sorting + compound matching +
     third-party legal-only drop (using the entry's own url + sources).
  4. Write the reclassified checkpoint alongside the old one with a
     `.reclassified-<timestamp>` suffix.
  5. Print a diff summary: moves from other → priority, total noise dropped,
     ROT13 recoveries (skipped — ROT13 only applies at crawl-time; the
     checkpoint only has the verbatim output).

Usage:
    python _scrapers/reclassify_checkpoint.py
    python _scrapers/reclassify_checkpoint.py --in path/to/checkpoint.jsonl
    python _scrapers/reclassify_checkpoint.py --in IN --out OUT
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from _scrapers.clinic_emails.extractors import classify, clean_email  # noqa: E402


def _entry_domain(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def reclassify_entry(entry: dict) -> tuple[dict, dict]:
    """Return (new_entry, per-entry diff stats)."""
    old_emails = entry.get("emails", {}) or {}
    old_priority = old_emails.get("priority", []) or []
    old_general = old_emails.get("general", []) or []
    old_other = old_emails.get("other", []) or []

    # Collect + re-clean every candidate (drops new noise)
    all_raw = list(old_priority) + list(old_general) + list(old_other)
    cleaned: set[str] = set()
    for e in all_raw:
        c = clean_email(e)
        if c:
            cleaned.add(c)

    # Reclassify with tier-aware sort + optional third-party-legal drop
    entry_domain = _entry_domain(entry.get("url") or "")
    sources = entry.get("sources", {}) or {}
    buckets = classify(cleaned, entry_domain=entry_domain or None, sources=sources)

    # Diff for reporting
    old_all = set(old_priority) | set(old_general) | set(old_other)
    new_all = set(buckets["priority"]) | set(buckets["general"]) | set(buckets["other"])
    diff = {
        "dropped_as_noise": sorted(old_all - new_all - {e.lower() for e in old_all} | (old_all - new_all)),
        "moved_other_to_priority": sorted(
            set(buckets["priority"]) & set(old_other)
        ),
        "stayed_priority": sorted(set(buckets["priority"]) & set(old_priority)),
    }
    # Fix dropped_as_noise — simpler form
    diff["dropped_as_noise"] = sorted(old_all - new_all)

    new_entry = dict(entry)
    new_entry["emails"] = buckets
    return new_entry, diff


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--in", dest="input",
        default=str(REPO_ROOT / "_scrapers" / "results" / "clinic_emails_checkpoint.jsonl"),
        help="Input checkpoint JSONL",
    )
    p.add_argument(
        "--out", dest="output",
        help="Output path (default: <in>.reclassified-<date>.jsonl)",
    )
    args = p.parse_args(argv)

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Checkpoint not found: {in_path}", file=sys.stderr)
        return 2

    out_path = Path(args.output) if args.output else Path(
        str(in_path) + ".reclassified.jsonl"
    )

    # Aggregate stats
    entries_processed = 0
    total_dropped = 0
    total_promoted = 0
    dropped_domain_counts: Counter = Counter()
    promoted_prefix_counts: Counter = Counter()
    bucket_totals_old = {"priority": 0, "general": 0, "other": 0}
    bucket_totals_new = {"priority": 0, "general": 0, "other": 0}

    with out_path.open("w", encoding="utf-8") as out_f:
        with in_path.open("r", encoding="utf-8") as in_f:
            for line in in_f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Old counts
                old_e = entry.get("emails", {}) or {}
                bucket_totals_old["priority"] += len(old_e.get("priority") or [])
                bucket_totals_old["general"] += len(old_e.get("general") or [])
                bucket_totals_old["other"] += len(old_e.get("other") or [])

                new_entry, diff = reclassify_entry(entry)
                new_e = new_entry["emails"]
                bucket_totals_new["priority"] += len(new_e["priority"])
                bucket_totals_new["general"] += len(new_e["general"])
                bucket_totals_new["other"] += len(new_e["other"])

                total_dropped += len(diff["dropped_as_noise"])
                for e in diff["dropped_as_noise"]:
                    host = e.rsplit("@", 1)[-1] if "@" in e else "?"
                    dropped_domain_counts[host] += 1

                total_promoted += len(diff["moved_other_to_priority"])
                for e in diff["moved_other_to_priority"]:
                    prefix = e.partition("@")[0]
                    promoted_prefix_counts[prefix] += 1

                out_f.write(json.dumps(new_entry, ensure_ascii=False) + "\n")
                entries_processed += 1

    # Summary
    print(f"Reclassified {entries_processed:,} entries.")
    print(f"Output: {out_path}")
    print()
    print("Bucket totals (old → new):")
    for b in ("priority", "general", "other"):
        delta = bucket_totals_new[b] - bucket_totals_old[b]
        sign = "+" if delta >= 0 else ""
        print(f"  {b:<10} {bucket_totals_old[b]:>7,} → {bucket_totals_new[b]:>7,}  ({sign}{delta:,})")
    print()
    print(f"Total addresses dropped as noise: {total_dropped:,}")
    if dropped_domain_counts:
        print("  Top 15 dropped domains:")
        for host, n in dropped_domain_counts.most_common(15):
            print(f"    x{n:>4}  {host}")
    print()
    print(f"Total addresses promoted from 'other' → 'priority': {total_promoted:,}")
    if promoted_prefix_counts:
        print("  Top 15 promoted prefixes:")
        for prefix, n in promoted_prefix_counts.most_common(15):
            print(f"    x{n:>4}  {prefix}@")
    return 0


if __name__ == "__main__":
    sys.exit(main())
