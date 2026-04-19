"""HTTP layer — session, per-domain rate limit, homepage + contact-page crawl.

Design decisions:
- Thread-local `requests.Session` so each worker has its own connection pool.
- A `DomainRateLimiter` keyed by hostname gates same-domain requests. Different
  hostnames proceed in parallel; same hostname is serialized with a random
  1-3s delay between hits. Cross-entry collisions (rare, since each entry is
  usually a distinct clinic) are handled naturally.
- Contact-page discovery uses weighted hint matching on same-origin <a> links.
  Weights are defined in patterns.CONTACT_HINT_WEIGHTS so kontakt/contact
  outrank datenschutz/privacy.
- Fallbacks: if the entry URL returns 404/410, we try the domain root. If the
  homepage has no usable contact links, we probe a short list of conventional
  paths (/kontakt, /impressum, /contact, …).
"""

from __future__ import annotations

import random
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .extractors import extract_emails
from .patterns import (
    CONTACT_HINT_WEIGHTS,
    DEFAULT_HEADERS,
    FALLBACK_PROBE_PATHS,
    SKIP_PATH_EXTENSIONS,
)
from .referral import aggregate as aggregate_referral
from .referral import detect_referral_signals, score_referral_links


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


def make_session(total_retries: int = 3, backoff_factor: float = 1.5) -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    retry = Retry(
        total=total_retries,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
        backoff_factor=backoff_factor,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retry, pool_connections=20, pool_maxsize=20
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_thread_local = threading.local()


def thread_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        _thread_local.session = make_session()
    return _thread_local.session


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class DomainRateLimiter:
    """Per-host serialization + min random delay between same-host requests."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self._locks: Dict[str, threading.Lock] = {}
        self._last_hit: Dict[str, float] = {}
        self._registry_lock = threading.Lock()
        self.min_delay = min_delay
        self.max_delay = max_delay

    def lock_for(self, host: str) -> threading.Lock:
        with self._registry_lock:
            lk = self._locks.get(host)
            if lk is None:
                lk = threading.Lock()
                self._locks[host] = lk
            return lk

    def wait(self, host: str) -> None:
        """Sleep if we hit the same host recently."""
        last = self._last_hit.get(host, 0.0)
        need = random.uniform(self.min_delay, self.max_delay)
        gap = time.time() - last
        if gap < need:
            time.sleep(need - gap)
        self._last_hit[host] = time.time()


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def fetch_html(
    url: str,
    rl: DomainRateLimiter,
    stop: threading.Event,
    timeout: float = 20.0,
) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """Fetch URL under per-domain serialization.

    Returns (html, status_code, final_url) — any of which may be None on
    failure. Only html-like content types are returned as html; other types
    return (None, status, final_url).
    """
    if stop.is_set():
        return None, None, None
    host = urlparse(url).netloc.lower()
    if not host:
        return None, None, None
    lock = rl.lock_for(host)
    with lock:
        if stop.is_set():
            return None, None, None
        rl.wait(host)
        try:
            resp = thread_session().get(url, timeout=timeout, allow_redirects=True)
        except requests.RequestException:
            return None, None, None
        status = resp.status_code
        final_url = resp.url
        if status >= 400:
            return None, status, final_url
        ct = resp.headers.get("content-type", "").lower()
        if ct and not any(x in ct for x in ("html", "xml", "text")):
            return None, status, final_url
        return resp.text, status, final_url


# ---------------------------------------------------------------------------
# Contact-page discovery
# ---------------------------------------------------------------------------


def _host_bare(host: str) -> str:
    return host.lower().lstrip(".").removeprefix("www.")


def score_contact_links(html: str, base_url: str, limit: int = 4) -> List[Tuple[str, int]]:
    """Parse same-origin <a> links, score by contact hint weights, return top N."""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    base_host = _host_bare(urlparse(base_url).netloc)
    base_clean = base_url.split("#", 1)[0].rstrip("/")

    candidates: Dict[str, int] = {}
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if _host_bare(parsed.netloc) != base_host:
            continue
        path = parsed.path.lower().rstrip("/")
        if any(path.endswith(ext) for ext in SKIP_PATH_EXTENSIONS):
            continue

        link_text = (a.get_text(" ", strip=True) or "").lower()
        score = 0
        for hint, weight in CONTACT_HINT_WEIGHTS.items():
            if hint in path:
                score += weight
            if hint in link_text:
                score += max(1, weight - 1)
        if score <= 0:
            continue

        normalized = absolute.split("#", 1)[0].rstrip("/")
        if normalized == base_clean:
            continue  # skip link back to the same page we're on
        if normalized not in candidates or score > candidates[normalized]:
            candidates[normalized] = score

    ranked = sorted(candidates.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:limit]


def probe_fallback_paths(
    base_url: str, rl: DomainRateLimiter, stop: threading.Event
) -> List[str]:
    """HEAD a handful of conventional contact paths; return ones that 2xx."""
    p = urlparse(base_url)
    if not p.netloc:
        return []
    root = f"{p.scheme}://{p.netloc}"
    hits: List[str] = []
    for path in FALLBACK_PROBE_PATHS:
        if stop.is_set():
            break
        target = root + path
        host = p.netloc.lower()
        with rl.lock_for(host):
            if stop.is_set():
                break
            rl.wait(host)
            try:
                r = thread_session().head(target, timeout=10, allow_redirects=True)
            except requests.RequestException:
                continue
            if 200 <= r.status_code < 400:
                hits.append(r.url)
    # dedupe while preserving order
    seen = set()
    unique = []
    for u in hits:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique[:4]


# ---------------------------------------------------------------------------
# Per-entry pipeline
# ---------------------------------------------------------------------------


def crawl_entry(
    url: str,
    rl: DomainRateLimiter,
    stop: threading.Event,
    max_contact_pages: int = 4,
    max_referral_pages: int = 2,
) -> Dict[str, object]:
    """Fetch homepage + top contact + top referral pages.

    Returns {emails, sources, pages, status, referral}.

    Behavior:
    - If the entry URL 404s, retries at the domain root.
    - If the homepage has no contact link candidates, probes FALLBACK_PROBE_PATHS.
    - Referral pages are discovered via REFERRAL_HINT_WEIGHTS scoring and
      crawled in addition to (and de-duped against) contact pages.
    - Email extraction AND referral detection both run on every fetched page,
      so we get both data sets from one HTTP pass.
    - Same-domain rate limiting via `rl`.
    """
    result: Dict[str, Any] = {
        "emails": set(),
        "sources": {},
        "pages": [],
        "status": "no_url",
        "referral": {"found": False},
    }

    url = (url or "").strip()
    if not url:
        return result
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    html, status, final_url = fetch_html(url, rl, stop)
    primary = final_url or url

    # 404 fallback: try the domain root
    if html is None and status in (404, 410):
        p = urlparse(url)
        root = f"{p.scheme}://{p.netloc}/"
        if root.rstrip("/") != url.rstrip("/"):
            html, status, final_url = fetch_html(root, rl, stop)
            primary = final_url or root
            if html is not None:
                result["status"] = "success_via_root"

    if html is None:
        result["status"] = "fetch_failed"
        return result

    if result["status"] == "no_url":
        result["status"] = "success"

    pages: List[str] = [primary]
    referral_findings: List[Dict[str, Any]] = []

    def _process(html_text: str, page_url: str) -> None:
        for email in extract_emails(html_text):
            if email not in result["sources"]:
                result["sources"][email] = page_url
                result["emails"].add(email)  # type: ignore[attr-defined]
        finding = detect_referral_signals(html_text, page_url)
        if finding:
            referral_findings.append(finding)

    _process(html, primary)

    # Discover contact + referral pages from the homepage's links
    contact_links = [u for (u, _s) in score_contact_links(html, primary, limit=max_contact_pages)]
    referral_links = [u for (u, _s) in score_referral_links(html, primary, limit=max_referral_pages)]

    if not contact_links and not referral_links:
        contact_links = probe_fallback_paths(primary, rl, stop)

    # De-dupe across the two sets so we don't fetch the same URL twice
    seen_urls = set(pages)
    follow_urls: List[str] = []
    for u in referral_links + contact_links:
        if u in seen_urls:
            continue
        seen_urls.add(u)
        follow_urls.append(u)

    for curl in follow_urls[: max_contact_pages + max_referral_pages]:
        if stop.is_set():
            break
        chtml, _cstatus, cfinal = fetch_html(curl, rl, stop)
        if chtml is None:
            continue
        actual = cfinal or curl
        pages.append(actual)
        _process(chtml, actual)

    result["pages"] = pages
    result["referral"] = aggregate_referral(referral_findings)
    if not result["emails"]:
        result["status"] = "no_emails"
    return result
