# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Craft CMS 5 application for Pom Pom GmbH combining two distinct subsystems:

1. **Craft CMS backend** (PHP 8.2+) using Feed Me for CSV imports. Healthcare-provider entries live in sections `medicalCenters` (2), `clinics` (3), `groupPractices` (4), `medClinics` (5), `hospitals` (6); section 1 (`crmDocs`) holds solo doctors. A custom "MediTransfer Mailer" plugin previously lived under `plugins/` but has been removed and is slated for a rewrite.
2. **Python scraping suite** under `_scrapers/` that collects Swiss healthcare provider data from `onedoc.ch` and emits CSVs to `/web/`, which are then imported into Craft via Feed Me.

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

1. **Emails** via several decoders: mailto, Cloudflare `data-cfemail` XOR, WordPress email-encoder-bundle, `(at)/[dot]` text obfuscation, HTML entities, `data-email` attributes, DeCryptX known-ciphertext lookup. Filters Wix/Sentry noise and image-filename look-alikes. Classifies into `priority` (info/kontakt/secretary prefixes, plus every `*@hin.ch` address since that's the Swiss healthcare HIN network), `general` (doctor prefixes), `other`.
2. **Referral characterization** (DE/FR/IT/EN): does this clinic have a referral section, and HOW does it accept referrals? Methods detected: web form (`form`), downloadable PDF (`pdf`), Word/RTF/ODT (`doc`), dedicated email (`email`), fax number (`fax`), or `page-only` text. PDF/DOC links are filtered: only those with referral keywords in href/anchor — unless the page URL itself is unambiguously referral-themed, in which case generic docs pass through.

Both passes piggyback on the same HTTP fetches; one crawl yields both data sets. Resumable via append-only JSONL checkpoint (`results/clinic_emails_checkpoint.jsonl`).

Companion diagnostic: `research_email_patterns.py` samples N random URLs and catalogs which obfuscation patterns / CMSs / contact-page conventions exist in the target population. Useful for gauging expected hit rate before a long run and for discovering new decoders worth adding.

### Legacy scraper subsystem (onedoc.ch directory crawl)

Separate from the clinic email finder. These populate Craft in the first place:

- All scrapers inherit from `_scrapers/base_scraper.py` (`BaseHealthcareScraper`), which provides per-canton, per-page progress tracking via `{scraper_key}_processed_pages.csv` and `{scraper_key}_progress.csv` — runs are resumable.
- `_scrapers/config.json` holds scraper metadata (source URLs, script paths, output filenames, web-facing CSV destinations) plus global settings (retry policy, 1-3s delays, `banned_domains`).
- Each scraper directory (`hospitals/`, `clinics/`, etc.) contains a crawler (`get-*.py`) and a `urlFetch.py` that enriches rows with practice website URLs via SearchAPI.
- **The `clinic_emails` package does NOT use `base_scraper`, `scraper_manager`, or `config.json`'s `scrapers` dict** — it reads its own settings from `clinic_emails/patterns.py`.

### Data pipeline

```
onedoc.ch → scraper_manager.py → _scrapers/*.csv → /web/*.csv → Feed Me → Craft entries
```

CSV filenames in `/web/` are referenced by Feed Me feed configs stored in Craft's project config (`config/project/`). Renaming or moving a web CSV will break the corresponding feed.

### Craft config notes

- `config/general.php` sets `omitScriptNameInUrls`, `preloadSingles`, and `preventUserEnumeration`. `@webroot` is explicitly aliased so `clear-caches` works from CLI.
- Environment-specific config is driven entirely by `CRAFT_ENVIRONMENT` (see `.env.example.dev`). There is no multi-environment `config/*/` split beyond `config/project/`.
- `putyourlightson/craft-dashboard-begone` is installed — the default Craft dashboard is suppressed.

## Commit Messages

- **Never** add "Generated with Claude Code", "Co-Authored-By: Claude", or similar AI attribution.
- Keep messages focused on what changed and why.
