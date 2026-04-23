# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Craft CMS 5 application for Pom Pom GmbH combining three distinct subsystems:

1. **Craft CMS backend** (PHP 8.2+) using Feed Me for CSV imports. Healthcare-provider entries live in sections `medicalCenters` (2), `clinics` (3), `groupPractices` (4), `medClinics` (5), `hospitals` (6); section 1 (`crmDocs`) holds solo doctors. A custom "MediTransfer Mailer" plugin previously lived under `plugins/` but has been removed; the rewrite lives outside Craft as a standalone Python service (see `_mailer/`).
2. **Python scraping suite** under `_scrapers/` that collects Swiss healthcare provider data from `onedoc.ch` and emits CSVs to `/web/`, which are then imported into Craft via Feed Me.
3. **Cold-outreach mailer** under `_mailer/` (separate Python app, deployed standalone on Fly.io) that sends the MediTransfer A/B/C campaign to ~10–15k clinics via Postmark, tracks opens/clicks/conversions, and serves a small dashboard.

Local development runs inside DDEV (nginx-fpm, PHP 8.3, MySQL 8.0). The public URL is `https://crm.ddev.site`.

## Development Commands

All PHP/Craft work must go through DDEV (the host has no PHP runtime configured for this project):

- `ddev start` / `ddev restart` / `ddev stop`
- `ddev composer <cmd>` — Composer inside the web container
- `ddev craft <cmd>` — Craft console (e.g. `migrate/all`, `project-config/apply`, `clear-caches/all`)
- `ddev ssh` — shell into web container; `ddev mysql` — MySQL CLI
- `ddev import-db` / `ddev export-db`

### Scraper CLI

The scrapers are driven by a single manager, not by running individual scripts:

```bash
cd _scrapers
python3 setup.py                          # one-time: creates venv + installs requirements
source venv/bin/activate
python scraper_manager.py list            # show all scrapers + status
python scraper_manager.py run <key>       # run one scraper (keys from config.json)
python scraper_manager.py run-all         # run everything in sequence
python scraper_manager.py stats           # record counts per source
python scraper_manager.py clean           # remove stale progress files
```

Scraper keys (see `_scrapers/config.json`): `hospitals`, `clinics`, `group-practices`, `medical-clinics`, `medical-centers`, `complete-directory`.

### Clinic email finder

A separate, newer subsystem at `_scrapers/clinic_emails/` (package) with entry point `_scrapers/find_clinic_emails.py`. Purpose: find real email addresses on the websites of the clinics/hospitals that `scraper_manager` has already imported into Craft.

```bash
cd _scrapers && source venv/bin/activate
python find_clinic_emails.py --refresh-input     # dump ~18k target URLs from DB
python find_clinic_emails.py --test <URL>        # diagnose one URL
python find_clinic_emails.py --sample 50         # random benchmark
python find_clinic_emails.py --workers 10        # full run (resumable)
python find_clinic_emails.py --report            # rebuild CSV from checkpoint
python -m pytest tests/ -v                       # unit tests (35+ cases)
```

Reads target entries directly from the Craft DB via `ddev mysql` (sections 2-6 only; section 1 = solo doctors excluded). For each site it fetches the homepage + top-scored contact/impressum/team pages **and top-scored referral pages** (Zuweiser / Médecins référents / Medici invianti / Refer-a-Patient) and extracts:

1. **Emails** via 10 decoders: mailto, Cloudflare `data-cfemail` XOR, WordPress email-encoder-bundle, `(at)/[dot]` text obfuscation, HTML entities, `data-email` attributes, DeCryptX known-ciphertext lookup, `<script>` string literals, raw-HTML sweep, and ROT13 fallback (catches the clienia.ch anti-scraping pattern where TLDs get rotated `.ch`→`.pu` / `.com`→`.pbz`). Filters Wix/Sentry noise and image-filename look-alikes.

    **Classification** (see `clinic_emails/patterns.py` + `extractors.py::classify()`):
    - **`priority`** bucket sorted by three tiers (best first):
      - `hin.ch` domain (owner-operated Swiss secure email — always priority, any local-part, never dropped by third-party filters)
      - **TOP**: `sekretariat*`, `secretariat*`, `empfang`, `reception`, `zuweiser*`, `zuweisung*`, `triage`, `anmeldung`, `mpa`, `referral`, `referring`, `medecin-referent`, `termine`/`termin`, etc. (compound-safe, so `sekretariatsdienste@` and `zuweiserbrief@` also match) — these are secretariat/reception/referral-coordinator mailboxes, the highest-value Meditransfer targets.
      - **MID**: `info`, `kontakt`, `contact`, `praxis`, `klinik`, `cabinet`, `studio` (general reception mailboxes)
      - **LOW**: `office`, `buero`, `verwaltung`, `administration`, `leitung` (generic office, still priority but last-resort)
      - `it`, `support`, `edv`, `admin`, `buchhaltung` are deliberately **NOT** priority — those are the tech helpdesk, wrong audience.
    - **`general`**: doctor-prefix addresses (`dr.`, `doc.`, `med.`, `arzt.`, etc.)
    - **`other`**: fallback
    - Noise/agency filters drop: `activemind.legal`, `wepractice.ch`, `*.ingest.sentry.io`, `muster.com`, `fotolia.com`, regex match on `webdesign-*`, `*.agency`, `*.digital`, `*.studio`, etc. — see `AGENCY_DOMAIN_PATTERNS` and `NOISE_EMAIL_DOMAIN_PATTERNS` in `patterns.py` for the full list.
    - **Third-party legal-only drop**: if an email's domain differs from the practice's own domain AND the only recorded source URL is a legal/privacy page (`/impressum`, `/datenschutz`, etc.), the email is dropped as a third-party leak (catches DPO-as-a-service and web-agency credits). Exempts `hin.ch` addresses — those are always the practice's own.

2. **Referral characterization** (DE/FR/IT/EN): does this clinic have a referral section, and HOW does it accept referrals? Methods detected: web form (`form`), downloadable PDF (`pdf`), Word/RTF/ODT (`doc`), dedicated email (`email`), fax number (`fax`), or `page-only` text. PDF/DOC links are filtered: only those with referral keywords in href/anchor — unless the page URL itself is unambiguously referral-themed, in which case generic docs pass through.

Both passes piggyback on the same HTTP fetches; one crawl yields both data sets. Resumable via append-only JSONL checkpoint (`results/clinic_emails_checkpoint.jsonl`).

Companion diagnostic: `research_email_patterns.py` samples N random URLs and catalogs which obfuscation patterns / CMSs / contact-page conventions exist in the target population. Useful for gauging expected hit rate before a long run and for discovering new decoders worth adding.

**Reclassify-only tool** (`_scrapers/reclassify_checkpoint.py`): re-runs `clean_email()` + `classify()` on the existing checkpoint without touching the network. Use after tightening filters or adding new noise patterns — recovers `sekretariat*` compounds, `zuweiser@` variants, ROT13-able addresses, and drops addresses that the stricter filters now reject. Produces a `.reclassified.jsonl` alongside the original and prints a before/after bucket diff.

### URL enrichment (`_scrapers/url_enrichment.py`)

Second-stage tool that **fills the `URL` field on existing Craft entries**. The initial Feed-Me import populated URLs for some entries but ~35k entries across sections 2–6 were left without a URL — mostly because `groupclinics/urlFetch.py` and `med-clinic/urlFetch.py` used rate-limited DuckDuckGo, giving up after backoff. Without a URL, the email scraper can't crawl those practices and we lose thousands of potential email addresses.

The enrichment runner:

1. Queries Craft for enabled entries in sections 2–6 that lack the URL field (`ee61a20b-95a1-4265-b42d-84a780431065`).
2. **Dedupes in SQL** via `GROUP BY title, city, sectionId` — Feed-Me imported most practices twice (consecutive entry IDs with the same title/city); this collapses them so we only hit SearchAPI once per practice.
3. Calls SearchAPI's Google engine (`num=10`, gl=ch, hl=de) with `{title} {city}`.
4. Picks the first result in positions 1–2 that passes:
   - Not in `BANNED_DOMAINS` (onedoc, doktor.ch, search.ch, firmen.ch, doctena, zip.ch, logicrdv, medsite, therapievermittlung, treatwell, hin.ch, social/search/wiki, etc.)
   - Not in `LARGE_PROVIDER_DOMAINS` (hirslanden, usz, ksa, ksb, ksw, ksgr, insel, luks, sanacare, medbase, swissmedical, h-och, upd, upk, pdag, etc.)
   - Not a PDF/DOC/RTF path
   - Not a staging/test subdomain
5. Writes the URL back into `elements_sites.content` via `JSON_SET` on the same field UID the scraper reads.
6. If no clean URL is found in positions 1–2, records `reason="no_site_in_top_2:<top_host>"` and moves on — the practice likely has no website of its own, and taking a position-3+ long-shot result would corrupt Craft with directory/aggregator URLs.

