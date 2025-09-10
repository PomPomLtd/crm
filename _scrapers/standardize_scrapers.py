#!/usr/bin/env python3
"""
Scraper Standardization Utility
Creates unified versions of all scrapers that use common utilities.
"""

import os
import shutil
from pathlib import Path

# Template for a standardized scraper
SCRAPER_TEMPLATE = '''#!/usr/bin/env python3
"""
{scraper_name} Data Scraper (Unified Version)
Scrapes {scraper_description} using unified common utilities.
"""

import os
import sys
import csv
import re
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Set
from bs4 import BeautifulSoup

# Add parent directory to path for common imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import ScraperSession, CSVManager, get_scraper_config, standardize_csv_output

class {class_name}Scraper:
    """{{scraper_description}} scraper using unified utilities"""
    
    def __init__(self):
        self.config = get_scraper_config('{scraper_key}')
        self.session = ScraperSession('{scraper_key}')
        self.csv_manager = CSVManager('{scraper_key}')
        
        self.overview_url = self.config['url']
        self.output_file = self.config['output_file']
        
        # Progress tracking
        self.processed_pages = self._load_processed_pages()
        self.scraped_urls = self._load_scraped_urls()
        
    def _load_processed_pages(self) -> Dict[str, Set[int]]:
        """Load already processed pages from tracking file"""
        processed = {{}}
        tracking_file = '{scraper_key}_processed_pages.csv'
        
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
        progress_file = '{scraper_key}_progress.csv'
        
        if os.path.exists(progress_file):
            data = self.csv_manager.load_from_csv(progress_file)
            for row in data:
                scraped_urls.add(row.get('url', ''))
                
        self.session.logger.info(f"Found {{len(scraped_urls)}} already scraped items")
        return scraped_urls
    
    def _mark_page_processed(self, canton: str, page_num: int):
        """Mark a page as processed in tracking file"""
        with open('{scraper_key}_processed_pages.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([canton, page_num])
    
    def extract_canton_links(self, html: str) -> List[Dict[str, str]]:
        """Extract links to canton pages from overview page"""
        if not html:
            return []
        
        canton_links = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for canton links (adjust selector as needed)
        canton_headings = soup.select('.top-states h2 a')
        
        for heading in canton_headings:
            canton_url = "https://www.onedoc.ch" + heading['href']
            canton_name = heading.text.strip()
            canton_links.append({{'name': canton_name, 'url': canton_url}})
        
        self.session.logger.info(f"Found {{len(canton_links)}} canton links")
        return canton_links
    
    def get_max_page_number(self, html: str, canton_url: str) -> int:
        """Determine maximum number of pages from pagination"""
        if not html:
            return 1
        
        soup = BeautifulSoup(html, 'html.parser')
        pagination = soup.find('ul', class_='pagination')
        
        if not pagination:
            return 1
        
        # Extract page numbers
        visible_pages = []
        for link in pagination.find_all('a'):
            try:
                page_num = int(link.text.strip())
                visible_pages.append(page_num)
            except (ValueError, TypeError):
                continue
        
        return max(visible_pages) if visible_pages else 1
    
    def extract_item_details(self, url: str, item_name: str, index: int, total: int) -> Dict[str, Any]:
        """Extract detailed information from item page"""
        details = {{
            'phone_number': "",
            'professions': []
        }}
        
        self.session.logger.info(f"[{{index}}/{{total}}] Getting details for: {{item_name}}")
        
        response = self.session.fetch_page(url)
        if not response:
            return details
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract phone number
        phone_link = soup.select_one('a[href^="tel:"]')
        if phone_link:
            details['phone_number'] = phone_link.text.strip()
        
        # Extract professions/specialties
        profession_chips = soup.select('.od-profile-chip')
        if profession_chips:
            details['professions'] = [chip.text.strip() for chip in profession_chips]
        
        # Rate limiting
        time.sleep(random.uniform(0.5, 2))
        
        return details
    
    def extract_items(self, html: str, canton_name: str) -> List[Dict[str, Any]]:
        """Extract item data from canton page"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='directory-item')
        
        self.session.logger.info(f"Found {{len(items)}} items on this page")
        
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
            street = ""
            postal_code = ""
            city = ""
            
            if address and ", " in address:
                address_parts = address.split(", ")
                street = address_parts[0]
                
                if len(address_parts) > 1:
                    postal_city = address_parts[1]
                    postal_match = re.search(r'(\\d{{4}})\\s+(.*)', postal_city)
                    if postal_match:
                        postal_code = postal_match.group(1)
                        city = postal_match.group(2)
                    else:
                        city = postal_city
            
            # Create item data
            item_data = {{
                'name': name,
                'address': address,
                'street': street,
                'postal_code': postal_code,
                'city': city,
                'phone': "",
                'email': "",
                'website': item_url,
                'specialty': "",
                'source_url': item_url,
                'scraped_at': datetime.now().isoformat()
            }}
            
            # Get additional details
            if item_url:
                details = self.extract_item_details(item_url, name, index, len(items))
                item_data['phone'] = details['phone_number']
                item_data['specialty'] = ", ".join(details['professions'])
            
            extracted_items.append(item_data)
            self.scraped_urls.add(item_url)
        
        return extracted_items
    
    def save_progress(self, data: List[Dict[str, Any]]):
        """Save progress data"""
        if not data:
            return
        
        progress_file = '{scraper_key}_progress.csv'
        file_exists = os.path.isfile(progress_file)
        
        with open(progress_file, 'a', newline='', encoding='utf-8') as f:
            if data:
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(data)
        
        self.session.logger.info(f"Saved progress: {{len(data)}} items")
    
    def run(self):
        """Main scraping logic"""
        all_items = []
        
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
            
            self.session.logger.info(f"[{{canton_index+1}}/{{len(canton_links)}}] Processing: {{canton_name}}")
            
            # Fetch canton page
            response = self.session.fetch_page(canton_url)
            if not response:
                continue
            
            # Get max pages
            max_page = self.get_max_page_number(response.text, canton_url)
            
            # Process all pages
            for page_num in range(1, max_page + 1):
                if page_num == 1:
                    page_html = response.text
                else:
                    page_url = f"{{canton_url}}?page={{page_num}}"
                    page_response = self.session.fetch_page(page_url)
                    page_html = page_response.text if page_response else None
                
                if page_html:
                    items = self.extract_items(page_html, canton_name)
                    all_items.extend(items)
                    self.save_progress(items)
        
        # Standardize and save final output
        if all_items:
            standardized_data = standardize_csv_output(all_items, '{scraper_type}')
            self.csv_manager.save_to_csv(standardized_data, self.output_file)
            self.session.logger.info(f"Scraping completed. Total items: {{len(standardized_data)}}")

def main():
    """Entry point"""
    scraper = {class_name}Scraper()
    scraper.run()

if __name__ == "__main__":
    main()
'''

