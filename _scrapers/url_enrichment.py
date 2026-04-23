#!/usr/bin/env python3
"""Fill missing practice-website URLs on existing Craft entries.

The initial Feed Me import for `groupPractices` and `medClinics` used
DuckDuckGo to look up each practice's website; DuckDuckGo rate-limits
aggressively and left tens of thousands of entries with no URL in the
Craft content JSON. Without a URL the email scraper can't crawl the
practice, which means we never find emails for them.

This runner:
  1. Queries Craft (via `ddev mysql`) for enabled entries in sections
     2-6 that are missing the URL field.
  2. For each, calls SearchAPI's Google engine with `{title} {city}`
     and takes the first organic result.
  3. Filters out directory/social/search domains.
  4. Writes the resulting URL back into Craft's `elements_sites.content`
     JSON under the practice-URL field UID (same UID the email scraper
     reads).

Resumable via a JSONL checkpoint — re-runs skip any entry already
processed. Concurrency + rate-limit backoff handle API quota politely.

Usage:
    python url_enrichment.py --sections 4 --workers 5 --limit 100
    python url_enrichment.py --test 307073     # one entry, no DB write
    python url_enrichment.py --workers 8       # full run over all missing
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import queue
import random
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn, MofNCompleteColumn, Progress, SpinnerColumn,
    TextColumn, TimeElapsedColumn, TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_DEFAULT = Path(__file__).parent / "results" / "url_enrichment_checkpoint.jsonl"

SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"
SEARCHAPI_KEY_ENV = "SEARCHAPI_KEY"
# Fallback to the key already baked into clinics/urlFetch.py (same account).
SEARCHAPI_KEY_FALLBACK = "VQxddzhtWBd9ANBGbtLGd3dk"

# Field-layout-element UIDs (consistent across sections 2-6, verified in
# elements_sites.content on 2026-04-23).
URL_FIELD_UID = "ee61a20b-95a1-4265-b42d-84a780431065"
CITY_FIELD_UID = "279e9891-8e85-4aeb-a4c0-aa66466882bd"

# Never accept as "the practice URL" — directories, search pages,
# social profiles, phone-number aggregators, booking platforms.
BANNED_DOMAINS = {
    # Swiss directories / phone-book sites (identified from run analysis)
    "onedoc.ch", "comparis.ch", "doktor.ch", "local.ch", "yellow.ch",
    "search.ch", "firmen.ch", "zip.ch",
    "medicosearch.ch", "drdoctor.ch", "docfinder.at", "medsite.ch",
    "docfind.ch", "deindoktor.ch", "seelandnet.ch",
    "therapievermittlung.ch", "leading-medicine-guide.com",
    # Booking platforms
    "doctena.ch", "logicrdv.ch", "treatwell.ch", "doc24.ch",
    # Search engines
    "google.com", "bing.com", "duckduckgo.com", "yahoo.com",
    # Social
    "facebook.com", "linkedin.com", "instagram.com", "twitter.com",
    "x.com", "youtube.com",
    # Reviews / aggregators
    "trustpilot.com", "yelp.com", "tripadvisor.com",
    # Wikipedia / news
    "wikipedia.org", "nzz.ch", "srf.ch", "tagesanzeiger.ch",
    # HIN network directory (different purpose — their own site isn't a practice site)
    "hin.ch",
}

# Host-pattern checks that aren't pure domain matches.
SUSPICIOUS_HOST_TOKENS = ("staging.", "test.", "dev.", "localhost")
# Reject results whose path ends in these extensions — these are documents,
# not practice websites (e.g., a doctor's CV PDF on a directory site).
BANNED_PATH_EXTENSIONS = (".pdf", ".docx", ".doc", ".rtf", ".zip")

# Large healthcare provider domains (chains, university hospitals, big
# cantonal hospitals). These are real sites, but:
#  - They're covered by their own referral systems, not our product
#  - A per-domain match would cause us to send hundreds of their
#    practice entries all to the same corporate inbox
#  - User excluded them at the mailer level; no point spending API credits
#    finding their URLs here either.
LARGE_PROVIDER_DOMAINS = {
    # University hospitals
    "usz.ch", "usb.ch", "luks.ch", "insel.ch", "inselgruppe.ch",
    "dekmed.uzh.ch", "kispi.uzh.ch",
    # Big cantonal hospitals (Kantonsspitäler)
    "ksa.ch", "ksb.ch", "ksw.ch", "ksgr.ch", "ksgl.ch", "ksuri.ch",
    "ksow.ch", "kssg.ch",
    # Private chains
    "hirslanden.ch",
    "sanacare.ch", "medbase.ch", "medix.ch", "medix-gruppenpraxis.ch",
    "swissmedical.net",
    "h-och.ch", "barmelweid.ch",
    # Multi-hospital cantonal groups
    "spitaeler-sh.ch", "spitaleler-sh.ch",
    # Specialized / psychiatric networks (university + cantonal)
    "upd.ch", "upk.ch", "kispisg.ch", "pdag.ch",
}

# Hard cap on pick position. If the clean URL isn't in the top 2 Google
# results, the practice almost certainly doesn't have its own website —
# better to record `no_site_in_top_2` than to accept a long-shot result
# that's going to be a directory, review site, or chain HQ anyway.
MAX_PICK_POSITION = 2

log = logging.getLogger("url_enrichment")


@dataclass(frozen=True)
class Entry:
    id: int
    title: str
    city: str
    section_id: int


def _bare_host(u: str) -> str:
    try:
        h = urlparse(u).netloc.lower().lstrip(".")
    except Exception:
        return ""
    return h.removeprefix("www.")


def is_acceptable_url(u: str) -> bool:
    """True if `u` looks like a legitimate practice website — not a
    directory, not a booking platform, not a large chain/hospital we've
    agreed to exclude upstream, not a PDF/doc attachment, not a staging
    environment."""
    if not u or not u.startswith(("http://", "https://")):
        return False
    try:
        parsed = urlparse(u)
    except Exception:
        return False
    host = parsed.netloc.lower().lstrip(".").removeprefix("www.")
    if not host:
        return False
    for banned in BANNED_DOMAINS:
        if host == banned or host.endswith("." + banned):
            return False
    for big in LARGE_PROVIDER_DOMAINS:
        if host == big or host.endswith("." + big):
            return False
    for token in SUSPICIOUS_HOST_TOKENS:
        if token in host:
            return False
    path_lower = (parsed.path or "").lower()
    for ext in BANNED_PATH_EXTENSIONS:
        if path_lower.endswith(ext):
            return False
    return True


def load_missing_url_entries(
    *, sections: list[int], limit: Optional[int] = None
) -> list[Entry]:
    """Ask Craft for enabled entries in the given sections that lack the
    practice-URL field. **Deduped by (title, city) in SQL** — Feed-Me
    import created two entries per practice (sequential IDs with same
    title+city); we hit SearchAPI once per practice, not twice.

    Returns the lower entry_id for each (title, city) pair. The unused
    duplicate entry just sits there without a URL; when the email scraper
    later reads Craft, it'll see one practice with a URL and crawl it. If
    you want to also backfill the duplicate with the same URL, a post-step
    could copy the URL across — but that's cosmetic, scraper dedupes by
    URL anyway."""
    section_list = ",".join(str(s) for s in sections)
    limit_clause = f"LIMIT {int(limit)}" if limit else ""
    # GROUP BY on title + city (city comes from the CITY_FIELD_UID).
    # MIN(e.id) picks the earliest (canonical) duplicate; ANY_VALUE keeps
    # section_id stable for each group.
    sql = (
        "SELECT CONCAT('{\"id\":', MIN(e.id), "
        "',\"sid\":', ANY_VALUE(e.sectionId), "
        "',\"title\":', COALESCE(JSON_QUOTE(ANY_VALUE(es.title)), 'null'), "
        "',\"city\":', COALESCE(JSON_QUOTE(JSON_UNQUOTE(ANY_VALUE(JSON_EXTRACT(es.content, "
        f"'$.\"{CITY_FIELD_UID}\"')))), 'null'), "
        "'}') AS j "
        "FROM entries e "
        "JOIN elements_sites es ON es.elementId = e.id AND es.siteId = 1 "
        "JOIN elements el ON el.id = e.id "
        f"WHERE e.sectionId IN ({section_list}) "
        "  AND el.enabled = 1 "
        "  AND el.dateDeleted IS NULL "
        "  AND el.archived = 0 "
        f"  AND JSON_EXTRACT(es.content, '$.\"{URL_FIELD_UID}\"') IS NULL "
        "GROUP BY es.title, "
        f"JSON_UNQUOTE(JSON_EXTRACT(es.content, '$.\"{CITY_FIELD_UID}\"')), "
        "e.sectionId "
        f"ORDER BY MIN(e.sectionId), MIN(e.id) {limit_clause}"
    )
    proc = subprocess.run(
        ["ddev", "mysql", "db", "--skip-column-names", "--raw", "-e", sql],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ddev mysql failed:\n{proc.stderr}")
    out: list[Entry] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        out.append(Entry(
            id=int(r["id"]), section_id=int(r["sid"]),
            title=(r.get("title") or "").strip(),
            city=(r.get("city") or "").strip(),
        ))
    return out


def fetch_url_via_searchapi(
    *, api_key: str, title: str, city: str, max_retries: int = 3,
) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Returns (url, reason, position). `url` is None when nothing acceptable
    was found; `reason` describes why (`rate_limit`, `quota`, `no_results`,
    `all_banned:<top_host>`, `http_error:<code>`, `exception`). `position`
    is the 1-indexed organic-result rank we picked from (None if no pick).

    Requests `num=10` — SearchAPI charges per search, not per result, so
    this is free extra coverage. We iterate until we find a non-directory
    result, which turns many "banned domain" outcomes into real URLs.
    """
    if not title:
        return None, "empty_title", None
    query = title
    if city and city.lower() not in title.lower():
        query = f"{title} {city}"

    for attempt in range(max_retries):
        try:
            resp = requests.get(
                SEARCHAPI_URL,
                params={
                    "engine": "google", "q": query,
                    "api_key": api_key, "num": 10,
                    "gl": "ch", "hl": "de",
                },
                timeout=30,
            )
            if resp.status_code in (429, 403):
                time.sleep(random.uniform(3, 7) * (attempt + 1))
                continue
            if resp.status_code == 401:
                return None, "auth_error", None
            if resp.status_code != 200:
                return None, f"http_error:{resp.status_code}", None
            data = resp.json()
            if "error" in data and data.get("error"):
                msg = str(data["error"]).lower()
                if "all of the searches" in msg or "quota" in msg:
                    return None, "quota_exhausted", None
                return None, f"api_error:{data['error'][:60]}", None
            results = data.get("organic_results") or []
            if not results:
                return None, "no_results", None
            top_host = _bare_host((results[0].get("link") or "").strip())
            # Hard cap: only accept position 1 or 2. A clean URL further
            # down almost always means the practice has no site of its own
            # and we're about to pick a directory / town portal / misc hit.
            for pos, r in enumerate(results[:MAX_PICK_POSITION], start=1):
                link = (r.get("link") or "").strip()
                if not link:
                    continue
                if is_acceptable_url(link):
                    return link, None, pos
            return None, f"no_site_in_top_{MAX_PICK_POSITION}:{top_host}", None
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                return None, f"exception:{type(e).__name__}", None
            time.sleep(random.uniform(2, 5) * (attempt + 1))
    return None, "max_retries", None


