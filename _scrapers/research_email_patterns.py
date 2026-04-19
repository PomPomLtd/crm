#!/usr/bin/env python3
"""
Reconnaissance: catalog email-exposure patterns across a sample of real clinic sites.

Runs through a list of URLs (default: random sample from clinic_entries.json),
fetches homepage + common contact paths, and reports per-URL + aggregate stats
on which obfuscation techniques and page types are in play.

Output:
- Console summary per URL
- results/research_patterns_<ts>.json   (raw machine-readable)
- results/research_patterns_<ts>.md     (human-readable findings digest)

This is a planning tool, not the production scraper.
"""

import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CONFIG  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
ENTRIES_CACHE = os.path.join(RESULTS_DIR, "clinic_entries.json")

# ---- Pattern detectors (descriptive; we want to know what's in the HTML) ----

PATTERNS = {
    "mailto_link": re.compile(r"mailto:([^\"'?>\s]+)", re.I),
    "cf_cfemail": re.compile(r'data-cfemail=["\']([0-9a-f]+)["\']', re.I),
    "cf_email_protect": re.compile(r"/cdn-cgi/l/email-protection", re.I),
    "data_email_attr": re.compile(r'data-(?:email|mail|mailto)=["\']([^"\']+)["\']', re.I),
    "html_entity_at_dec": re.compile(r"&#0*64;"),
    "html_entity_at_hex": re.compile(r"&#x0*40;", re.I),
    "html_entity_dot_dec": re.compile(r"&#0*46;"),
    "html_entity_dot_hex": re.compile(r"&#x0*2e;", re.I),
    "wp_eeb_decode_uri": re.compile(r"decodeURIComponent\([\"']([^\"']{10,})[\"']\)"),
    "text_at_brackets": re.compile(r"[a-z0-9._\-]{2,}\s*[\[\(\{]\s*(?:at|@)\s*[\]\)\}]\s*[a-z0-9.\-]+", re.I),
    "text_dot_brackets": re.compile(r"[a-z0-9._\-]{2,}\s*[\[\(\{]\s*(?:dot|punkt|point)\s*[\]\)\}]\s*[a-z]+", re.I),
    "decryptx": re.compile(r"DeCryptX\(", re.I),
    "plain_email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "js_reversed_email": re.compile(r"\.reverse\(\)\.join\(", re.I),
    "js_email_charcode": re.compile(r"String\.fromCharCode\([^)]{20,}\)"),
    "rot13": re.compile(r"\brot13\b", re.I),
    "base64_email_candidate": re.compile(r"[A-Za-z0-9+/]{24,}={0,2}"),
    "contact_form": re.compile(r'<form\b|id=["\']contact|name=["\']contact|kontaktformular', re.I),
    "recaptcha": re.compile(r"grecaptcha|g-recaptcha|hcaptcha", re.I),
    "wordpress": re.compile(r'wp-content|wp-includes|wp-json|generator"[^>]*WordPress', re.I),
    "typo3": re.compile(r"typo3conf|typo3temp", re.I),
    "joomla": re.compile(r"option=com_|joomla", re.I),
    "wix": re.compile(r"static\.wixstatic|wix\.com/_api", re.I),
    "squarespace": re.compile(r"squarespace", re.I),
    "cookiebot_etc": re.compile(r"cookiebot|usercentrics|onetrust|iubenda", re.I),
}

CONTACT_HINTS = (
    "kontakt", "impressum", "team", "ueber-uns", "uberuns", "ueberuns",
    "datenschutz", "sprechstunde", "anfahrt", "praxis-team", "uber uns", "über",
    "contact", "mentions-legales", "mentions_legales", "equipe", "équipe",
    "a-propos", "apropos", "notre-equipe", "nous-contacter",
    "contatti", "chi-siamo", "chisiamo", "note-legali", "il-team",
    "about", "about-us", "imprint", "legal", "our-team", "staff",
)
SKIP_EXTS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
             ".doc", ".docx", ".xls", ".xlsx", ".zip", ".mp4", ".mp3", ".css", ".js")