def create_standardized_scraper(scraper_key: str, config: dict) -> str:
    """Create a standardized scraper from template"""
    
    # Generate class name from scraper key
    class_name = ''.join(word.capitalize() for word in scraper_key.replace('-', ' ').split())
    
    # Map scraper types
    scraper_type_map = {
        'hospitals': 'hospital',
        'clinics': 'clinic', 
        'group-practices': 'group_practice',
        'medical-clinics': 'medical_clinic',
        'medical-centers': 'medical_center',
        'complete-directory': 'healthcare_provider'
    }
    
    scraper_type = scraper_type_map.get(scraper_key, 'healthcare_provider')
    
    return SCRAPER_TEMPLATE.format(
        scraper_name=config['name'],
        scraper_description=config['description'].lower(),
        scraper_key=scraper_key,
        class_name=class_name,
        scraper_type=scraper_type
    )

def main():
    """Create standardized versions of all scrapers"""
    # Load config
    import json
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("Creating standardized scrapers...")
    
    for scraper_key, scraper_config in config['scrapers'].items():
        print(f"Processing {scraper_key}...")
        
        # Create standardized version
        standardized_code = create_standardized_scraper(scraper_key, scraper_config)
        
        # Determine output filename
        output_filename = f"{scraper_config['main_script'].replace('.py', '-unified.py')}"
        
        # Write file
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(standardized_code)
        
        # Make executable
        os.chmod(output_filename, 0o755)
        
        print(f"Created: {output_filename}")
    
    print("\\nAll standardized scrapers created!")
    print("\\nNext steps:")
    print("1. Test the unified scrapers")
    print("2. Replace old scrapers with unified versions")
    print("3. Update config.json to point to unified scripts")

if __name__ == "__main__":
    main()