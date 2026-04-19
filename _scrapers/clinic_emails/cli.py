"""Command-line runner. See `python find_clinic_emails.py --help`."""

from __future__ import annotations

import argparse
import logging
import os
import random
import signal
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List

from .checkpoint import Checkpoint
from .crawler import DomainRateLimiter, crawl_entry
from .entries import load_entries
from .extractors import classify
from .patterns import SECTION_HANDLES
from .report import write_report


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # _scrapers/
REPO_ROOT = os.path.dirname(BASE_DIR)
RESULTS_DIR = os.path.join(BASE_DIR, "results")
ENTRIES_CACHE = os.path.join(RESULTS_DIR, "clinic_entries.json")
CHECKPOINT_PATH = os.path.join(RESULTS_DIR, "clinic_emails_checkpoint.jsonl")


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("clinic-emails")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    h.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%H:%M:%S")
    )
    logger.addHandler(h)
    return logger


# ---------------------------------------------------------------------------
# Single-URL diagnostic mode
# ---------------------------------------------------------------------------


def _run_test(url: str, logger: logging.Logger) -> None:
    rl = DomainRateLimiter(min_delay=1.0, max_delay=3.0)
    stop = threading.Event()
    logger.info(f"Testing: {url}")
    res = crawl_entry(url, rl, stop)
    emails = classify(res["emails"])
    print("\n=== TEST RESULT ===")
    print(f"URL:           {url}")
    print(f"Status:        {res['status']}")
    print(f"Pages crawled: {len(res['pages'])}")
    for p in res["pages"]:
        print(f"  - {p}")
    for bucket_name in ("priority", "general", "other"):
        bucket = emails[bucket_name]
        print(f"\n{bucket_name.title()} ({len(bucket)}):")
        for e in bucket:
            src = res["sources"].get(e, "?")
            print(f"  {e}   <- {src}")
    print()


# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------


def _build_entry_result(
    entry: Dict[str, Any], crawl_result: Dict[str, Any]
) -> Dict[str, Any]:
    buckets = classify(crawl_result.get("emails", set()))
    sources = crawl_result.get("sources", {})
    return {
        "entry_id": entry.get("id"),
        "section": entry.get("section", ""),
        "title": entry.get("title", ""),
        "url": entry.get("url", ""),
        "status": crawl_result.get("status", ""),
        "emails": buckets,
        "sources": sources,
        "pages": crawl_result.get("pages", []),
        "error": None,
        "ts": datetime.utcnow().isoformat() + "Z",
    }