# Fallback paths we probe if homepage has no obvious contact link
PROBE_PATHS = (
    "/kontakt", "/kontakt/", "/contact", "/contact/",
    "/impressum", "/impressum/",
    "/team", "/team/", "/unser-team", "/das-team",
    "/ueber-uns", "/über-uns", "/about",
    "/datenschutz",
    "/mentions-legales", "/mentions-legales/",
    "/contatti", "/contatti/", "/chi-siamo",
)


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(CONFIG["settings"]["headers"])
    rc = CONFIG["settings"]["retry_strategy"]
    retry = Retry(
        total=2,  # faster failure for recon
        status_forcelist=rc["status_forcelist"],
        allowed_methods=["GET", "HEAD"],
        backoff_factor=1,
    )
    ad = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    s.mount("http://", ad)
    s.mount("https://", ad)
    return s


def detect_patterns(html: str) -> Dict[str, List[str]]:
    """Run every pattern regex; return dict of name->first-3-samples."""
    found: Dict[str, List[str]] = {}
    for name, rx in PATTERNS.items():
        matches = rx.findall(html)
        if matches:
            # Normalize to strings, dedupe, keep first 3
            samples: List[str] = []
            seen = set()
            for m in matches:
                s = m if isinstance(m, str) else str(m)
                s = s.strip()
                if not s or s in seen:
                    continue
                seen.add(s)
                samples.append(s[:150])
                if len(samples) >= 3:
                    break
            if samples:
                found[name] = samples
    return found


def find_contact_links(html: str, base_url: str) -> List[Tuple[str, str, int]]:
    """Return list of (url, link_text, score) for same-domain contact-ish links."""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []
    base_host = urlparse(base_url).netloc.lower().removeprefix("www.")
    out: List[Tuple[str, str, int]] = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        p = urlparse(absolute)
        if p.scheme not in ("http", "https"):
            continue
        host = p.netloc.lower().removeprefix("www.")
        if host != base_host:
            continue
        path = p.path.lower().rstrip("/")
        if any(path.endswith(ext) for ext in SKIP_EXTS):
            continue
        text = a.get_text(" ", strip=True).lower()
        score = 0
        hits: List[str] = []
        for hint in CONTACT_HINTS:
            if hint in path:
                score += 2
                hits.append(f"path:{hint}")
            if hint in text:
                score += 1
                hits.append(f"text:{hint}")
        if score == 0:
            continue
        norm = absolute.split("#", 1)[0]
        if norm in seen:
            continue
        seen.add(norm)
        out.append((norm, text[:60], score))
    return sorted(out, key=lambda t: -t[2])


def probe_common_paths(session: requests.Session, base_url: str, logger) -> List[str]:
    """HEAD a few common contact paths; return list of 2xx URLs not already known."""
    p = urlparse(base_url)
    root = f"{p.scheme}://{p.netloc}"
    hits: List[str] = []
    for path in PROBE_PATHS:
        url = root + path
        try:
            r = session.head(url, timeout=8, allow_redirects=True)
            if 200 <= r.status_code < 300:
                hits.append(r.url)
        except Exception:
            pass
    return hits


def analyze_url(url: str, session: requests.Session, logger) -> Dict[str, Any]:
    """Fetch homepage, detect patterns, enumerate contact pages, fetch best contact page."""
    entry: Dict[str, Any] = {
        "url": url,
        "homepage": {},
        "contact_links_found": [],
        "probed_paths_ok": [],
        "best_contact_page": None,
        "errors": [],
    }
    try:
        r = session.get(url, timeout=15, allow_redirects=True)
        entry["homepage"] = {
            "final_url": r.url,
            "status": r.status_code,
            "content_type": r.headers.get("content-type", ""),
            "server": r.headers.get("server", ""),
            "size_kb": round(len(r.content) / 1024, 1),
        }
        if r.status_code >= 400:
            entry["errors"].append(f"HTTP {r.status_code}")
            return entry
        html = r.text
        entry["homepage"]["patterns"] = detect_patterns(html)
        entry["homepage"]["title"] = _soup_title(html)
        contact = find_contact_links(html, r.url)
        entry["contact_links_found"] = [
            {"url": u, "text": t, "score": s} for (u, t, s) in contact[:8]
        ]
        if not contact:
            # fall back to probing known paths
            entry["probed_paths_ok"] = probe_common_paths(session, r.url, logger)
        # Fetch best contact page
        best_url = contact[0][0] if contact else (entry["probed_paths_ok"][0] if entry["probed_paths_ok"] else None)
        if best_url:
            try:
                r2 = session.get(best_url, timeout=15, allow_redirects=True)
                entry["best_contact_page"] = {
                    "url": r2.url,
                    "requested": best_url,
                    "status": r2.status_code,
                    "patterns": detect_patterns(r2.text) if r2.status_code < 400 else {},
                    "size_kb": round(len(r2.content) / 1024, 1),
                }
            except Exception as e:
                entry["errors"].append(f"contact-fetch: {e}")
    except Exception as e:
        entry["errors"].append(str(e))
    return entry


