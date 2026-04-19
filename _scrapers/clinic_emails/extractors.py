"""Email extraction — decoders, normalizers, classifiers.

All logic here is pure-Python and unit-testable. No I/O.

Public API:
  - extract_emails(html: str) -> Set[str]   : run every decoder, return cleaned set
  - clean_email(raw: str) -> str            : normalize + validate one candidate
  - classify(emails: Set[str]) -> dict      : bucket into priority/general/other

Decoders covered (based on real-world reconnaissance of 80 Swiss clinic sites):
  1. mailto: links (including URL-encoded and HTML-entity-encoded hrefs)
  2. Plain-text emails in rendered text
  3. HTML entity encoding (&#64;, &#x40;, &commat;, decimal, hex)
  4. [at]/(at)/{at} + [dot]/(dot)/{dot} text obfuscation
  5. Cloudflare data-cfemail XOR encoding
  6. data-email / data-mail / data-mailto DOM attributes
  7. WordPress email-encoder-bundle (decodeURIComponent blobs)
  8. DeCryptX: known-ciphertext lookup only (cannot decrypt unknowns)
  9. <script>-embedded literal emails

Noise filters (also informed by recon) reject Wix Sentry IDs, image-filename
look-alikes (e.g. "hero@2x.webp"), and placeholder domains.
"""

from __future__ import annotations

import re
import urllib.parse
from html import unescape
from typing import Dict, List, Optional, Set

from bs4 import BeautifulSoup

from .patterns import (
    DECRYPTX_KNOWN,
    GENERAL_PREFIXES,
    NOISE_EMAIL_DOMAIN_SUFFIXES,
    NOISE_EMAIL_DOMAINS,
    PRIORITY_DOMAIN_SUFFIXES,
    PRIORITY_PREFIXES,
)


# Wider than RFC-strict; we let clean_email() tighten.
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def clean_email(raw: str) -> str:
    """Normalize + validate one email candidate. Returns '' if invalid/noise."""
    if not raw:
        return ""

    # Unescape HTML entities first (e.g. "info&#64;example.ch" -> "info@example.ch")
    email = unescape(raw).strip()
    # URL-decode for mailto hrefs that contain %40 etc.
    try:
        email = urllib.parse.unquote(email)
    except Exception:
        pass
    email = email.strip().strip("\\").strip()
    email = email.lower()

    # Strip leading noise (whitespace, quote marks, zero-width chars, %20 artifacts)
    email = re.sub(r"^[^a-z0-9]+", "", email)
    email = re.sub(r"[^a-z0-9._%+\-]+$", "", email)

    # Some mailto links arrive with leading digits glued on (e.g. "05info@")
    # or with a URL-decoded leading space that became prefixed "20"
    email = re.sub(r"^(?:20|\d+)(?=[a-z])", "", email)

    if "@" not in email:
        return ""
    username, _, domain = email.partition("@")
    if not username or not domain:
        return ""

    # Defuse common concatenations ("...chwww.example.ch" -> "...ch")
    domain = re.sub(
        r"(\.ch|\.com|\.org|\.net|\.de|\.at|\.fr|\.it|\.li|\.eu)"
        r"(?:www\.|https?://|[a-z]{3,}\.)",
        r"\1",
        domain,
    )
    domain = re.sub(
        r"(\.ch|\.com|\.org|\.net|\.de|\.at|\.fr|\.it|\.li|\.eu).*",
        r"\1",
        domain,
    )
    email = f"{username}@{domain}"

    # Format validation
    if not re.match(
        r"^[a-z0-9][a-z0-9._%+\-]*@[a-z0-9][a-z0-9.\-]+\.[a-z]{2,}$", email
    ):
        return ""
    if len(email) > 100 or len(username) > 40:
        return ""

    # Noise filters
    if domain in NOISE_EMAIL_DOMAINS:
        return ""
    if any(domain.endswith(sfx) for sfx in NOISE_EMAIL_DOMAIN_SUFFIXES):
        return ""
    # Image-filename patterns: "hero@2x.webp", "pic@560w.jpg", "foo@1120w2x.jpg"
    if re.match(r"^\d+x?w?$|^\d+w\d?x?$", username[-6:]):
        # only reject if domain suffix was image-like (already caught above),
        # this is a second-chance guard
        pass
    # Reject "foo@bar" with no multi-level TLD or clearly bogus
    if ".." in domain:
        return ""
    if any(bad in domain for bad in (".shnur", ".chunser")):
        return ""
    # Mixed-case username heuristic (rare for real addresses, common for
    # concatenation artifacts in raw HTML dumps after case-preserving extraction)
    if re.search(r"[a-z]{6,}[A-Z]", raw) and "@" not in raw[:5]:
        # be conservative — only applies when we see a clear CamelCase lump
        pass

    return email


# ---------------------------------------------------------------------------
# Cloudflare email protection (data-cfemail hex XOR)
# ---------------------------------------------------------------------------


def decode_cloudflare_cfemail(encoded: str) -> Optional[str]:
    """XOR-decode a data-cfemail attribute. Returns email or None."""
    if not encoded or len(encoded) < 4 or len(encoded) % 2 != 0:
        return None
    try:
        key = int(encoded[:2], 16)
        chars = [int(encoded[i : i + 2], 16) ^ key for i in range(2, len(encoded), 2)]
        return "".join(chr(c) for c in chars)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Text de-obfuscation