def update_craft_entry_url(entry_id: int, url: str) -> None:
    """Write the URL into the entry's content JSON, under the
    practice-URL field UID. Uses JSON_SET so existing keys stay intact.
    Value shape matches Craft's typed URL field: {"type":"url","value":...}."""
    value_json = json.dumps({"type": "url", "value": url}, ensure_ascii=False)
    sql = (
        f"UPDATE elements_sites SET content = JSON_SET(content, "
        f"'$.\"{URL_FIELD_UID}\"', CAST(? AS JSON)) "
        f"WHERE elementId = ? AND siteId = 1"
    )
    # ddev mysql doesn't support -e with ? placeholders; escape manually.
    safe = value_json.replace("\\", "\\\\").replace("'", "''")
    direct_sql = (
        f"UPDATE elements_sites SET content = JSON_SET(content, "
        f"'$.\"{URL_FIELD_UID}\"', CAST('{safe}' AS JSON)) "
        f"WHERE elementId = {int(entry_id)} AND siteId = 1"
    )
    proc = subprocess.run(
        ["ddev", "mysql", "db", "-e", direct_sql],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"UPDATE failed for {entry_id}:\n{proc.stderr}")


class Checkpoint:
    """Append-only JSONL. One row per completed entry."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seen: set[int] = set()
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                        self._seen.add(int(r.get("id", 0)))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue

    def already_processed(self, entry_id: int) -> bool:
        return entry_id in self._seen

    def record(
        self, *, entry_id: int, url: Optional[str], reason: Optional[str],
        position: Optional[int] = None,
    ) -> None:
        row = {
            "id": entry_id, "url": url, "reason": reason, "pos": position,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            self._seen.add(entry_id)


RECENT_TAIL = 6

# Craft section short-labels (for the compact workers view)
SECTION_LABELS: dict[int, str] = {
    2: "mc", 3: "clin", 4: "grp", 5: "med", 6: "hosp",
}

_BLOCKS = " ▏▎▍▌▋▊▉█"  # 8 partial-block glyphs + full block


def _mini_bar(value: int, maximum: int, width: int = 14) -> str:
    """Render a small Unicode progress bar, e.g. '▇▇▇▇▇▁▁▁▁▁' style.
    `width` is in character cells. Returns a bare string ready to wrap in Text.from_markup."""
    if maximum <= 0 or width <= 0:
        return " " * width
    frac = max(0.0, min(1.0, value / maximum))
    total_eighths = int(round(frac * width * 8))
    full, rest = divmod(total_eighths, 8)
    bar = "█" * full
    if rest and full < width:
        bar += _BLOCKS[rest]
    return bar.ljust(width)


@dataclass
class _WorkerSlot:
    entry_id: int
    title: str
    city: str
    section_id: int
    started_at: float


@dataclass
class _Completion:
    ts: float
    entry_id: int
    title: str
    url: Optional[str]
    reason: Optional[str]
    position: Optional[int]
    elapsed: float


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _switch_logger_to_rich(console: Console) -> None:
    """Redirect the root logger through Rich so `logging.info(...)` calls
    from worker threads render above the Live region instead of tearing
    the layout. Idempotent."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(RichHandler(
        console=console, show_path=False, show_time=True, markup=True,
        rich_tracebacks=True,
    ))
    root.setLevel(logging.INFO)


