"""Live terminal UI for the scraper.

A thin wrapper around Rich primitives. The scraper threads call into the
update hooks (`on_worker_start`, `on_worker_finish`, `on_progress`); a
background render loop owned by `rich.live.Live` re-paints the layout 4×
per second.

Designed to be invisible to the rest of the scraper: the CLI either wraps
the worker pool in `with LiveTUI(...) as tui:` or skips it entirely (the
`--no-tui` path keeps the legacy log output).
"""

from __future__ import annotations

import threading
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Iterable, Optional
from urllib.parse import urlparse

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

# How many recent completions to keep in the scrolling tail panel.
RECENT_TAIL = 6


# ---------------------------------------------------------------------------
# State containers
# ---------------------------------------------------------------------------


@dataclass
class _WorkerSlot:
    entry_id: int
    title: str
    host: str
    started_at: float


@dataclass
class _Completion:
    ts: float
    entry_id: int
    title: str
    status: str
    priority: int
    general: int
    other: int
    elapsed: float
    error: Optional[str] = None


def _host_of(url: str) -> str:
    try:
        h = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return h.removeprefix("www.")[:32]


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _status_glyph(status: str) -> Text:
    if status in ("success", "success_via_root"):
        return Text("✓", style="bold green")
    if status == "no_emails":
        return Text("⚠", style="yellow")
    if status in ("fetch_failed", "error"):
        return Text("✗", style="bold red")
    return Text("·", style="dim")


# ---------------------------------------------------------------------------
# Main TUI class
# ---------------------------------------------------------------------------