```bash
cd _scrapers && source venv/bin/activate
python url_enrichment.py --test 307073           # one entry dry-run
python url_enrichment.py --sections 4 --limit 500 --workers 8   # small batch
python url_enrichment.py --workers 8             # full run, all 5 sections
python url_enrichment.py --no-tui --workers 8    # plain log output (CI/pipe-safe)
```

Rich-based live TUI (`LiveTUI` class inline in the script) mirrors the `clinic_emails/tui.py` style: header progress bar → workers panel (with section code) + dashboard panel (outcomes bar, pick-position histogram, per-section hit-rate) → recent tail. Resumable via `_scrapers/results/url_enrichment_checkpoint.jsonl` — every completed entry is appended atomically; re-runs skip any already-processed entry.

**When to re-run**: after any new Feed-Me import that adds entries without URLs, or after tightening the banned-domain list (in which case: null the URL field for the checkpointed entries via `UPDATE elements_sites SET content = JSON_REMOVE(content, '$."<URL_UID>"')` so they get re-processed).

### Legacy scraper subsystem (onedoc.ch directory crawl)

Separate from the clinic email finder. These populate Craft in the first place:

- All scrapers inherit from `_scrapers/base_scraper.py` (`BaseHealthcareScraper`), which provides per-canton, per-page progress tracking via `{scraper_key}_processed_pages.csv` and `{scraper_key}_progress.csv` — runs are resumable.
- `_scrapers/config.json` holds scraper metadata (source URLs, script paths, output filenames, web-facing CSV destinations) plus global settings (retry policy, 1-3s delays, `banned_domains`).
- Each scraper directory (`hospitals/`, `clinics/`, etc.) contains a crawler (`get-*.py`) and a `urlFetch.py` that enriches rows with practice website URLs via SearchAPI.
- **The `clinic_emails` package does NOT use `base_scraper`, `scraper_manager`, or `config.json`'s `scrapers` dict** — it reads its own settings from `clinic_emails/patterns.py`.

### Data pipeline

```
onedoc.ch → scraper_manager.py → _scrapers/*.csv → /web/*.csv → Feed Me → Craft entries
                                                                ↘ _mailer/ (reads scraper checkpoint + Craft DB for segmentation)
```

CSV filenames in `/web/` are referenced by Feed Me feed configs stored in Craft's project config (`config/project/`). Renaming or moving a web CSV will break the corresponding feed.

### Cold-outreach mailer (`_mailer/`)

Standalone Python service (Flask + SQLite + Postmark) deployed to Fly.io as `meditransfer-mailer.fly.dev`. Sends the MediTransfer cold-outreach campaign to ~10–15k Swiss clinics with three-way A/B/C split testing.

**Read `_mailer/README.md` first** — it documents the full architecture, ops workflow, env vars, dashboard, conversion endpoint, and Fly deployment.

Quick orientation:

- Reads emails from `_scrapers/results/clinic_emails_checkpoint.jsonl` (the scraper's append-only checkpoint).
- Reads canton/profession/section segmentation from the Craft DB via `ddev mysql` (same query pattern as `_scrapers/clinic_emails/entries.py`).
- All sending happens **inside the Fly container** via `fly ssh console -C "python send_mailer.py …"` so the SQLite state DB on the mounted volume is the single source of truth. Local CLI runs are dev-only.
- Webhooks (open/click/bounce/spam/subscription) land at `/webhook/postmark`; conversions from the meditransfer.ch site land at `/api/conversion` (see `_mailer/CONVERSION_API.md` for the integration handoff).
- Dashboard at `/dashboard` (HTTP Basic Auth).
- 55 unit tests under `_mailer/tests/`; run via `cd _mailer && ../_scrapers/venv/bin/python -m pytest tests/ -v`.

**Don't** re-add the old MediTransfer Mailer Craft plugin — it was deliberately removed and the rewrite is intentionally external to Craft.

### Craft config notes

- `config/general.php` sets `omitScriptNameInUrls`, `preloadSingles`, and `preventUserEnumeration`. `@webroot` is explicitly aliased so `clear-caches` works from CLI.
- Environment-specific config is driven entirely by `CRAFT_ENVIRONMENT` (see `.env.example.dev`). There is no multi-environment `config/*/` split beyond `config/project/`.
- `putyourlightson/craft-dashboard-begone` is installed — the default Craft dashboard is suppressed.

## Commit Messages

- **Never** add "Generated with Claude Code", "Co-Authored-By: Claude", or similar AI attribution.
- Keep messages focused on what changed and why.
