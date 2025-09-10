# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Craft CMS 5 project with an integrated data scraping system for collecting healthcare provider information. The project uses DDEV for local development and combines a PHP-based CMS with Python scrapers for data collection.

## Development Commands

### DDEV Environment
- `ddev start` - Start the development environment
- `ddev stop` - Stop the development environment
- `ddev restart` - Restart services
- `ddev ssh` - SSH into the web container
- `ddev exec` - Execute commands in the web container

### Craft CMS Commands
- `./craft` - Run Craft console commands
- `./craft migrate/all` - Run all migrations
- `./craft project-config/apply` - Apply project configuration changes
- `./craft clear-caches/all` - Clear all caches

### Composer
- `composer install` - Install PHP dependencies
- `composer update` - Update PHP dependencies
- `composer require [package]` - Add new PHP package

### Database
- `ddev import-db` - Import database from dump
- `ddev export-db` - Export database
- `ddev mysql` - Access MySQL CLI

## Architecture Overview

### Core Structure
- **Craft CMS Backend**: PHP-based content management system using Craft CMS 5
- **Web Root**: `/web/` directory serves the public site with `index.php` as entry point
- **Configuration**: Environment-specific configs in `/config/` directory
- **Templates**: Twig templates in `/templates/` directory
- **Data Scrapers**: Python scripts in `/_scrapers/` for healthcare data collection

### Key Directories
- `/config/` - Craft CMS configuration files (general.php, app.php, routes.php)
- `/templates/` - Twig template files
- `/web/` - Public web root with CSV data exports
- `/storage/` - Craft CMS storage directory (logs, cache, etc.)
- `/_scrapers/` - Python scraping scripts organized by target type:
  - `/hospitals/` - Hospital data scrapers
  - `/clinics/` - Medical clinic scrapers  
  - `/groupclinics/` - Group practice scrapers
  - `/medicalCenters/` - Medical center scrapers
  - `/docs/` - Scraper documentation and data exports

### Data Flow
1. Python scrapers collect healthcare provider data from various sources
2. Data is processed and exported as CSV files to `/web/` directory
3. Craft CMS can import and manage this data through the Feed Me plugin
4. Final data is accessible via the web interface

## Environment Configuration

### DDEV Setup
- PHP 8.3 with nginx-fpm
- MySQL 8.0 database
- Project name: `crm`
- Access via: `https://crm.ddev.site`

### Environment Variables
Key environment variables (see `.env.example.dev`):
- `CRAFT_APP_ID` - Unique application identifier
- `CRAFT_ENVIRONMENT=dev` - Environment setting
- `CRAFT_DB_*` - Database connection settings
- `CRAFT_SECURITY_KEY` - Security key for encryption
- `CRAFT_DEV_MODE=true` - Enable development mode

## Scraping System

The `/_scrapers/` directory contains Python scripts for collecting healthcare provider data:

### Structure
- Each scraper type has its own directory with specialized scripts
- Python virtual environment located at `/_scrapers/venv/`
- Common patterns: `urlFetch.py` for URL collection, main scrapers for data extraction
- Output typically saved as CSV files in `/web/` for public access

### Python Environment
- Activate venv: `source _scrapers/venv/bin/activate`
- Install requirements: `pip install -r requirements.txt`
- Scrapers use libraries like requests, BeautifulSoup, pandas for data collection

## Data Management

### CSV Exports
The `/web/` directory contains various CSV files with healthcare provider data:
- `hospitals.csv` - Hospital directory data
- `clinics.csv` - Medical clinic information
- `group_practices.csv` - Group practice data
- `med_centers.csv` - Medical center listings
- Various processed and deduplicated versions

### Craft CMS Integration
- Feed Me plugin configured for CSV imports
- Content structure designed for healthcare provider information
- Admin interface accessible via `/admin/`

## Important Notes

### Security
- Environment variables stored in `.env` (not committed)
- License key files in `/config/` (likely excluded from git)
- Database credentials managed through DDEV

### Dependencies
- PHP 8.2+ required (composer.json specifies platform requirement)
- Python 3.x for scraping scripts
- DDEV for consistent development environment
- Craft CMS 5.x with Feed Me plugin

### File Permissions
- Ensure `/storage/` directory is writable
- CSV files in `/web/` should be publicly accessible
- Python virtual environment may need activation before running scrapers