class LiveTUI:
    """Owns the Rich Live display + thread-safe shared state.

    Use as a context manager around the worker pool. Worker threads call
    the `on_*` hooks; a background thread driven by `rich.live.Live`
    re-renders the layout.
    """

    def __init__(
        self,
        *,
        total: int,
        already_done: int,
        n_workers: int,
        title: str = "MediTransfer Email Scraper",
        console: Optional[Console] = None,
        refresh_per_second: int = 4,
    ):
        self.total = total
        self.n_workers = n_workers
        self.title = title
        self.console = console or Console()
        self._refresh = refresh_per_second

        # Shared state — every read/write goes through self._lock
        self._lock = threading.Lock()
        self._workers: Dict[int, Optional[_WorkerSlot]] = {i: None for i in range(n_workers)}
        self._counts: Counter[str] = Counter()
        self._by_section: Counter[str] = Counter()
        self._emails_total = 0
        self._priority_total = 0
        self._recent: Deque[_Completion] = deque(maxlen=RECENT_TAIL)
        self._started = time.monotonic()
        self._already_done = already_done

        # Progress bar lives outside the Layout so its render keeps state
        # (e.g. ETA smoothing) across re-renders.
        self._progress = Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[bold]Progress"),
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
        self._task_id = self._progress.add_task("scraping", total=total, completed=already_done, rate="0/s")
        self._live: Optional[Live] = None

    # ------------------------------------------------------------------
    # Worker hooks (called from worker threads)
    # ------------------------------------------------------------------

    def on_worker_start(self, slot: int, entry: Dict[str, Any]) -> None:
        with self._lock:
            self._workers[slot] = _WorkerSlot(
                entry_id=int(entry.get("id", 0) or 0),
                title=str(entry.get("title") or ""),
                host=_host_of(str(entry.get("url") or "")),
                started_at=time.monotonic(),
            )

    def on_worker_finish(
        self,
        slot: int,
        entry: Dict[str, Any],
        result: Dict[str, Any],
        elapsed: float,
    ) -> None:
        ems = result.get("emails") or {}
        priority = len(ems.get("priority") or [])
        general = len(ems.get("general") or [])
        other = len(ems.get("other") or [])
        status = str(result.get("status") or "error")
        completion = _Completion(
            ts=time.time(),
            entry_id=int(entry.get("id", 0) or 0),
            title=str(entry.get("title") or ""),
            status=status,
            priority=priority,
            general=general,
            other=other,
            elapsed=elapsed,
            error=(result.get("error") or None),
        )
        section = str(entry.get("section") or "")

        with self._lock:
            self._workers[slot] = None
            self._counts[status] += 1
            if section:
                self._by_section[section] += 1
            self._emails_total += priority + general + other
            self._priority_total += priority
            self._recent.appendleft(completion)
            done_total = self._already_done + sum(self._counts.values())
            elapsed_total = time.monotonic() - self._started
            rate = (sum(self._counts.values()) / elapsed_total) if elapsed_total > 0 else 0.0

        self._progress.update(
            self._task_id,
            completed=done_total,
            rate=f"{rate:.2f}/s",
        )

    # ------------------------------------------------------------------
    # Logging into the Live region
    # ------------------------------------------------------------------

    def log(self, message: str, *, style: str = "") -> None:
        """Print a one-off line above the live region (won't clobber layout)."""
        self.console.log(message if not style else Text(message, style=style))

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _render_workers_table(self) -> Table:
        t = Table.grid(padding=(0, 1), expand=True)
        t.add_column("#", justify="right", style="dim", no_wrap=True, width=3)
        t.add_column("Entry", justify="right", style="cyan", no_wrap=True, width=8)
        t.add_column("Title", overflow="ellipsis", no_wrap=True)
        t.add_column("Host", style="magenta", no_wrap=True, overflow="ellipsis", max_width=28)
        t.add_column("Elapsed", justify="right", no_wrap=True, width=7)

        now = time.monotonic()
        with self._lock:
            slots = list(self._workers.items())

        for slot, worker in slots:
            if worker is None:
                t.add_row(
                    f"#{slot+1}",
                    Text("--", style="dim"),
                    Text("idle", style="dim"),
                    "",
                    "",
                )
            else:
                el = now - worker.started_at
                style = "yellow" if el > 8 else ""
                t.add_row(
                    f"#{slot+1}",
                    str(worker.entry_id),
                    Text(_truncate(worker.title, 60), style=style),
                    worker.host,
                    Text(f"{el:5.1f}s", style=style),
                )
        return t

    def _render_stats_table(self) -> Table:
        t = Table.grid(padding=(0, 1), expand=True)
        t.add_column("Label", no_wrap=True, justify="left")
        t.add_column("Value", no_wrap=True, justify="right", style="bold")

        with self._lock:
            ok = self._counts.get("success", 0) + self._counts.get("success_via_root", 0)
            no_emails = self._counts.get("no_emails", 0)
            failed = self._counts.get("fetch_failed", 0)
            errors = self._counts.get("error", 0)
            emails = self._emails_total
            priority = self._priority_total
            sections = self._by_section.most_common(5)

        t.add_row(Text("✓ success", style="green"), str(ok))
        t.add_row(Text("⚠ no_emails", style="yellow"), str(no_emails))
        t.add_row(Text("✗ fetch_failed", style="red"), str(failed))
        t.add_row(Text("  error", style="red"), str(errors))
        t.add_row("", "")
        t.add_row(Text("emails", style="cyan"), f"{emails:,}")
        t.add_row(Text("priority", style="cyan"), f"{priority:,}")
        if sections:
            t.add_row("", "")
            t.add_row(Text("by section", style="dim"), "")
            for sec, n in sections:
                t.add_row(Text(f"  {sec}", style="dim"), f"{n:,}")
        return t

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
            t.add_row("", "", "", Text("(no completions yet)", style="dim"), "", "")
            return t

        for c in recent:
            ts = time.strftime("%H:%M:%S", time.localtime(c.ts))
            glyph = _status_glyph(c.status)
            if c.status in ("success", "success_via_root"):
                if c.priority:
                    bits = []
                    if c.priority: bits.append(f"{c.priority} priority")
                    if c.general: bits.append(f"{c.general} general")
                    if c.other: bits.append(f"{c.other} other")
                    desc = " + ".join(bits)
                else:
                    desc = f"{c.general + c.other} email(s)"
                desc_text = Text(desc, style="green")
            elif c.status == "no_emails":
                desc_text = Text("no emails found", style="yellow")
            elif c.status == "fetch_failed":
                desc_text = Text("fetch_failed", style="red")
            elif c.status == "error":
                desc_text = Text(f"error: {_truncate(c.error or '', 40)}", style="red")
            else:
                desc_text = Text(c.status, style="dim")
            t.add_row(
                ts,
                glyph,
                str(c.entry_id),
                _truncate(c.title, 50),
                desc_text,
                f"{c.elapsed:5.1f}s",
            )
        return t

    def _render_layout(self) -> Layout:
        layout = Layout()
        # Fixed sizes instead of ratio=1 — prevents the middle section from
        # greedily taking all remaining terminal height and pushing the
        # header off-screen on tall terminals. Total budget:
        #   header 4 + middle 14 (n_workers rows + border + title) + stats
        #   is bounded by workers panel height + recent 10 (6+border) = ~28 rows.
        middle_size = max(14, self.n_workers + 4)
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="middle", size=middle_size),
            Layout(name="recent", size=RECENT_TAIL + 4),
        )
        layout["header"].update(
            Panel(
                self._progress,
                title=f"[bold]{self.title}[/]",
                title_align="left",
                border_style="cyan",
            )
        )
        layout["middle"].split_row(
            Layout(name="workers", ratio=2),
            Layout(name="stats", ratio=1, minimum_size=28),
        )
        layout["middle"]["workers"].update(
            Panel(self._render_workers_table(), title="Workers", title_align="left", border_style="blue")
        )
        layout["middle"]["stats"].update(
            Panel(self._render_stats_table(), title="Stats", title_align="left", border_style="magenta")
        )
        layout["recent"].update(
            Panel(self._render_recent_table(), title="Recent", title_align="left", border_style="green")
        )
        return layout

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "LiveTUI":
        self._live = Live(
            self._render_layout(),
            console=self.console,
            refresh_per_second=self._refresh,
            screen=False,
            transient=False,
            get_renderable=self._render_layout,
        )
        self._live.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._live is not None:
            self._live.__exit__(exc_type, exc, tb)
            self._live = None