def _run_main(args: argparse.Namespace, logger: logging.Logger) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if args.restart and os.path.exists(CHECKPOINT_PATH):
        logger.warning(f"--restart: removing {CHECKPOINT_PATH}")
        os.remove(CHECKPOINT_PATH)

    entries = load_entries(ENTRIES_CACHE, REPO_ROOT, args.refresh_input, logger)

    if args.section:
        handle = SECTION_HANDLES.get(args.section)
        before = len(entries)
        entries = [e for e in entries if e.get("section") == handle]
        logger.info(f"Filtered to section={handle}: {len(entries)}/{before}")

    cp = Checkpoint(CHECKPOINT_PATH)
    pending = [e for e in entries if int(e["id"]) not in cp.done]
    logger.info(
        f"Pool: total={len(entries)} done={len(cp.done)} pending={len(pending)}"
    )

    if args.sample:
        random.seed(args.seed)
        pending = random.sample(pending, min(args.sample, len(pending)))
        logger.info(f"Random sample: {len(pending)} (seed={args.seed})")

    if args.limit:
        pending = pending[: args.limit]

    if not pending:
        logger.info("Nothing to do.")
        cp.close()
        write_report(cp, RESULTS_DIR, logger)
        return

    # signal handling — cooperative stop
    stop_event = threading.Event()

    def _sig(signum, _frame):
        logger.warning(f"signal {signum}: stopping after in-flight pages…")
        stop_event.set()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    rl = DomainRateLimiter(min_delay=args.min_delay, max_delay=args.max_delay)

    counts: Dict[str, int] = defaultdict(int)
    emails_total = 0
    priority_total = 0
    done = 0
    start = time.time()
    stats_lock = threading.Lock()

    def _work(entry: Dict[str, Any]) -> None:
        nonlocal emails_total, priority_total
        if stop_event.is_set():
            return
        try:
            crawl_result = crawl_entry(entry["url"], rl, stop_event)
            result = _build_entry_result(entry, crawl_result)
        except Exception as e:
            logger.exception(f"worker crashed on entry {entry.get('id')}")
            result = {
                "entry_id": entry.get("id"),
                "section": entry.get("section", ""),
                "title": entry.get("title", ""),
                "url": entry.get("url", ""),
                "status": "error",
                "emails": {"priority": [], "general": [], "other": []},
                "sources": {},
                "pages": [],
                "error": str(e),
                "ts": datetime.utcnow().isoformat() + "Z",
            }
        cp.record(result)
        with stats_lock:
            counts[result.get("status", "error")] += 1
            ems = result.get("emails") or {}
            emails_total += sum(len(v) for v in ems.values())
            priority_total += len(ems.get("priority", []))

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_work, e) for e in pending]
        try:
            for fut in as_completed(futures):
                done += 1
                if done % 25 == 0 or done == len(pending):
                    elapsed = time.time() - start
                    rate = done / elapsed if elapsed else 0
                    eta_min = ((len(pending) - done) / rate / 60) if rate else 0
                    ok = counts.get("success", 0) + counts.get("success_via_root", 0)
                    logger.info(
                        f"[{done}/{len(pending)}] "
                        f"ok={ok} "
                        f"no_emails={counts.get('no_emails', 0)} "
                        f"failed={counts.get('fetch_failed', 0)} "
                        f"err={counts.get('error', 0)} "
                        f"emails={emails_total} priority={priority_total} "
                        f"rate={rate:.2f}/s eta={eta_min:.1f}m"
                    )
                if stop_event.is_set():
                    logger.warning("stop requested; cancelling queued workers")
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    break
        finally:
            cp.close()

    write_report(Checkpoint(CHECKPOINT_PATH), RESULTS_DIR, logger)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Find email addresses on Swiss clinic websites."
    )
    ap.add_argument("--workers", type=int, default=8, help="Thread pool size (default 8)")
    ap.add_argument("--min-delay", type=float, default=1.0, help="Min seconds between same-host hits")
    ap.add_argument("--max-delay", type=float, default=3.0, help="Max seconds between same-host hits")
    ap.add_argument("--limit", type=int, default=None, help="Stop after N new entries")
    ap.add_argument(
        "--section",
        type=int,
        choices=list(SECTION_HANDLES.keys()),
        help="Restrict to one section: 2=medicalCenters 3=clinics 4=groupPractices 5=medClinics 6=hospitals",
    )
    ap.add_argument("--refresh-input", action="store_true", help="Re-dump entries from DB")
    ap.add_argument("--restart", action="store_true", help="Wipe checkpoint before running")
    ap.add_argument("--report", action="store_true", help="Rebuild CSV/summary from checkpoint and exit")
    ap.add_argument("--test", metavar="URL", help="Diagnostic: run pipeline on one URL")
    ap.add_argument("--sample", type=int, default=None, help="Randomly sample N pending entries")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for --sample")
    return ap


def main(argv: List[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    logger = _setup_logger()

    if args.test:
        _run_test(args.test, logger)
        return
    if args.report:
        cp = Checkpoint(CHECKPOINT_PATH)
        write_report(cp, RESULTS_DIR, logger)
        cp.close()
        return
    _run_main(args, logger)


if __name__ == "__main__":
    main()
