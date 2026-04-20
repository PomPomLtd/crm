"""Deterministic A/B/C variant assignment.

Bucketing by SHA-256(email) mod 3 ensures:
  - Same recipient always gets the same variant across re-runs.
  - An uneven list still yields ~equal A/B/C groups for any large enough N.
  - The assignment is salt-able per campaign if we ever want independent
    assignments across two campaigns to the same recipient.
"""

from __future__ import annotations

import hashlib
from typing import Sequence

VARIANTS: tuple[str, ...] = ("A", "B", "C")


def assign_variant(
    email: str,
    *,
    salt: str = "",
    variants: Sequence[str] = VARIANTS,
) -> str:
    normalized = email.strip().lower().encode("utf-8")
    key = (salt.encode("utf-8") + b":" + normalized) if salt else normalized
    digest = hashlib.sha256(key).digest()
    idx = int.from_bytes(digest[:8], "big") % len(variants)
    return variants[idx]
