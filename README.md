# CRM System with Healthcare Data Scrapers

This is a Craft CMS 5 project with an integrated healthcare data scraping system for collecting Swiss healthcare provider information.

## Project Structure

- **Craft CMS Backend**: PHP-based content management system
- **Healthcare Data Scrapers**: Unified Python scraping system in `/_scrapers/`
- **Web Interface**: Public data access via `/web/` directory

## Quick Start

### CRM System (Craft CMS)
```bash
# Start DDEV environment
ddev start

# Install dependencies
ddev composer install

# Run migrations
ddev craft migrate/all

# Clear caches
ddev craft clear-caches/all

# Access admin panel
https://crm.ddev.site/admin/

# Other useful DDEV commands
ddev stop          # Stop environment
ddev restart       # Restart services
ddev ssh           # SSH into web container
ddev mysql         # Access MySQL CLI
```

### Healthcare Data Scrapers
```bash
# Navigate to scrapers directory
cd _scrapers

# Setup environment (one-time)
python3 setup.py

# Activate virtual environment
source venv/bin/activate

# List available scrapers
python scraper_manager.py list

# Run specific scraper
python scraper_manager.py run hospitals

# View statistics
python scraper_manager.py stats
```

## Healthcare Data Scraper System

The `/_scrapers/` directory contains a **unified, production-ready system** for scraping Swiss healthcare provider data from onedoc.ch.

### Features
- ✅ **6 Healthcare Data Sources**: Hospitals, clinics, group practices, medical centers, etc.
- ✅ **54,000+ Provider Records**: Comprehensive Swiss healthcare directory
- ✅ **Unified Architecture**: Consistent code structure and error handling
- ✅ **Resumable Scraping**: Progress tracking and continuation after interruptions
- ✅ **Rate Limiting**: Respectful scraping with built-in delays
- ✅ **Command-Line Interface**: Simple management of all scrapers
- ✅ **Comprehensive Testing**: Validated and production-ready

### Available Data Sources
1. **Hospitals** (2,562 records) - Swiss hospitals
2. **Clinics** (1,357 records) - Medical clinics  
3. **Group Practices** (2,947 records) - Multi-doctor practices
4. **Medical Centers** (764 records) - Large medical facilities
5. **Complete Directory** (46,374 records) - Full provider listing

### Data Output
All scraped data is automatically:
- Standardized to consistent CSV format
- Exported to `/web/` directory for public access
- Available for import into Craft CMS via Feed Me plugin

## Development Environment

### Requirements
- **PHP 8.3+** with nginx-fpm
- **MySQL 8.0** database
- **Python 3.7+** for scrapers
- **DDEV** for local development

### Environment Variables
Key settings in `.env`:
- `CRAFT_ENVIRONMENT=dev`
- `CRAFT_DB_*` - Database connection
- `CRAFT_SECURITY_KEY` - Encryption key

## Directory Structure

```
crm/
├── config/                 # Craft CMS configuration
├── templates/              # Twig templates
├── web/                    # Public web root + CSV exports
├── _scrapers/              # Healthcare data scraping system
│   ├── config.json         # Scraper configuration
│   ├── scraper_manager.py  # Main CLI interface
│   ├── common.py           # Shared utilities
│   ├── base_scraper.py     # Base scraper class
│   ├── hospitals/          # Hospital scrapers
│   ├── clinics/            # Clinic scrapers
│   └── ...                 # Other scraper types
├── storage/                # Craft CMS storage
└── vendor/                 # PHP dependencies
```

## Scraper System Commands

```bash
# Environment setup (run once)
cd _scrapers && python3 setup.py

# Daily usage
source _scrapers/venv/bin/activate

# List all scrapers with status
python scraper_manager.py list

# Run specific scraper
python scraper_manager.py run hospitals

# Run all scrapers in sequence  
python scraper_manager.py run-all

# Show data statistics
python scraper_manager.py stats

# Clean up old progress files
python scraper_manager.py clean

# Get help
python scraper_manager.py --help
```

## Data Integration

### Craft CMS Integration
1. **Feed Me Plugin** configured for CSV imports
2. **Content Structure** designed for healthcare providers
3. **Admin Interface** accessible via `/admin/`

### CSV Data Location
- **Source Data**: `/_scrapers/` (working files)
- **Public Data**: `/web/` (web-accessible exports)
- **Format**: Standardized CSV with consistent schema

## Documentation

- **Scraper System**: See `/_scrapers/README.md` for detailed documentation
- **Implementation**: See `/_scrapers/FINAL_SYSTEM_SUMMARY.md` for technical details
- **Setup Guide**: Run `/_scrapers/setup.py` for automated setup

## Support

- **Scrapers**: All functionality tested and validated
- **Status**: Production-ready with 54,000+ healthcare records
- **Updates**: Scrapers can be run on-demand or scheduled

---

**The healthcare data scraper system is fully unified, tested, and ready for production use.**