class LiveTUI:
    """Rich Live display for url_enrichment.

    Mirrors the layout style of `_scrapers/clinic_emails/tui.py`: header
    progress bar, middle row with workers + stats side-by-side, bottom
    scrolling recent-completions panel. Context-manager API; worker
    threads call `on_worker_start` / `on_worker_finish`.
    """

    def __init__(
        self,
        *,
        total: int,
        already_done: int,
        n_workers: int,
        checkpoint_path: Path,
        title: str = "SearchAPI URL Enrichment",
        console: Optional[Console] = None,
        refresh_per_second: int = 4,
    ):
        self.total = total
        self.n_workers = n_workers
        self.title = title
        self.checkpoint_path = checkpoint_path
        self.console = console or Console()
        self._refresh = refresh_per_second

        self._lock = threading.Lock()
        self._workers: dict[int, Optional[_WorkerSlot]] = {i: None for i in range(n_workers)}
        self._found = 0
        self._no_site = 0  # reason starts with 'no_site_in_top_' → real practice has no own website
        self._no_results = 0
        self._rate_limit = 0
        self._db_write_failed = 0
        self._other = 0
        self._positions: dict[int, int] = {}
        # Per-section running counters: section_id -> (processed, found)
        self._per_section: dict[int, list[int]] = {}
        self._recent: deque[_Completion] = deque(maxlen=RECENT_TAIL)
        self._started = time.monotonic()
        self._already_done = already_done

        self._progress = Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[bold]Enriching"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TextColumn("[cyan]{task.percentage:>5.1f}%"),
            TextColumn("·"),
            TextColumn("rate {task.fields[rate]}"),
            TextColumn("·"),
            TimeElapsedColumn(),
            TextColumn("·"),
            TextColumn("ETA"),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
            transient=False,
        )
        self._task_id = self._progress.add_task(
            "enrich", total=total, completed=already_done, rate="0/s",
        )
        self._live: Optional[Live] = None

    # ------------------------------------------------------------------
    # Worker hooks
    # ------------------------------------------------------------------

    def on_worker_start(self, slot: int, entry: Entry) -> None:
        with self._lock:
            self._workers[slot] = _WorkerSlot(
                entry_id=entry.id,
                title=entry.title,
                city=entry.city,
                section_id=entry.section_id,
                started_at=time.monotonic(),
            )

    def on_worker_finish(
        self,
        slot: int,
        entry: Entry,
        url: Optional[str],
        reason: Optional[str],
        position: Optional[int],
        elapsed: float,
    ) -> None:
        completion = _Completion(
            ts=time.time(), entry_id=entry.id, title=entry.title,
            url=url, reason=reason, position=position, elapsed=elapsed,
        )
        with self._lock:
            self._workers[slot] = None
            if url:
                self._found += 1
                if position:
                    self._positions[position] = self._positions.get(position, 0) + 1
            elif reason and reason.startswith("no_site_in_top"):
                self._no_site += 1
            elif reason == "no_results":
                self._no_results += 1
            elif reason and "rate" in reason.lower():
                self._rate_limit += 1
            elif reason and reason.startswith("db_write_failed"):
                self._db_write_failed += 1
            else:
                self._other += 1
            # Per-section counter: [processed, found]
            sec = self._per_section.setdefault(entry.section_id, [0, 0])
            sec[0] += 1
            if url:
                sec[1] += 1
            self._recent.appendleft(completion)
            session_done = (
                self._found + self._no_site + self._no_results
                + self._rate_limit + self._db_write_failed + self._other
            )
            done_total = self._already_done + session_done
            elapsed_total = time.monotonic() - self._started
            rate = session_done / elapsed_total if elapsed_total > 0 else 0.0

        self._progress.update(
            self._task_id, completed=done_total, rate=f"{rate:.2f}/s",
        )

    def log(self, message: str, *, style: str = "") -> None:
        self.console.log(message if not style else Text(message, style=style))

    # ------------------------------------------------------------------
    # Render helpers
    # ------------------------------------------------------------------

    def _render_workers_table(self) -> Table:
        t = Table.grid(padding=(0, 1), expand=True)
        t.add_column("#", justify="right", style="dim", no_wrap=True, width=3)
        t.add_column("Entry", justify="right", style="cyan", no_wrap=True, width=7)
        t.add_column("Sec", style="magenta", no_wrap=True, width=4)
        t.add_column("Title", overflow="ellipsis", no_wrap=True)
        t.add_column("City", style="dim", no_wrap=True, overflow="ellipsis", max_width=14)
        t.add_column("Elapsed", justify="right", no_wrap=True, width=6)

        now = time.monotonic()
        with self._lock:
            slots = list(self._workers.items())
        for slot, w in slots:
            if w is None:
                t.add_row(f"#{slot+1}",
                          Text("--", style="dim"),
                          Text("", style="dim"),
                          Text("idle", style="dim"),
                          "", "")
            else:
                el = now - w.started_at
                style = "yellow" if el > 8 else ""
                sec_label = SECTION_LABELS.get(w.section_id, str(w.section_id))
                t.add_row(
                    f"#{slot+1}", str(w.entry_id),
                    sec_label,
                    Text(_truncate(w.title, 60), style=style),
                    w.city,
                    Text(f"{el:4.1f}s", style=style),
                )
        return t

    def _render_dashboard(self) -> "Group":
        """Dashboard-style right panel tailored to URL enrichment:
        - Hit-rate summary with visual bars
        - Pick-position histogram (validates the num=10 bet)
        - Per-section hit-rate breakdown
        """
        from rich.console import Group
        with self._lock:
            found = self._found
            banned = self._no_site
            no_res = self._no_results
            dbf = self._db_write_failed
            rl = self._rate_limit
            other = self._other
            positions = dict(self._positions)
            per_section = {k: list(v) for k, v in self._per_section.items()}
        session_done = found + banned + no_res + rl + dbf + other
        denom = max(1, session_done)

        # ---- 1. Hit-rate summary with bars ----
        outcomes = Table.grid(padding=(0, 1), expand=True)
        outcomes.add_column("label", no_wrap=True)
        outcomes.add_column("bar", no_wrap=True, width=12)
        outcomes.add_column("count", justify="right", style="bold", no_wrap=True, min_width=5)
        outcomes.add_column("pct", justify="right", style="dim", no_wrap=True, width=5)

        def _row(label_text: Text, n: int, bar_color: str) -> None:
            pct = n * 100.0 / denom
            bar = _mini_bar(n, denom, width=12)
            outcomes.add_row(
                label_text,
                Text(bar, style=bar_color),
                f"{n:,}",
                f"{pct:4.1f}%",
            )

        _row(Text("✓ Found", style="green"), found, "green")
        if banned:
            _row(Text("⊘ No own site", style="yellow"), banned, "yellow")
        if no_res:
            _row(Text("∅ No results", style="dim"), no_res, "white")
        if dbf:
            _row(Text("⚠ DB fail", style="red"), dbf, "red")
        if rl:
            _row(Text("↻ Retried", style="dim"), rl, "white")
        if other:
            _row(Text("· Other", style="dim"), other, "white")

        # ---- 2. Pick position histogram ----
        pos_tbl = Table.grid(padding=(0, 1), expand=True)
        pos_tbl.add_column("pos", no_wrap=True, style="dim", width=3)
        pos_tbl.add_column("bar", no_wrap=True, width=12)
        pos_tbl.add_column("count", justify="right", style="cyan", no_wrap=True, min_width=5)
        pos_tbl.add_column("pct", justify="right", style="dim", no_wrap=True, width=5)
        pos_max = max(positions.values(), default=0)
        ordered_pos = sorted(positions.items())
        # Show positions 1-3 individually, group 4+ for cleanliness
        grouped_high: int = 0
        for p, n in ordered_pos:
            if p <= 3:
                pct = (n * 100.0 / found) if found else 0
                pos_tbl.add_row(
                    f"#{p}",
                    Text(_mini_bar(n, pos_max, 12), style="cyan"),
                    f"{n:,}", f"{pct:4.1f}%",
                )
            else:
                grouped_high += n
        if grouped_high:
            pct = (grouped_high * 100.0 / found) if found else 0
            pos_tbl.add_row(
                "#4+",
                Text(_mini_bar(grouped_high, pos_max, 12), style="cyan dim"),
                f"{grouped_high:,}", f"{pct:4.1f}%",
            )
        if not ordered_pos:
            pos_tbl.add_row("", Text("(waiting…)", style="dim"), "", "")

        # ---- 3. Per-section hit-rate ----
        sec_tbl = Table.grid(padding=(0, 1), expand=True)
        sec_tbl.add_column("sec", no_wrap=True, style="magenta", width=4)
        sec_tbl.add_column("bar", no_wrap=True, width=10)
        sec_tbl.add_column("ratio", justify="right", no_wrap=True, style="dim")
        sec_tbl.add_column("hitpct", justify="right", no_wrap=True, style="bold", min_width=5)
        for sid in sorted(per_section.keys()):
            proc, fnd = per_section[sid]
            label = SECTION_LABELS.get(sid, f"sec{sid}")
            hit_rate = (fnd / proc) if proc else 0
            bar_color = (
                "green" if hit_rate >= 0.75
                else "yellow" if hit_rate >= 0.5
                else "red"
            )
            sec_tbl.add_row(
                label,
                Text(_mini_bar(fnd, proc or 1, 10), style=bar_color),
                f"{fnd}/{proc}",
                f"{hit_rate*100:4.1f}%",
            )
        if not per_section:
            sec_tbl.add_row("", Text("(waiting…)", style="dim"), "", "")

        hit_pct = found * 100.0 / denom

        # Compact: label immediately above its table, no blank separator rows
        hdr = Text.from_markup(
            f"[bold green]{found:,}[/] found · "
            f"[bold]{hit_pct:.1f}%[/] hit-rate · "
            f"[dim]{session_done:,} processed[/]"
        )
        return Group(
            hdr,
            Text("Outcomes", style="bold dim"),
            outcomes,
            Text("Pick position", style="bold dim"),
            pos_tbl,
            Text("By section", style="bold dim"),
            sec_tbl,
        )

    def _render_recent_table(self) -> Table:
        t = Table.grid(padding=(0, 1), expand=True)
        t.add_column("Time", no_wrap=True, style="dim", width=8)
        t.add_column("", no_wrap=True, width=2)
        t.add_column("ID", justify="right", style="cyan", no_wrap=True, width=8)
        t.add_column("Title", overflow="ellipsis", no_wrap=True)
        t.add_column("Result", overflow="ellipsis", no_wrap=True)
        t.add_column("Took", justify="right", no_wrap=True, width=7)

        with self._lock:
            recent = list(self._recent)
        if not recent:
            t.add_row("", "", "", Text("(warming up…)", style="dim"), "", "")
            return t
        for c in recent:
            ts = time.strftime("%H:%M:%S", time.localtime(c.ts))
            if c.url:
                glyph = Text("✓", style="bold green")
                host = _bare_host(c.url)
                pos_suffix = f" [dim](#{c.position})[/]" if c.position and c.position > 1 else ""
                desc_text = Text.from_markup(f"[cyan]{host}[/]{pos_suffix}")
            elif c.reason and c.reason.startswith("all_banned"):
                glyph = Text("⊘", style="yellow")
                host = c.reason.split(":", 1)[1] if ":" in c.reason else "directory"
                desc_text = Text(f"only directories ({host})", style="yellow")
            elif c.reason == "no_results":
                glyph = Text("∅", style="dim")
                desc_text = Text("no search results", style="dim")
            elif c.reason and c.reason.startswith("db_write_failed"):
                glyph = Text("⚠", style="bold red")
                desc_text = Text(c.reason, style="red")
            elif c.reason == "quota_exhausted":
                glyph = Text("⚠", style="bold red")
                desc_text = Text("SEARCHAPI QUOTA EXHAUSTED", style="bold red")
            else:
                glyph = Text("·", style="dim")
                desc_text = Text(c.reason or "?", style="dim")
            t.add_row(
                ts, glyph, str(c.entry_id),
                _truncate(c.title, 50), desc_text, f"{c.elapsed:5.1f}s",
            )
        return t

    def _render_layout(self):
        # Heights budgeted so the whole TUI fits in ~32 terminal rows:
        #   header  = 4   (progress panel)
        #   middle  = 18  (workers panel: 8 worker rows + borders = ~12;
        #                  dashboard panel: hdr + 3 mini-sections with labels
        #                  = ~15 at peak — 18 is comfortable for both without
        #                  leaving huge empty inner space like `ratio=1` did)
        #   recent  = RECENT_TAIL + 4  (6 recent rows + borders = 10)
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="middle", size=18),
            Layout(name="recent", size=RECENT_TAIL + 4),
        )
        layout["header"].update(
            Panel(self._progress, title=f"[bold]{self.title}[/]",
                  title_align="left", border_style="cyan")
        )
        layout["middle"].split_row(
            Layout(name="workers", ratio=2),
            Layout(name="stats", ratio=1, minimum_size=26),
        )
        layout["middle"]["workers"].update(
            Panel(self._render_workers_table(),
                  title=f"Workers ({self.n_workers})",
                  title_align="left", border_style="blue")
        )
        layout["middle"]["stats"].update(
            Panel(self._render_dashboard(), title="Dashboard",
                  title_align="left", border_style="magenta")
        )
        layout["recent"].update(
            Panel(self._render_recent_table(), title="Recent",
                  title_align="left", border_style="green")
        )
        return layout

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "LiveTUI":
        self._live = Live(
            self._render_layout(), console=self.console,
            refresh_per_second=self._refresh, screen=False,
            transient=False, get_renderable=self._render_layout,
        )
        self._live.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._live is not None:
            self._live.__exit__(exc_type, exc, tb)
            self._live = None

    def print_summary(self) -> None:
        session_done = (
            self._found + self._no_site + self._no_results
            + self._rate_limit + self._db_write_failed + self._other
        )
        elapsed = time.monotonic() - self._started
        rate = session_done / elapsed if elapsed > 0 else 0
        hit_pct = self._found * 100.0 / max(1, session_done)
        self.console.rule("[bold cyan]Run complete")
        self.console.print(
            f"[bold green]✓ {self._found:,} URLs found[/] "
            f"([green]{hit_pct:.1f}%[/] hit-rate) in "
            f"[bold]{elapsed:.0f}s[/] "
            f"([cyan]{rate:.2f}/s[/])"
        )
        self.console.print(
            f"[dim]Skipped:[/] ⊘ {self._no_site:,} no-own-site  "
            f"∅ {self._no_results:,} no-results  "
            f"⚠ {self._db_write_failed:,} DB fail  "
            f"↻ {self._rate_limit:,} rate-limit"
        )
        self.console.print(
            f"[dim]Checkpoint:[/] [cyan]{self.checkpoint_path}[/]  "
            f"[dim](re-run to resume any remaining)[/]"
        )


