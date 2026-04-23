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
    AGENCY_DOMAIN_PATTERNS,
    DECRYPTX_KNOWN,
    GENERAL_PREFIXES,
    NOISE_EMAIL_DOMAIN_PATTERNS,
    NOISE_EMAIL_DOMAIN_SUFFIXES,
    NOISE_EMAIL_DOMAINS,
    NOISE_USERNAME_PATTERNS,
    PRIORITY_DOMAIN_SUFFIXES,
    PRIORITY_PREFIXES_LOW,
    PRIORITY_PREFIXES_MID,
    PRIORITY_PREFIXES_TOP,
    THIRD_PARTY_SOURCE_HINTS,
)

# Compiled regex objects for the new pattern lists.
_NOISE_DOMAIN_RES = tuple(re.compile(p) for p in NOISE_EMAIL_DOMAIN_PATTERNS)
_NOISE_USERNAME_RES = tuple(re.compile(p) for p in NOISE_USERNAME_PATTERNS)
_AGENCY_DOMAIN_RES = tuple(re.compile(p) for p in AGENCY_DOMAIN_PATTERNS)


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
    # New noise filters (2026-04-23 audit additions)
    if any(r.search(domain) for r in _NOISE_DOMAIN_RES):
        return ""
    if any(r.match(username) for r in _NOISE_USERNAME_RES):
        return ""
    if any(r.search(domain) for r in _AGENCY_DOMAIN_RES):
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
# ROT13 fallback (decoder #10)
# ---------------------------------------------------------------------------

# ROT13-rotated TLDs for common real TLDs: ch → pu, com → pbz, de → qr, etc.
# If we see one of these "impossible" TLDs on a candidate email, the whole
# string is almost certainly ROT13-obfuscated (a known anti-scraping trick —
# the clienia.ch clinic network uses it).
_ROT13_TLDS = {"pu", "pbz", "qr", "se", "ng", "yv", "rh", "vg"}


def _try_rot13(candidate: str) -> Optional[str]:
    """If candidate's TLD is a ROT13-rotated common TLD, rotate the whole
    string back and return the decoded email. Otherwise None."""
    if "@" not in candidate:
        return None
    domain = candidate.rsplit("@", 1)[1]
    tld = domain.rsplit(".", 1)[-1].lower()
    if tld not in _ROT13_TLDS:
        return None
    # ROT13 the entire string
    decoded = candidate.translate(str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM",
    ))
    # Validate the decoded form looks like a real email
    cleaned = clean_email(decoded)
    return cleaned or None


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

    # 9. ROT13 fallback: sweep raw HTML for email-shaped strings whose TLD
    # looks ROT13-rotated (.pu/.pbz/.qr = .ch/.com/.de). Recovers addresses
    # on sites that rot13 their mailtos as an anti-scraping trick (seen on
    # clienia.ch network). clean_email first so we don't re-rot a real email.
    _ROT13_EMAIL_RE = re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\."
        + "(?:" + "|".join(sorted(_ROT13_TLDS)) + r")\b",
        re.IGNORECASE,
    )
    for m in _ROT13_EMAIL_RE.finditer(html):
        decoded = _try_rot13(m.group())
        if decoded:
            found.add(decoded)

    return found


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def _prefix_matches(prefix: str, candidates: tuple) -> bool:
    """True if `prefix` starts with any tuple entry followed by an optional
    delimiter. Compound-safe: matches both bare `sekretariat@` AND compounds
    like `sekretariatsdienste@`, `secretariatdirection@`, `zuweiserbrief@`.

    Exact match and separator-delimited forms still match too (`info.xyz@`,
    `kontakt-praxis@`)."""
    for p in candidates:
        if prefix == p or prefix.startswith(p):
            return True
        for sep in (".", "-", "_"):
            if prefix.endswith(sep + p):
                return True
    return False


def _domain_of(email: str) -> str:
    return email.rsplit("@", 1)[1].lower() if "@" in email else ""


def _registrable(domain: str) -> str:
    """Rough registrable-domain extract: take the last two labels. Good enough
    for Swiss practices where we just need to compare 'clinic.ch' across a
    homepage hit vs. an impressum-only third-party hit."""
    parts = domain.lower().strip(".").split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain


def _is_third_party_legal_only(
    email: str, entry_domain: Optional[str], sources: Optional[Dict[str, str]],
) -> bool:
    """Returns True if this email is clearly a third-party legal/DPO address
    that leaked in from an impressum/datenschutz page. Catches entries like
    `hirslanden@activemind.legal`, `dpo.ch@affidea.ch`, `webmaster@*`.

    Rule: domain differs from entry's practice domain AND every recorded
    source URL for this email is a legal/privacy page — UNLESS the email
    is on a PRIORITY_DOMAIN_SUFFIX (hin.ch). HIN addresses are owned by
    the practice by definition (Swiss secure-email authentication), so
    even if one appears only in the impressum, it's still the practice's
    own reachable inbox."""
    if not entry_domain or not sources:
        return False
    domain = _domain_of(email)
    # Never drop HIN addresses or other owner-operated priority domains.
    if any(domain.endswith(sfx) for sfx in PRIORITY_DOMAIN_SUFFIXES):
        return False
    email_lower = email.lower()
    src_url = sources.get(email_lower) or sources.get(email) or ""
    if not src_url:
        return False
    src_lower = src_url.lower()
    # Is every source page a legal/privacy page?
    if not any(hint in src_lower for hint in THIRD_PARTY_SOURCE_HINTS):
        return False
    # Is the email's domain a different registrable domain than the practice?
    if _registrable(domain) == _registrable(entry_domain):
        return False
    return True


def classify(
    emails: Set[str],
    *,
    entry_domain: Optional[str] = None,
    sources: Optional[Dict[str, str]] = None,
) -> Dict[str, List[str]]:
    """Bucket emails into priority / general / other.

    Priority bucket is sorted by tier (TOP → MID → LOW) then alphabetically,
    so the first element is always the best contact (prefers `sekretariat@`
    over `info@` when both exist at the same practice).

    When `entry_domain` and `sources` are supplied, addresses whose domain
    differs from `entry_domain` AND whose recorded source is ONLY a legal /
    privacy page get dropped entirely (catches DPO-as-a-service leaks and
    web-agency credits in impressum pages).

    The keyword args are optional so old call sites keep working."""
    # Priority tier ranking (lower = better for sort stability)
    TIER_HIN = 0       # HIN-network addresses — person-operated by design
    TIER_TOP = 1       # sekretariat, empfang, zuweiser, triage, mpa, etc.
    TIER_MID = 2       # info, kontakt, contact, praxis, klinik
    TIER_LOW = 3       # office, buero, verwaltung, administration, leitung
    NOT_PRIORITY = 99

    priority_tiered: List[tuple] = []
    general: List[str] = []
    other: List[str] = []

    for email in emails:
        # Third-party legal-only filter (drops e.g. `webmaster@agency.ch`
        # found only on /impressum).
        if _is_third_party_legal_only(email, entry_domain, sources):
            continue

        prefix, _, domain = email.partition("@")
        prefix = prefix.lower()

        # HIN network — highest priority, any local-part.
        if any(domain.endswith(sfx) for sfx in PRIORITY_DOMAIN_SUFFIXES):
            priority_tiered.append((TIER_HIN, email))
            continue

        # Tier matching (compound-safe startswith)
        if _prefix_matches(prefix, PRIORITY_PREFIXES_TOP):
            priority_tiered.append((TIER_TOP, email))
            continue
        if _prefix_matches(prefix, PRIORITY_PREFIXES_MID):
            priority_tiered.append((TIER_MID, email))
            continue
        if _prefix_matches(prefix, PRIORITY_PREFIXES_LOW):
            priority_tiered.append((TIER_LOW, email))
            continue

        # General (doctor prefixes)
        if any(
            prefix == p or prefix.startswith(p + ".") or prefix.startswith(p + "-")
            for p in GENERAL_PREFIXES
        ):
            general.append(email)
        else:
            other.append(email)

    # Sort priority by (tier, alpha) — first element is always best contact.
    priority = [e for _, e in sorted(priority_tiered, key=lambda t: (t[0], t[1]))]
    general.sort()
    other.sort()
    return {"priority": priority, "general": general, "other": other}