def _soup_title(html: str) -> str:
    try:
        soup = BeautifulSoup(html, "html.parser")
        return (soup.title.string if soup.title and soup.title.string else "")[:120].strip()
    except Exception:
        return ""


# ---- CLI ----


def load_urls_from_cache(n: int, seed: int, section: Optional[str]) -> List[Dict[str, Any]]:
    if not os.path.exists(ENTRIES_CACHE):
        raise SystemExit(
            f"No cached entries at {ENTRIES_CACHE}. "
            "Run `python clinic_emails.py --refresh-input` first."
        )
    with open(ENTRIES_CACHE, "r", encoding="utf-8") as f:
        entries = json.load(f)
    if section:
        entries = [e for e in entries if e.get("section") == section]
    random.seed(seed)
    return random.sample(entries, min(n, len(entries)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="Number of URLs to sample.")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--section", help="Filter to one section handle (clinics, hospitals, …).")
    ap.add_argument("--url", action="append", help="Add specific URLs (repeatable).")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    if args.url:
        samples = [{"url": u, "section": "manual", "title": u, "id": -1} for u in args.url]
    else:
        samples = load_urls_from_cache(args.n, args.seed, args.section)
    print(f"Analyzing {len(samples)} URLs…\n", flush=True)

    session = make_session()

    results: List[Dict[str, Any]] = []
    # Parallel fetch
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(analyze_url, s["url"], session, None): s for s in samples
        }
        for fut in as_completed(futs):
            src = futs[fut]
            try:
                r = fut.result()
            except Exception as e:
                r = {"url": src["url"], "errors": [str(e)]}
            r["entry_title"] = src.get("title", "")
            r["section"] = src.get("section", "")
            results.append(r)
            # live feedback
            hp = r.get("homepage") or {}
            patterns = list((hp.get("patterns") or {}).keys())
            contact_n = len(r.get("contact_links_found") or [])
            status = hp.get("status", "?")
            errs = "; ".join(r.get("errors") or [])
            tag = f"[{r.get('section', '-'):14s}]"
            summary = f"  home patterns={patterns[:6]}{'…' if len(patterns) > 6 else ''}  contacts={contact_n}"
            print(f"{tag} {src['url']}  status={status}{' ERR='+errs if errs else ''}")
            print(summary, flush=True)

    # Aggregate
    pattern_counts: Counter = Counter()
    pattern_on_homepage: Counter = Counter()
    pattern_on_contact: Counter = Counter()
    sections_n: Counter = Counter()
    status_n: Counter = Counter()
    server_n: Counter = Counter()
    contact_found = 0
    homepage_emails = 0
    contact_emails = 0
    sites_with_any_email = 0

    for r in results:
        sections_n[r.get("section", "-")] += 1
        hp = r.get("homepage") or {}
        status_n[hp.get("status", "error")] += 1
        if hp.get("server"):
            server_n[hp["server"][:40]] += 1
        hp_patterns = (hp.get("patterns") or {})
        bc = r.get("best_contact_page") or {}
        bc_patterns = (bc.get("patterns") or {})
        # "plain_email" found
        if "plain_email" in hp_patterns:
            homepage_emails += 1
        if "plain_email" in bc_patterns:
            contact_emails += 1
        if "plain_email" in hp_patterns or "plain_email" in bc_patterns:
            sites_with_any_email += 1
        if r.get("contact_links_found"):
            contact_found += 1
        for name in hp_patterns:
            pattern_counts[name] += 1
            pattern_on_homepage[name] += 1
        for name in bc_patterns:
            pattern_counts[name] += 1
            pattern_on_contact[name] += 1

    # Dump raw + markdown digest
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    raw_path = os.path.join(RESULTS_DIR, f"research_patterns_{ts}.json")
    md_path = os.path.join(RESULTS_DIR, f"research_patterns_{ts}.md")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({"generated": ts, "n": len(results), "results": results}, f, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Email Pattern Reconnaissance — {ts}\n\n")
        f.write(f"Sampled **{len(results)}** clinic sites.\n\n")
        f.write("## Coverage\n\n")
        f.write(f"- Sites with any plaintext email (home or contact page): **{sites_with_any_email}/{len(results)}**  ({100 * sites_with_any_email / len(results):.1f}%)\n")
        f.write(f"- Plaintext email visible on homepage: **{homepage_emails}/{len(results)}**\n")
        f.write(f"- Plaintext email on contact page: **{contact_emails}/{len(results)}**\n")
        f.write(f"- Contact link discoverable from homepage: **{contact_found}/{len(results)}**\n\n")
        f.write("## Patterns detected (sites where pattern appears on any page)\n\n")
        f.write("| Pattern | Count | Homepage | Contact page |\n|---|---|---|---|\n")
        for name, cnt in pattern_counts.most_common():
            f.write(f"| `{name}` | {cnt} | {pattern_on_homepage[name]} | {pattern_on_contact[name]} |\n")
        f.write("\n## Status codes\n\n")
        for k, v in status_n.most_common():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Top servers\n\n")
        for k, v in server_n.most_common(10):
            f.write(f"- {k}: {v}\n")
        f.write("\n## Per-URL details\n\n")
        for r in results:
            hp = r.get("homepage") or {}
            bc = r.get("best_contact_page") or {}
            title = r.get("entry_title", "")
            f.write(f"### {r['url']}\n")
            f.write(f"- Section: {r.get('section', '-')} · Title: {title[:80]}\n")
            if r.get("errors"):
                f.write(f"- **Errors**: {r['errors']}\n")
            f.write(f"- Homepage status: {hp.get('status', '?')} · server: `{hp.get('server', '')}`\n")
            hp_pat = hp.get("patterns") or {}
            if hp_pat:
                f.write(f"- Homepage patterns: {sorted(hp_pat.keys())}\n")
                for name, samples in list(hp_pat.items())[:10]:
                    for s in samples[:2]:
                        f.write(f"    - `{name}`: `{s[:120]}`\n")
            contacts = r.get("contact_links_found") or []
            if contacts:
                f.write(f"- Contact links: {[(c['url'], c['score']) for c in contacts[:5]]}\n")
            probed = r.get("probed_paths_ok") or []
            if probed:
                f.write(f"- Probed paths OK: {probed[:5]}\n")
            if bc:
                f.write(f"- Best contact page: {bc.get('url')} (status {bc.get('status')})\n")
                bc_pat = bc.get("patterns") or {}
                if bc_pat:
                    f.write(f"  - patterns: {sorted(bc_pat.keys())}\n")
                    for name, samples in list(bc_pat.items())[:10]:
                        for s in samples[:2]:
                            f.write(f"      - `{name}`: `{s[:120]}`\n")
            f.write("\n")

    print(f"\n--- DONE ---")
    print(f"Raw:       {raw_path}")
    print(f"Markdown:  {md_path}")
    print(f"\nQuick stats:")
    print(f"  sites with any plaintext email: {sites_with_any_email}/{len(results)} ({100*sites_with_any_email/len(results):.1f}%)")
    print(f"  contact link found (homepage):  {contact_found}/{len(results)} ({100*contact_found/len(results):.1f}%)")
    print(f"  pattern frequencies: {dict(pattern_counts.most_common(10))}")


if __name__ == "__main__":
    main()