def run_one(
    entry: Entry, slot: int, *, api_key: str, checkpoint: Checkpoint,
    dry_run: bool, tui: Optional[LiveTUI],
) -> tuple[Entry, int, Optional[str], Optional[str]]:
    if checkpoint.already_processed(entry.id):
        return entry, slot, None, "already_processed"
    if tui:
        tui.on_worker_start(slot, entry)
    t0 = time.monotonic()
    url, reason, position = fetch_url_via_searchapi(
        api_key=api_key, title=entry.title, city=entry.city,
    )
    if url and not dry_run:
        try:
            update_craft_entry_url(entry.id, url)
        except Exception as e:
            reason = f"db_write_failed:{type(e).__name__}"
            url = None
    checkpoint.record(entry_id=entry.id, url=url, reason=reason, position=position)
    elapsed = time.monotonic() - t0
    if tui:
        tui.on_worker_finish(slot, entry, url, reason, position, elapsed)
    return entry, slot, url, reason


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--sections", default="2,3,4,5,6",
                   help="Craft section IDs to enrich (default: 2,3,4,5,6)")
    p.add_argument("--limit", type=int, help="Max entries to process this run")
    p.add_argument("--workers", type=int, default=5, help="Concurrent API calls (default: 5)")
    p.add_argument("--test", type=int, metavar="ENTRY_ID",
                   help="Dry-run on one entry id; prints what we'd write")
    p.add_argument("--dry-run", action="store_true",
                   help="Call SearchAPI but don't UPDATE Craft")
    p.add_argument("--no-tui", action="store_true",
                   help="Plain log output instead of the live rich UI")
    p.add_argument("--checkpoint", type=Path, default=CHECKPOINT_DEFAULT)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S", level=logging.INFO)
    args = build_parser().parse_args(argv)
    api_key = os.environ.get(SEARCHAPI_KEY_ENV) or SEARCHAPI_KEY_FALLBACK
    if not api_key:
        log.error("Set %s or update SEARCHAPI_KEY_FALLBACK", SEARCHAPI_KEY_ENV)
        return 2

    if args.test is not None:
        # Fetch the single entry by id
        sql = (
            "SELECT CONCAT('{\"id\":', e.id, "
            "',\"sid\":', e.sectionId, "
            "',\"title\":', COALESCE(JSON_QUOTE(es.title), 'null'), "
            "',\"city\":', COALESCE(JSON_QUOTE(JSON_UNQUOTE(JSON_EXTRACT(es.content, "
            f"'$.\"{CITY_FIELD_UID}\"'))), 'null'), "
            "'}') AS j "
            "FROM entries e JOIN elements_sites es ON es.elementId=e.id AND es.siteId=1 "
            f"WHERE e.id = {int(args.test)}"
        )
        proc = subprocess.run(
            ["ddev", "mysql", "db", "--skip-column-names", "--raw", "-e", sql],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            log.error("Entry %s not found (or ddev mysql failed)", args.test)
            return 2
        r = json.loads(proc.stdout.strip().splitlines()[0])
        e = Entry(id=int(r["id"]), section_id=int(r["sid"]),
                  title=(r.get("title") or "").strip(),
                  city=(r.get("city") or "").strip())
        log.info("Testing: id=%s section=%s title=%r city=%r",
                 e.id, e.section_id, e.title, e.city)
        url, reason, position = fetch_url_via_searchapi(
            api_key=api_key, title=e.title, city=e.city)
        log.info("Would write url=%s reason=%s position=%s", url, reason, position)
        return 0

    sections = [int(s) for s in args.sections.split(",") if s.strip()]
    console = Console()
    console.rule("[bold cyan]SearchAPI URL Enrichment")
    console.print(
        f"[dim]Sections[/] {sections}  "
        f"[dim]Workers[/] {args.workers}  "
        f"[dim]Limit[/] {args.limit or '[unbounded]'}"
    )
    console.print(f"[dim]Loading candidates from Craft…[/]")
    entries = load_missing_url_entries(sections=sections, limit=args.limit)
    cp = Checkpoint(args.checkpoint)
    fresh = [e for e in entries if not cp.already_processed(e.id)]
    already = len(entries) - len(fresh)
    console.print(
        f"[bold]{len(entries):,}[/] candidates · "
        f"[green]{already:,}[/] already in checkpoint · "
        f"[bold yellow]{len(fresh):,}[/] to process this run"
    )
    if not fresh:
        console.print("[green]Nothing to do — every target is already in the checkpoint.[/]")
        return 0

    # Graceful Ctrl+C — set the stop event so in-flight workers finish then we bail
    stop = threading.Event()
    def _handle_sigint(signum, frame):
        if not stop.is_set():
            console.print("\n[yellow]Ctrl+C received — finishing in-flight workers, then stopping. Checkpoint is safe.[/]")
            stop.set()
        else:
            console.print("\n[red]Second Ctrl+C — forcing exit.[/]")
            sys.exit(130)
    signal.signal(signal.SIGINT, _handle_sigint)

    # Build the TUI (or a no-op fallback if --no-tui)
    use_tui = not args.no_tui and sys.stdout.isatty()
    tui = LiveTUI(
        total=len(fresh), already_done=0, n_workers=args.workers,
        checkpoint_path=args.checkpoint, console=console,
    ) if use_tui else None
    if tui:
        _switch_logger_to_rich(tui.console)
        tui.log(
            f"Checkpoint [cyan]{args.checkpoint}[/] — "
            f"[bold green]resumable, Ctrl+C anytime[/] "
            f"· SearchAPI [bold]Production (35k/mo)[/]"
        )

    # Slot queue — one stable slot per in-flight worker. Matches the
    # clinic_emails/cli.py pattern. get() on entry, put() on exit.
    slots: queue.Queue = queue.Queue()
    for i in range(args.workers):
        slots.put(i)

    def _worker(entry: Entry) -> tuple[Entry, Optional[str], Optional[str]]:
        if stop.is_set():
            return entry, None, "aborted"
        slot = slots.get()
        try:
            _, _, url, reason = run_one(
                entry, slot, api_key=api_key, checkpoint=cp,
                dry_run=args.dry_run, tui=tui,
            )
            return entry, url, reason
        finally:
            slots.put(slot)

    ctx = tui if tui else _nullcontext()
    with ctx:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = [pool.submit(_worker, e) for e in fresh]
            for fut in as_completed(futures):
                entry, url, reason = fut.result()
                if reason == "quota_exhausted":
                    if tui:
                        tui.log("[bold red]SearchAPI quota exhausted — cancelling remaining work.[/]")
                    else:
                        console.print("[bold red]SearchAPI quota exhausted — cancelling remaining work.[/]")
                    stop.set()
                    for f in futures:
                        f.cancel()
                    break
                if not tui and not stop.is_set():
                    # Plain log-mode progress
                    if url:
                        console.print(f"[green]✓[/] {entry.id} {_truncate(entry.title, 50)} → {_bare_host(url)}")
                    elif reason == "no_results":
                        console.print(f"[dim]∅ {entry.id} {_truncate(entry.title, 50)}[/]")
                    elif reason and reason.startswith("all_banned"):
                        console.print(f"[yellow]⊘ {entry.id} {_truncate(entry.title, 50)} (directory only)[/]")

    if tui:
        tui.print_summary()
    return 0


class _nullcontext:
    def __enter__(self):
        return None
    def __exit__(self, *args):
        return False


if __name__ == "__main__":
    sys.exit(main())
