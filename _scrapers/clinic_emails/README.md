# clinic_emails

Finds email addresses AND characterizes referral sections on Swiss clinic
websites, reading targets directly from the Craft CMS database.

Entry point: `../find_clinic_emails.py` (wraps `clinic_emails.cli:main`).

## Quick start

```bash
cd _scrapers && source venv/bin/activate

# One-time: dump target entries from the Craft DB (~18k rows with practice URL)
python find_clinic_emails.py --refresh-input

# Diagnose one URL (prints extracted emails + referral findings)
python find_clinic_emails.py --test https://www.lindenhofgruppe.ch/

# Random sample (for benchmarking before a long run)
python find_clinic_emails.py --sample 50

# Single section only (2=medicalCenters 3=clinics 4=groupPractices 5=medClinics 6=hospitals)
python find_clinic_emails.py --section 6

# Full run (resumable; Ctrl-C anytime)
python find_clinic_emails.py --workers 10

# Rebuild CSV + summary from the existing checkpoint (applies the CURRENT
# noise-domain filter retroactively — useful after tightening patterns.py)
python find_clinic_emails.py --report

# Unit tests
python -m pytest ../tests/ -v     # 51 tests covering every decoder + referral
```

## What it does

For each target clinic entry in the DB (sections 2–6 only; section 1 = solo
doctors is excluded):

1. Fetches the clinic's homepage.
2. Scores internal links for contact-page hints (DE/FR/IT/EN) and follows
   the top 4. Also scores referral-page hints (DE/FR/IT/EN) and follows the
   top 2. De-duped against contact pages.
3. If the entry URL 404s, retries the domain root.
4. If no contact links are discoverable, probes conventional paths
   (`/kontakt`, `/contact`, `/impressum`, `/team`, …).
5. Runs email extraction AND referral detection on every fetched page.
6. Aggregates, classifies, writes to JSONL checkpoint.

## Input / output files

Everything lives under `_scrapers/results/`:

| File | Role | Gitignored |
|---|---|---|
| `clinic_entries.json` | DB-dump cache; list of `{id, section, title, url}` | ✅ |
| `clinic_emails_checkpoint.jsonl` | Append-only state — one JSON line per processed entry | ✅ |
| `clinic_emails_<ts>.csv` | Timestamped final output, rebuilt on `--report` | ✅ |
| `clinic_emails_<ts>_summary.txt` | Hit rates, per-section stats, top email domains, referral breakdown | ✅ |
| `research_patterns_*.md` | Reconnaissance reports from `research_email_patterns.py` | kept |

### CSV schema

| Column | Content |
|---|---|
| `entry_id`, `section`, `title`, `url` | from Craft DB |
| `priority_emails` | `info@`, `kontakt@`, `sekretariat@`, `*@hin.ch` …<br>(semicolon-separated) |
| `general_emails` | doctor-prefixed addresses (`dr.*`, `doc@`, …) |
| `other_emails` | everything else |
| `all_emails` | priority + general + other in order |
| `sources_json` | JSON map `{email → first page URL that yielded it}` |
| `pages_crawled` | semicolon-separated list of URLs actually fetched |
| `status` | `success` / `success_via_root` / `no_emails` / `fetch_failed` / `error` |
| `has_referral` | `yes` / `no` |
| `referral_methods` | subset of `form`, `pdf`, `doc`, `email`, `fax`, `page-only` |
| `referral_pages` | pages that matched referral signals |
| `referral_emails` | referral-prefixed addresses (`zuweis@`, `ueberweis@`, …) |
| `referral_faxes` | fax numbers found under a "Fax:" label |
| `referral_documents_json` | JSON list of `{url, anchor, type}` for referral form PDFs/DOCs |
| `error` | exception message if worker crashed |
| `ts` | ISO-8601 UTC timestamp |

## Architecture

All pure-Python, no I/O in the extractor layer — the decoders are unit-testable
against raw HTML strings.

```
find_clinic_emails.py          # entry point shim
  → clinic_emails.cli.main()   # argparse, thread pool, checkpoint, signals
      → entries.load_entries   # ddev mysql dump + cached JSON
      → crawler.crawl_entry    # homepage + contact + referral pages
          → extractors         # 8 email decoders (below)
          → referral           # page / form / doc / email / fax detection
      → checkpoint.Checkpoint  # append-only JSONL, crash-safe
      → report.write_report    # CSV + summary, applies current noise filter
```

### Email decoders (`extractors.py`)

