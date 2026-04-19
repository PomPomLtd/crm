"""Append-only JSONL checkpoint for resumable runs.

Each processed entry writes one line with the result. On startup we read the
file to recover the set of already-processed entry IDs so a crash/cancel/resume
never re-processes anything.

Writes are guarded by a lock and flushed immediately for crash-safety.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, Iterator, Set


class Checkpoint:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._lock = threading.Lock()
        self.done: Set[int] = self._scan_done_ids()
        self._fh = open(path, "a", encoding="utf-8")

    def _scan_done_ids(self) -> Set[int]:
        if not os.path.exists(self.path):
            return set()
        ids: Set[int] = set()
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    eid = rec.get("entry_id")
                    if eid is not None:
                        ids.add(int(eid))
                except Exception:
                    pass
        return ids

    def record(self, result: Dict[str, Any]) -> None:
        with self._lock:
            self._fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            self._fh.flush()
            eid = result.get("entry_id")
            if eid is not None:
                try:
                    self.done.add(int(eid))
                except (TypeError, ValueError):
                    pass

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass

    def iter_records(self) -> Iterator[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return iter(())
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
