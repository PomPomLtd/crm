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
7. **email-scraper** - Extract email addresses from practice websites (for CRM entries with zuweisung=1)

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

### **Email Scraper**
```bash
# Run email scraper for CRM entries (zuweisung=1)
python scraper_manager.py run email-scraper

# Check email scraper status
python scraper_manager.py list | grep EMAIL-SCRAPER

# Run email scraper directly (bypass manager)
python email_scraper.py

# View email scraping results
head -10 scraped_emails.csv

# Count total emails found
python3 -c "
import pandas as pd
df = pd.read_csv('scraped_emails.csv')
print(f'Total emails found: {df.total_emails_found.sum()}')
print(f'Success rate: {len(df[df.scraping_status==\"success\"])/len(df)*100:.1f}%')
"
```