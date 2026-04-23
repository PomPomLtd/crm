"""DB entries loader.

Pulls target clinic/hospital/etc. entries from the Craft CMS DB via `ddev mysql`
and extracts the practice website URL from each entry's content JSON.

The content JSON uses field-layout-element UIDs as keys (not field handles), so
we can't filter by a specific UID — the practice URL is whichever URL-typed
value isn't onedoc.ch, google.*, LinkedIn, or one of the other directory sites.

Cached locally as a JSON file; the CLI can force a refresh.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .patterns import NON_PRACTICE_HOSTS


_DUMP_QUERY = (
    "SELECT CONCAT("
    "'{\"id\":', e.id, "
    "',\"section\":', JSON_QUOTE(s.handle), "
    "',\"title\":', COALESCE(JSON_QUOTE(es.title), 'null'), "
    "',\"content\":', es.content, "
    "'}' ) AS j "
    "FROM entries e "
    "JOIN elements_sites es ON es.elementId = e.id AND es.siteId = 1 "
    "JOIN sections s ON s.id = e.sectionId "
    "JOIN elements el ON el.id = e.id "
    "WHERE e.sectionId IN (2,3,4,5,6) "
    "AND el.dateDeleted IS NULL "
    "AND el.archived = 0"
)

# --- Canton extraction (same token approach as mailer/targets.py) ---
# Maps full German/French/Italian canton names + 2-letter codes to the
# canonical 2-letter code.
_CANTON_TOKENS: Dict[str, str] = {
    "zh": "ZH", "be": "BE", "lu": "LU", "ur": "UR", "sz": "SZ", "ow": "OW",
    "nw": "NW", "gl": "GL", "zg": "ZG", "fr": "FR", "so": "SO", "bs": "BS",
    "bl": "BL", "sh": "SH", "ar": "AR", "ai": "AI", "sg": "SG", "gr": "GR",
    "ag": "AG", "tg": "TG", "ti": "TI", "vd": "VD", "vs": "VS", "ne": "NE",
    "ge": "GE", "ju": "JU",
    "zürich": "ZH", "zuerich": "ZH", "bern": "BE", "berne": "BE",
    "luzern": "LU", "lucerne": "LU", "basel-stadt": "BS",
    "basel-landschaft": "BL", "basel": "BS",
    "st. gallen": "SG", "st.gallen": "SG", "sankt gallen": "SG",
    "graubünden": "GR", "graubunden": "GR",
    "tessin": "TI", "ticino": "TI", "waadt": "VD", "vaud": "VD",
    "wallis": "VS", "valais": "VS", "neuenburg": "NE",
    "neuchâtel": "NE", "neuchatel": "NE", "genf": "GE",
    "genève": "GE", "geneve": "GE", "genf / geneve": "GE",
    "freiburg": "FR", "fribourg": "FR", "schwyz": "SZ",
    "obwalden": "OW", "nidwalden": "NW", "glarus": "GL",
    "zug": "ZG", "solothurn": "SO", "schaffhausen": "SH",
    "appenzell ausserrhoden": "AR", "appenzell innerrhoden": "AI",
    "aargau": "AG", "thurgau": "TG", "uri": "UR", "jura": "JU",
}

# DACH-default canton set — German-speaking cantons only. Excludes Romandie
# (GE, VD, NE, JU), predominantly-French bilingual (FR, VS), and Ticino (TI).
# Our mailer templates are DE-only, so crawling non-DACH practices burns
# time for addresses we can't actually cold-email yet.
DEFAULT_CANTONS: tuple = (
    "ZH", "BE", "AG", "LU", "SG", "BS", "BL", "SO", "TG", "SH",
    "SZ", "ZG", "GR", "AR", "AI", "OW", "NW", "UR", "GL",
)


def extract_canton_code(content_obj: Any) -> str:
    """Walk content JSON; return 2-letter canton code if any value matches a
    known canton name/code. Returns '' if no canton found."""
    if not isinstance(content_obj, dict):
        return ""
    for val in content_obj.values():
        if isinstance(val, str):
            s = val.strip().lower().rstrip(".").strip()
        elif isinstance(val, dict):
            raw = val.get("value") if val.get("type") != "url" else None
            s = raw.strip().lower().rstrip(".").strip() if isinstance(raw, str) else ""
        else:
            continue
        if not s:
            continue
        code = _CANTON_TOKENS.get(s)
        if code:
            return code
    return ""


def _host_bare(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower().lstrip(".")
    except Exception:
        return ""
    return host.removeprefix("www.")


def extract_practice_url(content_obj: Any) -> str:
    """Pick the first URL-typed content value that isn't a known directory site."""
    if not isinstance(content_obj, dict):
        return ""
    for val in content_obj.values():
        if not (isinstance(val, dict) and val.get("type") == "url"):
            continue
        u = (val.get("value") or "").strip()
        if not u:
            continue
        host = _host_bare(u)
        if not host:
            continue
        if any(host == skip or host.endswith("." + skip) for skip in NON_PRACTICE_HOSTS):
            continue
        return u
    return ""


def dump_from_db(cache_path: str, repo_root: str, logger) -> List[Dict[str, Any]]:
    """Run the DB query via `ddev mysql`, filter, cache."""
    logger.info("Dumping entries from DB (ddev mysql)…")
    proc = subprocess.run(
        ["ddev", "mysql", "db", "--skip-column-names", "--raw", "-e", _DUMP_QUERY],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ddev mysql failed:\n{proc.stderr}")

    total = 0
    parse_errors = 0
    entries: List[Dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue
        url = extract_practice_url(raw.get("content"))
        if not url:
            continue
        canton = extract_canton_code(raw.get("content"))
        entries.append(
            {
                "id": raw["id"],
                "section": raw.get("section", ""),
                "title": raw.get("title", ""),
                "url": url,
                "canton": canton,
            }
        )

    no_url = total - len(entries) - parse_errors
    logger.info(
        f"DB dump: {total} rows / {len(entries)} with practice URL / "
        f"{no_url} without URL / {parse_errors} parse errors"
    )
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    logger.info(f"Cached to {cache_path}")
    return entries


def load_entries(
    cache_path: str, repo_root: str, refresh: bool, logger
) -> List[Dict[str, Any]]:
    if refresh or not os.path.exists(cache_path):
        return dump_from_db(cache_path, repo_root, logger)
    with open(cache_path, "r", encoding="utf-8") as f:
        entries = json.load(f)
    logger.info(f"Loaded {len(entries)} entries from {cache_path}")
    return entries
