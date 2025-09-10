#!/usr/bin/env python3
"""
Common utilities and functions for healthcare data scrapers.
Provides unified session management, retry logic, and utility functions.
"""

import requests
import time
import random
import socket
import os
import csv
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional, Any
import logging

# Load configuration
def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

CONFIG = load_config()

# Setup logging
def setup_logging(scraper_name: str) -> logging.Logger:
    """Setup logging for a scraper"""
    logger = logging.getLogger(scraper_name)
    logger.setLevel(logging.INFO)
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger

class ScraperSession:
    """Unified session manager with retry logic and rate limiting"""
    
    def __init__(self, scraper_name: str):
        self.scraper_name = scraper_name
        self.logger = setup_logging(scraper_name)
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy from config
        retry_config = CONFIG['settings']['retry_strategy']
        retry_strategy = Retry(
            total=retry_config['total'],
            status_forcelist=retry_config['status_forcelist'],
            allowed_methods=["GET"],
            backoff_factor=retry_config['backoff_factor'],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update(CONFIG['settings']['headers'])
        
        return session
    
    def check_internet_connection(self) -> bool:
        """Check if internet connection is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except (socket.timeout, socket.gaierror, OSError):
            return False
    
    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Fetch a page with retry logic and rate limiting"""
        self.logger.info(f"Fetching URL: {url}")
        
        if not self.check_internet_connection():
            self.logger.warning("No internet connection detected")
            return None
        
        for attempt in range(max_retries):
            try:
                # Add random delay for rate limiting
                delay_config = CONFIG['settings']['delays']
                delay = random.uniform(delay_config['min_delay'], delay_config['max_delay'])
                time.sleep(delay)
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                self.logger.info(f"Successfully fetched {url} (attempt {attempt + 1})")
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    retry_delay = delay_config['retry_delay'] * (2 ** attempt)
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        
        return None

class CSVManager:
    """Unified CSV management for consistent file handling"""
    
    def __init__(self, scraper_name: str):
        self.scraper_name = scraper_name
        self.logger = setup_logging(f"{scraper_name}-csv")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str, fieldnames: Optional[List[str]] = None) -> bool:
        """Save data to CSV with consistent formatting"""
        try:
            if not data:
                self.logger.warning(f"No data to save to {filename}")
                return False
            
            # Auto-detect fieldnames if not provided
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"Saved {len(data)} records to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save CSV {filename}: {e}")
            return False
    
    def load_from_csv(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from CSV file"""
        try:
            if not os.path.exists(filename):
                self.logger.warning(f"CSV file {filename} does not exist")
                return []
            
            data = []
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
            
            self.logger.info(f"Loaded {len(data)} records from {filename}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV {filename}: {e}")
            return []
    
    def create_progress_file(self, data: List[Dict[str, Any]], page_num: int, prefix: str = "progress") -> str:
        """Create a progress file for resumable scraping"""
        filename = f"{prefix}_to_page{page_num}.csv"
        self.save_to_csv(data, filename)
        return filename
    
    def get_latest_progress_file(self, prefix: str = "progress") -> Optional[str]:
        """Get the latest progress file for resuming"""
        progress_files = []
        for filename in os.listdir('.'):
            if filename.startswith(prefix) and filename.endswith('.csv'):
                progress_files.append(filename)
        
        if not progress_files:
            return None
        
        # Sort by page number
        progress_files.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
        return progress_files[-1]
    
    def cleanup_old_progress_files(self, current_page: int, prefix: str = "progress", keep_latest: int = 3):
        """Clean up old progress files, keeping only the most recent ones"""
        progress_files = []
        for filename in os.listdir('.'):
            if filename.startswith(prefix) and filename.endswith('.csv'):
                progress_files.append(filename)
        
        if len(progress_files) <= keep_latest:
            return
        
        # Sort by page number
        progress_files.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
        
        # Keep only the most recent files
        files_to_delete = progress_files[:-keep_latest]
        
        for filename in files_to_delete:
            try:
                os.remove(filename)
                self.logger.info(f"Deleted old progress file: {filename}")
            except Exception as e:
                self.logger.warning(f"Failed to delete {filename}: {e}")

def get_scraper_config(scraper_key: str) -> Dict[str, Any]:
    """Get configuration for a specific scraper"""
    return CONFIG['scrapers'].get(scraper_key, {})

def get_searchapi_key() -> str:
    """Get SearchAPI key from config"""
    return CONFIG['settings']['searchapi_key']

def get_banned_domains() -> List[str]:
    """Get list of banned domains"""
    return CONFIG['settings']['banned_domains']

def clean_text(text: str) -> str:
    """Clean and normalize text data"""
    if not text:
        return ""
    return text.strip().replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

def extract_email(text: str) -> Optional[str]:
    """Extract email address from text using regex"""
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group() if match else None

def extract_phone(text: str) -> Optional[str]:
    """Extract Swiss phone number from text"""
    import re
    # Swiss phone patterns
    patterns = [
        r'\+41\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',  # +41 XX XXX XX XX
        r'0\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',         # 0XX XXX XX XX
        r'\d{3}\s?\d{2}\s?\d{2}',                   # XXX XX XX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group().strip()
    
    return None

def standardize_csv_output(data: List[Dict[str, Any]], scraper_type: str) -> List[Dict[str, Any]]:
    """Standardize CSV output format across all scrapers"""
    standardized_data = []
    
    for item in data:
        standardized_item = {
            'name': clean_text(item.get('name', '')),
            'address': clean_text(item.get('address', '')),
            'city': clean_text(item.get('city', '')),
            'postal_code': clean_text(item.get('postal_code', '')),
            'phone': extract_phone(item.get('phone', '')),
            'email': extract_email(item.get('email', '')),
            'website': clean_text(item.get('website', '')),
            'specialty': clean_text(item.get('specialty', '')),
            'type': scraper_type,
            'source_url': clean_text(item.get('source_url', '')),
            'scraped_at': item.get('scraped_at', ''),
        }
        standardized_data.append(standardized_item)
    
    return standardized_data