1. `mailto:` links — with HTML-entity + URL-decoding
2. Plain-text regex sweep on rendered text AND raw HTML
3. HTML entities — decimal (`&#64;`), hex (`&#x40;`), named (`&commat;`)
4. `[at]` / `(at)` / `{at}` + `[dot]` / `(dot)` / `[point]` / `[punkt]` obfuscation
5. Cloudflare `data-cfemail` XOR (very common on cloudflared hospital sites)
6. WordPress email-encoder-bundle: `decodeURIComponent("info%40hin.ch")`
7. `data-email` / `data-mail` / `data-mailto` DOM attributes
8. DeCryptX: known-ciphertext lookup (unknowns are cryptographically un-decodable)
9. `<script>` body email regex sweep

`clean_email()` validates every candidate, strips leading `%20`/`20`/digits,
defuses concatenated-domain artifacts (`.chwww.example.ch` → `.ch`), and
rejects image-filename look-alikes (`hero@2x.webp`) + Wix Sentry IDs.

### Referral detection (`referral.py`)

`score_referral_links` mirrors contact-link scoring but with
`REFERRAL_HINT_WEIGHTS` — catches `/zuweiser`, `/ueberweisung`, `/medecins-referents`,
`/medici-invianti`, `/refer-a-patient`, etc.

`detect_referral_signals` inspects one page and returns:
- `has_form` — via referral-text proximity or referral-flavored field names
  (`name="patient"`, `name="diagnose"`, `name="zuweisend"`, …)
- `documents` — PDF/DOC/DOCX/RTF/ODT links. **Strict by default**: only those
  whose href or anchor text matches `REFERRAL_DOC_HINTS` (`zuweis`, `anmeld`,
  `ueberweis`, `referral`, …). Relaxed to accept generic docs ONLY when the
  page URL itself strongly signals referral (`/zuweiser/`, `/referral/`, …) —
  this avoids scraping random Anfahrtspläne from a hospital's general info pages.
- `emails` — addresses whose prefix matches `REFERRAL_EMAIL_PREFIXES`
- `faxes` — numbers that appear after a "Fax:" / "Telefax:" label
- `evidence` — ordered list of methods found

`aggregate` merges per-page findings into the per-entry summary stored in
the checkpoint.

### Classification (`extractors.classify`)

- **Priority**: `info`, `kontakt`, `sekretariat`, `verwaltung`, `praxis`, `klinik`,
  `empfang`, `direktion`, `it`, `backoffice`, `mpa`, … prefix match — plus
  **any `*.hin.ch` address** (the Swiss healthcare HIN network; every
  registered clinician has one).
- **General**: `dr.*`, `doc@`, `med.*`, `prof.*` — real doctor addresses.
- **Other**: everything else.

## Extending

### Add a new email decoder

1. Implement it as a pure-Python function in `extractors.py`.
2. Wire it into `extract_emails()`.
3. Add a fixture-based unit test in `tests/test_extractors.py`.

### Tighten the noise filter

Add domains to `NOISE_EMAIL_DOMAINS` in `patterns.py`. `report.write_report`
re-applies the filter at report-build time, so adding new entries
retroactively cleans historical data — no rescraping needed.

### Add a new referral language/variant

Add keywords to `REFERRAL_HINT_WEIGHTS`, `REFERRAL_DOC_HINTS`,
`REFERRAL_EMAIL_PREFIXES`, `REFERRAL_TEXT_HINTS` in `patterns.py`. Unit tests
in `test_referral.py` cover DE/FR/IT/EN; add another case for the new variant.

## Known limitations

| Cause | Share of misses | Fixable? |
|---|---|---|
| Form-only sites (Typo3 hospitals with contact form, no email) | ~35% | ❌ no |
| JS-rendered mailtos (SPA, `mailto:\`) | ~30% | ✅ Playwright |
| Data-quality (LinkedIn URL as practice URL in DB) | ~20% | 🔧 DB cleanup |
| 403 / bot challenges | ~10% | ⚠️ partial |
| Email rendered as image | ~5% | ❌ OCR only |

Expected hit rate **~90-95%** on sites that have an email publicly available.

## Brotli

We explicitly advertise only `gzip, deflate` in `DEFAULT_HEADERS` — `requests`
can't decompress Brotli without the optional `brotli` package, and several
Swiss hospital CDNs (Netlify, Cloudflare) serve `br` by default when
advertised, which results in binary garbage. Do not re-add `br` to
`Accept-Encoding` unless you also install the `brotli` package.

## Rate limiting + politeness

- Per-domain serialization via `DomainRateLimiter` (one lock per hostname).
- Random 1–3 s delay between hits to the same host.
- Default 8–10 workers — cross-domain parallelism, never hammering any one site.
- All major Swiss clinic chains (hirslanden, hug, chuv, paraplegie, lindenhof,
  swissmedical, valaishospital, …) have permissive robots.txt for `/kontakt`,
  `/impressum`, `/team`. Verified before launch.

## Dependencies

Already in `_scrapers/requirements.txt`: `requests`, `beautifulsoup4`, `lxml`.
No new deps. Tests need `pytest` (installed into `venv/` during development).
