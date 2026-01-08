#!/usr/bin/env python3
"""
Healthcare Data Scraper Management System
Unified interface for managing and running all healthcare data scrapers.
"""

import os
import sys
import argparse
import json
import subprocess
import importlib.util
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import load_config, setup_logging, CSVManager

class ScraperManager:
    """Main management class for healthcare data scrapers"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging("scraper_manager")
        self.base_dir = Path(__file__).parent
        self.csv_manager = CSVManager("scraper_manager")
        
    def list_scrapers(self) -> None:
        """List all available scrapers with their information"""
        print("\n" + "="*80)
        print("AVAILABLE HEALTHCARE DATA SCRAPERS")
        print("="*80)
        
        for key, scraper_config in self.config['scrapers'].items():
            status = self._get_scraper_status(key)
            print(f"\n{key.upper()}")
            print(f"  Name: {scraper_config['name']}")
            print(f"  Description: {scraper_config['description']}")
            print(f"  URL: {scraper_config['url']}")
            print(f"  Main Script: {scraper_config['main_script']}")
            print(f"  Output File: {scraper_config['output_file']}")
            print(f"  Final Output: {scraper_config['final_output']}")
            print(f"  Status: {status}")
            
            if scraper_config.get('url_enricher'):
                print(f"  URL Enricher: {scraper_config['url_enricher']}")
    
    def _get_scraper_status(self, scraper_key: str) -> str:
        """Get the current status of a scraper"""
        scraper_config = self.config['scrapers'][scraper_key]
        
        # Check if output files exist
        output_file = scraper_config['output_file']
        final_output = scraper_config['final_output']
        web_output = scraper_config['web_output']
        
        status_parts = []
        
        if os.path.exists(output_file):
            mod_time = datetime.fromtimestamp(os.path.getmtime(output_file))
            status_parts.append(f"Raw data: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            status_parts.append("Raw data: Missing")
            
        if os.path.exists(final_output):
            mod_time = datetime.fromtimestamp(os.path.getmtime(final_output))
            status_parts.append(f"Final: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            status_parts.append("Final: Missing")
            
        if os.path.exists(web_output):
            mod_time = datetime.fromtimestamp(os.path.getmtime(web_output))
            status_parts.append(f"Web: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            status_parts.append("Web: Missing")
            
        return " | ".join(status_parts)
    
    def run_scraper(self, scraper_key: str, enricher_only: bool = False, force: bool = False, use_unified: bool = True) -> bool:
        """Run a specific scraper"""
        if scraper_key not in self.config['scrapers']:
            self.logger.error(f"Unknown scraper: {scraper_key}")
            return False
            
        scraper_config = self.config['scrapers'][scraper_key]
        self.logger.info(f"Starting scraper: {scraper_config['name']}")
        
        try:
            # Run main scraper unless enricher_only is True
            if not enricher_only:
                # Prefer unified script if available and use_unified is True
                script_to_run = scraper_config['main_script']
                if use_unified and scraper_config.get('main_script_unified'):
                    unified_script_path = self.base_dir / scraper_config['main_script_unified']
                    if unified_script_path.exists():
                        script_to_run = scraper_config['main_script_unified']
                        self.logger.info(f"Using unified script: {script_to_run}")
                    else:
                        self.logger.info(f"Unified script not found, using original: {script_to_run}")
                
                success = self._run_script(script_to_run, f"Main scraper for {scraper_key}")
                if not success:
                    return False
            
            # Run URL enricher if available
            if scraper_config.get('url_enricher'):
                success = self._run_script(scraper_config['url_enricher'], f"URL enricher for {scraper_key}")
                if not success:
                    return False
            
            # Copy to web directory
            self._copy_to_web(scraper_config)
            
            self.logger.info(f"Successfully completed scraper: {scraper_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error running scraper {scraper_key}: {e}")
            return False
    
    def _run_script(self, script_name: str, description: str) -> bool:
        """Run a Python script and return success status"""
        script_path = self.base_dir / script_name
        
        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return False
            
        self.logger.info(f"Running {description}: {script_name}")
        
        try:
            # Run the script as a subprocess
            # Set timeout based on script type (email scraper needs more time)
            timeout = 7200 if 'email' in script_name.lower() else 3600  # 2 hours for email scraper
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully completed: {script_name}")
                if result.stdout:
                    self.logger.info(f"Output: {result.stdout}")
                return True
            else:
                self.logger.error(f"Script failed: {script_name}")
                if result.stderr:
                    self.logger.error(f"Error: {result.stderr}")
                if result.stdout:
                    self.logger.error(f"Output: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Script timed out: {script_name}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to run script {script_name}: {e}")
            return False
    
    def _copy_to_web(self, scraper_config: Dict[str, Any]) -> None:
        """Copy final output to web directory"""
        final_output = scraper_config['final_output']
        web_output = scraper_config['web_output']
        
        if os.path.exists(final_output):
            try:
                # Ensure web directory exists
                web_dir = os.path.dirname(web_output)
                os.makedirs(web_dir, exist_ok=True)
                
                # Copy file
                import shutil
                shutil.copy2(final_output, web_output)
                self.logger.info(f"Copied {final_output} to {web_output}")
                
            except Exception as e:
                self.logger.error(f"Failed to copy to web directory: {e}")
    
    def run_all_scrapers(self, enricher_only: bool = False, use_unified: bool = True) -> None:
        """Run all scrapers sequentially"""
        self.logger.info("Starting batch run of all scrapers")
        
        failed_scrapers = []
        successful_scrapers = []
        
        for scraper_key in self.config['scrapers'].keys():
            self.logger.info(f"Processing scraper: {scraper_key}")
            
            if self.run_scraper(scraper_key, enricher_only, False, use_unified):
                successful_scrapers.append(scraper_key)
            else:
                failed_scrapers.append(scraper_key)
        
        # Summary
        print(f"\n{'='*60}")
        print("BATCH RUN SUMMARY")
        print(f"{'='*60}")
        print(f"Successful: {len(successful_scrapers)}")
        for scraper in successful_scrapers:
            print(f"  ✓ {scraper}")
        
        if failed_scrapers:
            print(f"\nFailed: {len(failed_scrapers)}")
            for scraper in failed_scrapers:
                print(f"  ✗ {scraper}")
        
        print(f"\nTotal: {len(successful_scrapers)}/{len(self.config['scrapers'])} successful")
    
    def show_statistics(self) -> None:
        """Show statistics about scraped data"""
        print(f"\n{'='*80}")
        print("DATA STATISTICS")
        print(f"{'='*80}")
        
        total_records = 0
        
        for scraper_key, scraper_config in self.config['scrapers'].items():
            web_output = scraper_config['web_output']
            
            if os.path.exists(web_output):
                try:
                    data = self.csv_manager.load_from_csv(web_output)
                    record_count = len(data)
                    total_records += record_count
                    
                    mod_time = datetime.fromtimestamp(os.path.getmtime(web_output))
                    
                    print(f"\n{scraper_config['name']}")
                    print(f"  Records: {record_count:,}")
                    print(f"  Last Updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  File: {web_output}")
                    
                except Exception as e:
                    print(f"\n{scraper_config['name']}")
                    print(f"  Error reading file: {e}")
            else:
                print(f"\n{scraper_config['name']}")
                print("  No data file found")
        
        print(f"\nTOTAL RECORDS: {total_records:,}")
    
    def clean_progress_files(self) -> None:
        """Clean up old progress files"""
        self.logger.info("Cleaning up old progress files")
        
        progress_files = []
        for filename in os.listdir('.'):
            if filename.startswith('progress_') and filename.endswith('.csv'):
                progress_files.append(filename)
        
        if not progress_files:
            print("No progress files found to clean")
            return
        
        print(f"Found {len(progress_files)} progress files:")
        for filename in progress_files:
            print(f"  {filename}")
        
        response = input("\nDelete all progress files? (y/N): ")
        if response.lower() == 'y':
            for filename in progress_files:
                try:
                    os.remove(filename)
                    print(f"  Deleted: {filename}")
                except Exception as e:
                    print(f"  Failed to delete {filename}: {e}")
        else:
            print("Cleanup cancelled")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Healthcare Data Scraper Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List all available scrapers')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a specific scraper')
    run_parser.add_argument('scraper', help='Scraper key to run')
    run_parser.add_argument('--enricher-only', action='store_true', help='Run only URL enricher')
    run_parser.add_argument('--force', action='store_true', help='Force run even if data exists')
    run_parser.add_argument('--no-unified', action='store_true', help='Use original scripts instead of unified versions')
    
    # Run all command
    run_all_parser = subparsers.add_parser('run-all', help='Run all scrapers')
    run_all_parser.add_argument('--enricher-only', action='store_true', help='Run only URL enrichers')
    run_all_parser.add_argument('--no-unified', action='store_true', help='Use original scripts instead of unified versions')
    
    # Stats command
    subparsers.add_parser('stats', help='Show data statistics')
    
    # Clean command
    subparsers.add_parser('clean', help='Clean up old progress files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ScraperManager()
    
    try:
        if args.command == 'list':
            manager.list_scrapers()
        elif args.command == 'run':
            use_unified = not args.no_unified
            success = manager.run_scraper(args.scraper, args.enricher_only, args.force, use_unified)
            sys.exit(0 if success else 1)
        elif args.command == 'run-all':
            use_unified = not args.no_unified
            manager.run_all_scrapers(args.enricher_only, use_unified)
        elif args.command == 'stats':
            manager.show_statistics()
        elif args.command == 'clean':
            manager.clean_progress_files()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        manager.logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()