# ---------------------------------------------------------------------------


_AT_BRACKET = re.compile(
    r"\s*[\[\(\{]\s*(?:at|@)\s*[\]\)\}]\s*", re.IGNORECASE
)
_DOT_BRACKET = re.compile(
    r"\s*[\[\(\{]\s*(?:dot|punkt|point)\s*[\]\)\}]\s*", re.IGNORECASE
)


def deobfuscate(text: str) -> str:
    """Replace HTML entities + [at]/[dot] spellings with real @ and . chars.

    Applied before regex sweeps so obfuscated forms match the plain email regex.
    """
    if not text:
        return ""
    # Expand HTML entities (&#64; &#x40; &commat; &period; …)
    text = unescape(text)
    # Bracketed [at]/(at)/{at} -> @
    text = _AT_BRACKET.sub("@", text)
    # Bracketed [dot]/(dot)/{dot}/[punkt]/[point] -> .
    text = _DOT_BRACKET.sub(".", text)
    return text


# ---------------------------------------------------------------------------
# Top-level extractor
# ---------------------------------------------------------------------------


def extract_emails(html: str) -> Set[str]:
    """Run every decoder on a page's HTML. Returns a set of cleaned emails."""
    found: Set[str] = set()
    if not html:
        return found

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        soup = None

    if soup is not None:
        # 1. mailto: links (unescape entities + URL-decode inside clean_email)
        for a in soup.find_all("a", href=True):
            href = a.get("href", "") or ""
            if href.strip().lower().startswith("mailto:"):
                candidate = href.strip()[7:].split("?", 1)[0]
                cleaned = clean_email(candidate)
                if cleaned:
                    found.add(cleaned)

        # 2. Cloudflare [data-cfemail]
        for el in soup.select("[data-cfemail]"):
            decoded = decode_cloudflare_cfemail(el.get("data-cfemail", ""))
            if decoded:
                cleaned = clean_email(decoded)
                if cleaned:
                    found.add(cleaned)

        # 3. data-email / data-mail / data-mailto
        for attr in ("data-email", "data-mail", "data-mailto"):
            for el in soup.select(f"[{attr}]"):
                cleaned = clean_email(el.get(attr, ""))
                if cleaned:
                    found.add(cleaned)

        # 4. <script> string literals
        for script in soup.find_all("script"):
            if script.string:
                for m in EMAIL_REGEX.finditer(script.string):
                    cleaned = clean_email(m.group())
                    if cleaned:
                        found.add(cleaned)

        # 5. visible text (after deobfuscation)
        text = soup.get_text(separator=" ")
        for m in EMAIL_REGEX.finditer(deobfuscate(text)):
            cleaned = clean_email(m.group())
            if cleaned:
                found.add(cleaned)

    # 6. raw-HTML sweep (after entity expansion + at/dot replacement) —
    # catches obfuscated forms in attributes that BeautifulSoup's text
    # extraction would skip.
    for m in EMAIL_REGEX.finditer(deobfuscate(html)):
        cleaned = clean_email(m.group())
        if cleaned:
            found.add(cleaned)

    # 7. WordPress email-encoder-bundle: decodeURIComponent("...") blobs
    for m in re.finditer(
        r"decodeURIComponent\([\"']([^\"']{8,})[\"']\)", html
    ):
        blob = m.group(1)
        try:
            decoded = urllib.parse.unquote(blob)
        except Exception:
            continue
        cleaned = clean_email(decoded)
        if cleaned:
            found.add(cleaned)

    # 8. DeCryptX: known ciphertext lookup (unknowns are not decrypt-able)
    for m in re.finditer(r"DeCryptX\([\"']([^\"']+)[\"']\)", html):
        mapped = DECRYPTX_KNOWN.get(m.group(1))
        if mapped:
            cleaned = clean_email(mapped)
            if cleaned:
                found.add(cleaned)

    return found


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify(emails: Set[str]) -> Dict[str, List[str]]:
    """Bucket emails into priority / general / other (sorted, deduped)."""
    priority: List[str] = []
    general: List[str] = []
    other: List[str] = []

    for email in sorted(emails):
        prefix, _, domain = email.partition("@")
        prefix = prefix.lower()

        # HIN network — specifically the Swiss healthcare provider email system.
        # Every hin.ch address belongs to a registered practitioner or practice.
        if any(domain.endswith(sfx) for sfx in PRIORITY_DOMAIN_SUFFIXES):
            priority.append(email)
            continue

        # prefix-based priority: exact match OR delimiter-separated variant
        is_priority = False
        for p in PRIORITY_PREFIXES:
            if prefix == p:
                is_priority = True
                break
            for sep in (".", "-", "_"):
                if prefix.startswith(p + sep) or prefix.endswith(sep + p):
                    is_priority = True
                    break
            if is_priority:
                break

        if is_priority:
            priority.append(email)
            continue

        if any(
            prefix == p or prefix.startswith(p + ".") or prefix.startswith(p + "-")
            for p in GENERAL_PREFIXES
        ):
            general.append(email)
        else:
            other.append(email)

    return {"priority": priority, "general": general, "other": other}
