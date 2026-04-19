# Healthcare Data Scrapers

Unified system for scraping Swiss healthcare provider data from onedoc.ch.

## Quick Start

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **List available scrapers:**
   ```bash
   python scraper_manager.py list
   ```

4. **Run a specific scraper:**
   ```bash
   python scraper_manager.py run hospitals
   ```

5. **Run all scrapers:**
   ```bash
   python scraper_manager.py run-all
   ```

## Available Commands

### scraper_manager.py

- `list` - Show all available scrapers and their status
- `run <scraper>` - Run a specific scraper by key
- `run-all` - Run all scrapers sequentially
- `stats` - Show data statistics for all scrapers
- `clean` - Clean up old progress files

### Options

- `--enricher-only` - Run only URL enrichment (requires existing data)
- `--force` - Force run even if data already exists

## Scraper Types

### **Directory Scrapers** (OneDOC.ch)
1. **hospitals** - Swiss hospitals from onedoc.ch/de/spital
2. **clinics** - Medical clinics from onedoc.ch/de/klinik  
3. **group-practices** - Group practices from onedoc.ch/de/gruppenpraxis
4. **medical-clinics** - Medical clinics from onedoc.ch/de/medizinische-praxis
5. **medical-centers** - Medical centers from onedoc.ch/de/medizinisches-zentrum
6. **complete-directory** - Complete directory from onedoc.ch/de/verzeichnis

### **Specialized Scrapers**
7. **clinic_emails** — Find real email addresses on clinic websites. Reads target entries directly from the Craft CMS database, crawls homepage + contact/impressum/team pages, and extracts emails via multiple decoders (mailto, Cloudflare `data-cfemail`, WordPress EEB, `(at)/[dot]` obfuscation, HTML entities, DeCryptX known mappings). Rejects noise like Wix Sentry IDs and image-filename look-alikes. Run via `python find_clinic_emails.py --help`.

## File Structure

- `config.json` - Central configuration for all scrapers
- `common.py` - Shared utilities (session management, CSV handling)
- `scraper_manager.py` - Main management interface
- `requirements.txt` - Python dependencies
- `*_progress.csv` - Progress tracking files for resumable scraping
- `*_processed_pages.csv` - Page tracking for resumption

## Output Files

Raw data files are saved in the scraper root directory, then copied to:
- `../web/` directory for web access
- Final output includes URL enrichment where available

## Features

- **Resumable scraping** - Automatically resumes from where it left off
- **Rate limiting** - Built-in delays and retry logic
- **Progress tracking** - Detailed logging and progress files
- **Unified format** - Consistent CSV output across all scrapers
- **Error handling** - Robust error handling with retries
- **URL enrichment** - Optional secondary pass for additional data

## Configuration

Edit `config.json` to modify:
- Scraper URLs and settings
- Output file locations
- Headers and retry strategies
- Rate limiting parameters

## Troubleshooting

1. **Module not found errors**: Make sure virtual environment is activated
2. **Network errors**: Check internet connection and rate limiting settings
3. **Permission errors**: Ensure write access to output directories
4. **Memory issues**: Process scrapers individually instead of batch mode

## Examples

### **Directory Scrapers**
```bash
# Show current status of all scrapers
python scraper_manager.py list

# Run hospitals scraper only
python scraper_manager.py run hospitals

# Run URL enrichment only for clinics
python scraper_manager.py run clinics --enricher-only

# Get statistics on all scraped data
python scraper_manager.py stats

# Clean up old progress files
python scraper_manager.py clean
```

### **Clinic Email Finder** (`clinic_emails` package)

Reads targets directly from the Craft DB (sections 2/3/4/5/6 only — solo doctors in section 1 are excluded), crawls each site, extracts emails. Resumable via JSONL checkpoint; single-terminal, multi-threaded with per-domain rate limiting.

```bash
# One-time: dump target entries from DB (~18k with practice URL)
python find_clinic_emails.py --refresh-input

# Diagnose one URL
python find_clinic_emails.py --test https://www.praxismuehleberg.ch/

# Random benchmark on 20 entries
python find_clinic_emails.py --sample 20

# Restrict to one section (6 = hospitals)
python find_clinic_emails.py --section 6 --workers 10

# Full run (resumable — Ctrl-C and re-run anytime)
python find_clinic_emails.py --workers 8

# Rebuild CSV + summary from existing checkpoint
python find_clinic_emails.py --report
```

Outputs land in `results/`:
- `clinic_emails_checkpoint.jsonl` — append-only state; source-of-truth for resume
- `clinic_emails_<ts>.csv` — one row per entry, columns for priority/general/other buckets
- `clinic_emails_<ts>_summary.txt` — per-section hit rate, top email domains

**Unit tests** (all extractor decoders):
```bash
python -m pytest tests/ -v
```

**Reconnaissance tool** — sample N sites and catalog which obfuscation patterns exist, which CMSs dominate, whether contact links are discoverable. Useful for gauging expected hit rate before a long run.

```bash
python research_email_patterns.py --n 80 --seed 7
# -> results/research_patterns_<ts>.md
```
```