"""Referral-section detection.

Inspects clinic websites for "Zuweiser" / "Médecins référents" /
"Medici invianti" / "Referring Physicians" sections and characterises HOW
the clinic accepts referrals: web form, downloadable form (PDF/DOC),
dedicated email, fax number, or just descriptive text.

Public API:

    score_referral_links(html, base_url, limit=3) -> List[(url, score)]
        Like crawler.score_contact_links but uses REFERRAL_HINT_WEIGHTS.
        Used to extend the per-entry crawl with referral-page candidates.

    detect_referral_signals(html, page_url) -> dict
        Inspect one fetched page; return findings (form, docs, emails, faxes,
        evidence keywords). Returns {} if nothing referral-like is on the page.

    aggregate(per_page_findings: List[dict]) -> dict
        Merge findings across multiple pages of one entry into a single
        per-entry summary (the shape stored in the checkpoint).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .extractors import extract_emails
from .patterns import (
    DOC_EXTENSIONS,
    REFERRAL_DOC_HINTS,
    REFERRAL_EMAIL_PREFIXES,
    REFERRAL_HINT_WEIGHTS,
    REFERRAL_TEXT_HINTS,
    SKIP_PATH_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# Link scoring (find dedicated referral pages from a homepage)
# ---------------------------------------------------------------------------


def _host_bare(host: str) -> str:
    return host.lower().lstrip(".").removeprefix("www.")


def score_referral_links(
    html: str, base_url: str, limit: int = 3
) -> List[Tuple[str, int]]:
    """Score same-origin <a> links by referral hints. Return top N."""
    try:
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
        for hint, weight in REFERRAL_HINT_WEIGHTS.items():
            if hint in path:
                score += weight
            if hint in link_text:
                score += max(1, weight - 1)
        if score <= 0:
            continue

        normalized = absolute.split("#", 1)[0].rstrip("/")
        if normalized == base_clean:
            continue
        if normalized not in candidates or score > candidates[normalized]:
            candidates[normalized] = score

    return sorted(candidates.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]


# ---------------------------------------------------------------------------
# Per-page detection
# ---------------------------------------------------------------------------

# A page-level fax search; conservative — needs an explicit "Fax" / "Telefax"
# label nearby so we don't capture random phone numbers.
_FAX_RE = re.compile(
    r"(?:fax|telefax|faxnummer|fax\.?:?)\s*[:.]?\s*"
    r"([+0-9][\d().\-/ ]{6,20}\d)",
    re.IGNORECASE,
)


def _normalize_fax(raw: str) -> str:
    s = re.sub(r"\s+", " ", raw.strip())
    digits = re.sub(r"[^0-9+]", "", s)
    if 8 <= len(digits) <= 16:
        return s
    return ""


def _form_looks_like_referral(form_tag) -> bool:
    """Decide if a <form> tag is plausibly a referral request form."""
    text = form_tag.get_text(" ", strip=True).lower()
    if any(hint in text for hint in REFERRAL_TEXT_HINTS):
        return True
    # Field-name heuristics
    for inp in form_tag.find_all(["input", "textarea", "select"]):
        name = (inp.get("name") or "").lower()
        ph = (inp.get("placeholder") or "").lower()
        for needle in (
            "patient", "diagnos", "zuweis", "uberweis", "überweis",
            "einweis", "anmeld", "referent", "referring", "rinvio",
        ):
            if needle in name or needle in ph:
                return True
    return False


def detect_referral_signals(html: str, page_url: str) -> Dict[str, Any]:
    """Inspect one page; return what we found about referrals here.

    Returns an empty dict (`{}`) if no referral signal is present on the page.
    Otherwise returns a dict with the keys:
        page_url       : the page URL
        text_signals   : list of REFERRAL_TEXT_HINTS that matched
        has_form       : bool
        documents      : list of {"url", "anchor", "type"}
        emails         : list of referral-prefixed emails
        faxes          : list of fax number strings
        evidence       : ordered set of method keywords found on this page
    """
    if not html:
        return {}
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return {}

    text_lower = soup.get_text(" ", strip=True).lower()
    text_signals = [h for h in REFERRAL_TEXT_HINTS if h in text_lower]

    # Forms — only count those plausibly referral-related on a referral-ish page
    has_form = False
    for form in soup.find_all("form"):
        if _form_looks_like_referral(form):
            has_form = True
            break
    # If no forms self-identify as referral but the page itself is clearly
    # a referral page (text signals), count the first form (if any).
    if not has_form and text_signals:
        if soup.find("form"):
            has_form = True

    # Downloadable referral forms (PDF/DOC/DOCX/RTF/ODT) on this page.
    #
    # Strict-by-default to avoid scraping random Anfahrtspläne / Datenschutz
    # PDFs from a hospital's general info pages: only accept docs whose href
    # OR anchor text matches REFERRAL_DOC_HINTS. We relax this rule ONLY when
    # the page URL itself contains a strong referral path hint — that means
    # we're on a dedicated referral page where every linked document is
    # plausibly relevant.
    page_path_lower = urlparse(page_url).path.lower()
    page_url_signals_referral = any(
        hint in page_path_lower for hint in (
            "zuweis", "uberweis", "überweis", "einweis",
            "referral", "referent", "référent",
            "medici-invianti", "rinvio", "refer-a-patient",
            "fuer-zuweis", "für-zuweis", "fuer-aerzte", "für-aerzte",
        )
    )

    documents: List[Dict[str, str]] = []
    seen_doc_urls: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        href_lower = href.lower()
        ext = next((e for e in DOC_EXTENSIONS if href_lower.split("?")[0].endswith(e)), None)
        if not ext:
            continue
        anchor = a.get_text(" ", strip=True)
        combined = (href_lower + " " + anchor.lower())
        keyword_hit = any(hint in combined for hint in REFERRAL_DOC_HINTS)
        if not keyword_hit and not page_url_signals_referral:
            continue
        absolute = urljoin(page_url, href).split("#", 1)[0]
        if absolute in seen_doc_urls:
            continue
        seen_doc_urls.add(absolute)
        documents.append(
            {
                "url": absolute,
                "anchor": anchor[:100],
                "type": ext.lstrip("."),
            }
        )
        if len(documents) >= 10:
            break

    # Emails on this page that look referral-specific
    emails: List[str] = []
    for email in extract_emails(html):
        prefix = email.split("@", 1)[0].lower()
        if any(prefix.startswith(p) for p in REFERRAL_EMAIL_PREFIXES):
            emails.append(email)
    emails = sorted(set(emails))

    # Fax numbers
    faxes: List[str] = []
    seen_fax: Set[str] = set()
    for m in _FAX_RE.finditer(text_lower):
        norm = _normalize_fax(m.group(1))
        if not norm or norm in seen_fax:
            continue
        seen_fax.add(norm)
        faxes.append(norm)
        if len(faxes) >= 5:
            break

    if not (text_signals or has_form or documents or emails):
        return {}

    evidence: List[str] = []
    if has_form:
        evidence.append("form")
    if any(d["type"] == "pdf" for d in documents):
        evidence.append("pdf")
    if any(d["type"] in ("doc", "docx", "rtf", "odt") for d in documents):
        evidence.append("doc")
    if emails:
        evidence.append("email")
    if faxes:
        evidence.append("fax")
    if not evidence and text_signals:
        evidence.append("page-only")

    return {
        "page_url": page_url,
        "text_signals": text_signals[:5],
        "has_form": has_form,
        "documents": documents,
        "emails": emails,
        "faxes": faxes,
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# Aggregation across multiple pages of one entry
# ---------------------------------------------------------------------------


def aggregate(per_page: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge per-page findings into a single per-entry summary."""
    page_urls: List[str] = []
    has_form = False
    documents: List[Dict[str, str]] = []
    seen_doc_urls: Set[str] = set()
    emails: Set[str] = set()
    faxes: Set[str] = set()
    text_signals: Set[str] = set()
    evidence: Set[str] = set()

    for page in per_page:
        if not page:
            continue
        url = page.get("page_url")
        if url and url not in page_urls:
            page_urls.append(url)
        if page.get("has_form"):
            has_form = True
        for d in page.get("documents") or []:
            if d["url"] not in seen_doc_urls:
                seen_doc_urls.add(d["url"])
                documents.append(d)
        for e in page.get("emails") or []:
            emails.add(e)
        for f in page.get("faxes") or []:
            faxes.add(f)
        for s in page.get("text_signals") or []:
            text_signals.add(s)
        for ev in page.get("evidence") or []:
            evidence.add(ev)

    if not page_urls and not documents and not emails and not faxes:
        return {"found": False}

    # Re-derive ordered evidence (form > pdf > doc > email > fax > page-only)
    method_order = ("form", "pdf", "doc", "email", "fax", "page-only")
    methods = [m for m in method_order if m in evidence]

    return {
        "found": True,
        "pages": page_urls,
        "methods": methods,
        "has_form": has_form,
        "documents": documents,
        "emails": sorted(emails),
        "faxes": sorted(faxes),
        "text_signals": sorted(text_signals)[:8],
    }
