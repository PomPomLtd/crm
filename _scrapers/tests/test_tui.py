"""Unit tests for clinic_emails.tui — state management glue, not Rich rendering.

We assert that worker hooks update the shared state correctly, that the
recent-completions deque rotates, and that the helpers format input as
expected. We do not exercise the Rich Live render loop.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from clinic_emails.tui import (
    RECENT_TAIL,
    LiveTUI,
    _Completion,
    _host_of,
    _status_glyph,
    _truncate,
)
from clinic_emails import cli as cli_mod


# ---- helpers ----


def test_host_of_strips_www_and_path():
    assert _host_of("https://www.example.ch/foo/bar") == "example.ch"
    assert _host_of("http://example.ch") == "example.ch"
    assert _host_of("https://sub.example.ch/x") == "sub.example.ch"


def test_host_of_handles_garbage():
    assert _host_of("") == ""
    assert _host_of("not a url") == ""


def test_truncate_short_strings_unchanged():
    assert _truncate("hi", 10) == "hi"
    assert _truncate("exactly 12", 10) == "exactly 12"  # equals limit → unchanged
    assert _truncate("a much longer string", 10) == "a much lo…"
    assert _truncate("", 5) == ""


def test_status_glyph_uses_distinct_colours():
    assert "✓" in str(_status_glyph("success"))
    assert "✓" in str(_status_glyph("success_via_root"))
    assert "⚠" in str(_status_glyph("no_emails"))
    assert "✗" in str(_status_glyph("fetch_failed"))
    assert "✗" in str(_status_glyph("error"))


# ---- LiveTUI state transitions ----


def _tui(n_workers: int = 4, total: int = 100, already_done: int = 0) -> LiveTUI:
    return LiveTUI(total=total, already_done=already_done, n_workers=n_workers)


def test_worker_start_records_slot_state():
    tui = _tui()
    entry = {"id": 42, "title": "Test Clinic", "url": "https://test.ch", "section": "clinics"}
    tui.on_worker_start(0, entry)
    assert tui._workers[0] is not None
    assert tui._workers[0].entry_id == 42
    assert tui._workers[0].host == "test.ch"


def test_worker_finish_clears_slot_and_increments_counters():
    tui = _tui()
    entry = {"id": 1, "title": "X", "url": "https://x.ch", "section": "clinics"}
    result = {
        "status": "success",
        "emails": {"priority": ["a@b.ch", "c@d.ch"], "general": ["dr@b.ch"], "other": []},
    }
    tui.on_worker_start(0, entry)
    tui.on_worker_finish(0, entry, result, 1.5)

    assert tui._workers[0] is None
    assert tui._counts["success"] == 1
    assert tui._by_section["clinics"] == 1
    assert tui._emails_total == 3
    assert tui._priority_total == 2


def test_recent_deque_rotates_at_capacity():
    tui = _tui(n_workers=1)
    for i in range(RECENT_TAIL + 5):
        entry = {"id": i, "title": f"E{i}", "url": "https://x.ch", "section": "clinics"}
        tui.on_worker_start(0, entry)
        tui.on_worker_finish(0, entry,
                             {"status": "no_emails", "emails": {"priority": [], "general": [], "other": []}},
                             0.1)
    assert len(tui._recent) == RECENT_TAIL
    # Newest entry is at position 0 (appendleft)
    newest = tui._recent[0]
    assert newest.entry_id == RECENT_TAIL + 4


def test_already_done_seeds_progress_completed():
    tui = _tui(already_done=12207, total=18046)
    # The Progress task must report we're already 12207 in.
    task = tui._progress.tasks[tui._task_id]
    assert task.completed == 12207
    assert task.total == 18046


def test_render_layout_does_not_raise_with_partial_state():
    tui = _tui()
    # Some workers idle, some active, some recents
    tui.on_worker_start(1, {"id": 1, "title": "Alpha", "url": "https://a.ch"})
    tui.on_worker_start(3, {"id": 2, "title": "Bravo " * 50, "url": "https://b.ch"})
    tui.on_worker_finish(1, {"id": 1, "title": "Alpha", "url": "https://a.ch", "section": "clinics"},
                         {"status": "fetch_failed", "emails": {}}, 9.9)
    layout = tui._render_layout()
    assert layout is not None  # render didn't blow up


# ---- CLI flag wiring ----


def test_no_tui_flag_recognised():
    parser = cli_mod._build_parser()
    args = parser.parse_args(["--no-tui"])
    assert args.no_tui is True


def test_no_tui_default_is_false():
    parser = cli_mod._build_parser()
    args = parser.parse_args([])
    assert args.no_tui is False
