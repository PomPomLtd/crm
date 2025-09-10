#!/usr/bin/env python3
"""
Base scraper class for all healthcare data scrapers.
Provides common functionality and structure for consistent scraping.
"""

import os
import sys
import csv
import re
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

# Add current directory to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ScraperSession, CSVManager, get_scraper_config, standardize_csv_output

class BaseHealthcareScraper(ABC):
    """Base class for all healthcare scrapers"""
    
    def __init__(self, scraper_key: str):
        self.scraper_key = scraper_key
        self.config = get_scraper_config(scraper_key)
        self.session = ScraperSession(scraper_key)
        self.csv_manager = CSVManager(scraper_key)
        
        self.overview_url = self.config['url']
        self.output_file = self.config['output_file']
        
        # Progress tracking
        self.processed_pages = self._load_processed_pages()
        self.scraped_urls = self._load_scraped_urls()
        
    def _load_processed_pages(self) -> Dict[str, Set[int]]:
        """Load already processed pages from tracking file"""
        processed = {}
        tracking_file = f'{self.scraper_key}_processed_pages.csv'
        
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        canton = row[0]
                        page = int(row[1])
                        if canton not in processed:
                            processed[canton] = set()
                        processed[canton].add(page)
        return processed
    
    def _load_scraped_urls(self) -> Set[str]:
        """Load already scraped URLs to avoid duplicates"""
        scraped_urls = set()
        progress_file = f'{self.scraper_key}_progress.csv'
        
        if os.path.exists(progress_file):
            data = self.csv_manager.load_from_csv(progress_file)
            for row in data:
                scraped_urls.add(row.get('url', ''))
                
        self.session.logger.info(f"Found {len(scraped_urls)} already scraped items")
        return scraped_urls
    
    def _mark_page_processed(self, canton: str, page_num: int):
        """Mark a page as processed in tracking file"""
        with open(f'{self.scraper_key}_processed_pages.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([canton, page_num])
    
    def extract_canton_links(self, html: str) -> List[Dict[str, str]]:
        """Extract links to canton pages from overview page"""
        if not html:
            return []
        
        canton_links = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for canton links - this is consistent across all OneDOC pages
        canton_headings = soup.select('.top-states h2 a')
        
        for heading in canton_headings:
            canton_url = "https://www.onedoc.ch" + heading['href']
            canton_name = heading.text.strip()
            canton_links.append({'name': canton_name, 'url': canton_url})
        
        self.session.logger.info(f"Found {len(canton_links)} canton links")
        return canton_links
    
    def get_max_page_number(self, html: str, canton_url: str) -> int:
        """Determine maximum number of pages from pagination"""
        if not html:
            return 1
        
        soup = BeautifulSoup(html, 'html.parser')
        pagination = soup.find('ul', class_='pagination')
        
        if not pagination:
            return 1
        
        # Extract all visible page numbers
        visible_pages = []
        for link in pagination.find_all('a'):
            try:
                page_num = int(link.text.strip())
                visible_pages.append(page_num)
            except (ValueError, TypeError):
                continue
        
        if not visible_pages:
            return 1
        
        # Get the highest visible page and check if there might be more
        highest_visible = max(visible_pages)
        
        # For robustness, check one page beyond what's visible
        test_page = highest_visible + 1
        test_url = f"{canton_url}?page={test_page}"
        response = self.session.fetch_page(test_url)
        
        if response:
            test_soup = BeautifulSoup(response.text, 'html.parser')
            test_items = test_soup.find_all('div', class_='directory-item')
            if test_items:
                self.session.logger.info(f"Found more pages beyond {highest_visible}")
                return test_page
        
        return highest_visible
    
    @abstractmethod
    def extract_item_details(self, url: str, item_name: str, index: int, total: int) -> Dict[str, Any]:
        """Extract detailed information from item page - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_scraper_type(self) -> str:
        """Return the type string for standardization - to be implemented by subclasses"""
        pass
    
    def parse_address(self, address: str) -> Dict[str, str]:
        """Parse address into components (street, postal code, city)"""
        street = ""
        postal_code = ""
        city = ""
        
        if address and ", " in address:
            address_parts = address.split(", ")
            street = address_parts[0].strip()
            
            if len(address_parts) > 1:
                postal_city = address_parts[1].strip()
                # Extract postal code (4 digits) and city
                postal_match = re.search(r'(\d{4})\s+(.*)', postal_city)
                if postal_match:
                    postal_code = postal_match.group(1)
                    city = postal_match.group(2).strip()
                else:
                    city = postal_city
        
        return {
            'street': street,
            'postal_code': postal_code,
            'city': city
        }
    
    def extract_items(self, html: str, canton_name: str) -> List[Dict[str, Any]]:
        """Extract item data from canton page"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='directory-item')
        
        self.session.logger.info(f"Found {len(items)} items on this page")
        
        extracted_items = []
        for index, item in enumerate(items, 1):
            # Extract basic information
            name_element = item.find('a')
            name = name_element.text.strip() if name_element else "Unknown"
            item_url = ("https://www.onedoc.ch" + name_element['href'] 
                       if name_element and name_element.has_attr('href') else "")
            
            # Skip if already processed
            if item_url in self.scraped_urls:
                continue
            
            # Extract address
            address_element = item.find('div', class_='directory-item-text-normal')
            address = address_element.text.strip() if address_element else ""
            
            # Parse address components
            address_parts = self.parse_address(address)
            
            # Create item data
            item_data = {
                'name': name,
                'address': address,
                'street': address_parts['street'],
                'postal_code': address_parts['postal_code'],
                'city': address_parts['city'],
                'phone': "",
                'email': "",
                'website': item_url,
                'specialty': "",
                'source_url': item_url,
                'scraped_at': datetime.now().isoformat(),
                'canton': canton_name
            }
            
            # Get additional details using subclass implementation
            if item_url:
                details = self.extract_item_details(item_url, name, index, len(items))
                item_data['phone'] = details.get('phone_number', '')
                item_data['specialty'] = ", ".join(details.get('professions', []))
                item_data['email'] = details.get('email', '')
                if details.get('website'):
                    item_data['website'] = details['website']
            
            extracted_items.append(item_data)
            self.scraped_urls.add(item_url)
            
            # Show progress
            if index % 10 == 0 or index == len(items):
                self.session.logger.info(f"Progress: {index}/{len(items)} items processed")
        
        return extracted_items
    
    def save_progress(self, data: List[Dict[str, Any]]):
        """Save progress data"""
        if not data:
            return
        
        progress_file = f'{self.scraper_key}_progress.csv'
        file_exists = os.path.isfile(progress_file)
        
        with open(progress_file, 'a', newline='', encoding='utf-8') as f:
            if data:
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(data)
        
        self.session.logger.info(f"Saved progress: {len(data)} items")
    
    def run(self):
        """Main scraping logic"""
        self.session.logger.info(f"Starting {self.config['name']} scraper")
        all_items = []
        total_count = 0
        
        # Fetch overview page
        response = self.session.fetch_page(self.overview_url)
        if not response:
            self.session.logger.error("Failed to fetch overview page")
            return
        
        # Extract canton links
        canton_links = self.extract_canton_links(response.text)
        
        # Process each canton
        for canton_index, canton in enumerate(canton_links):
            canton_name = canton['name']
            canton_url = canton['url']
            
            self.session.logger.info(f"[{canton_index+1}/{len(canton_links)}] Processing: {canton_name}")
            
            # Check if canton was already processed
            if canton_name in self.processed_pages and len(self.processed_pages[canton_name]) > 0:
                self.session.logger.info(f"Resuming canton {canton_name}")
            
            # Fetch first page
            first_page_processed = (canton_name in self.processed_pages and 
                                  1 in self.processed_pages[canton_name])
            
            if not first_page_processed:
                response = self.session.fetch_page(canton_url)
                if not response:
                    self.session.logger.error(f"Failed to fetch canton page for {canton_name}")
                    continue
                
                # Get max pages
                max_page = self.get_max_page_number(response.text, canton_url)
                self.session.logger.info(f"Canton {canton_name} has {max_page} pages")
                
                # Process first page
                items_page1 = self.extract_items(response.text, canton_name)
                self.session.logger.info(f"Found {len(items_page1)} new items on page 1")
                
                all_items.extend(items_page1)
                total_count += len(items_page1)
                
                # Save progress
                self.save_progress(items_page1)
                self._mark_page_processed(canton_name, 1)
                
                self.session.logger.info(f"Overall progress: {total_count} items scraped")
            else:
                # Get max_page for resumption
                response = self.session.fetch_page(canton_url)
                max_page = self.get_max_page_number(response.text, canton_url) if response else 1
            
            # Process remaining pages
            for page_num in range(2, max_page + 1):
                if (canton_name in self.processed_pages and 
                    page_num in self.processed_pages[canton_name]):
                    self.session.logger.info(f"Skipping processed page {page_num}")
                    continue
                
                self.session.logger.info(f"Processing page {page_num}/{max_page} for {canton_name}")
                page_url = f"{canton_url}?page={page_num}"
                response = self.session.fetch_page(page_url)
                
                if not response:
                    self.session.logger.error(f"Failed to fetch page {page_num}")
                    continue
                
                items = self.extract_items(response.text, canton_name)
                self.session.logger.info(f"Found {len(items)} new items on page {page_num}")
                
                all_items.extend(items)
                total_count += len(items)
                
                # Save progress
                self.save_progress(items)
                self._mark_page_processed(canton_name, page_num)
                
                self.session.logger.info(f"Overall progress: {total_count} items scraped")
        
        # Standardize and save final output
        if all_items:
            standardized_data = standardize_csv_output(all_items, self.get_scraper_type())
            self.csv_manager.save_to_csv(standardized_data, self.output_file)
            self.session.logger.info(f"Scraping completed. Total items: {len(standardized_data)}")
        else:
            self.session.logger.info("No new items found")
        
        return len(all_items)