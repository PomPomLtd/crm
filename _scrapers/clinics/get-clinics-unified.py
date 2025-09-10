#!/usr/bin/env python3
"""
Clinics Data Scraper (Unified Version)
Scrapes swiss clinics from onedoc.ch using unified base scraper class.
"""

import os
import sys
import time
import random
from typing import Dict, Any
from bs4 import BeautifulSoup

# Add parent directory to path for common imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_scraper import BaseHealthcareScraper

class ClinicsScraper(BaseHealthcareScraper):
    """Clinics data scraper using unified base class"""
    
    def __init__(self):
        super().__init__('clinics')
    
    def get_scraper_type(self) -> str:
        """Return the type string for standardization"""
        return 'clinic'
    
    def extract_item_details(self, url: str, item_name: str, index: int, total: int) -> Dict[str, Any]:
        """Extract detailed information from swiss clinics from onedoc.ch page"""
        details = {
            'phone_number': "",
            'professions': [],
            'email': "",
            'website': ""
        }
        
        self.session.logger.info(f"[{index}/{total}] Getting details for: {item_name}")
        
        response = self.session.fetch_page(url)
        if not response:
            self.session.logger.warning(f"Failed to get details for {item_name}")
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
        
        # Extract email if available
        email_links = soup.select('a[href^="mailto:"]')
        if email_links:
            details['email'] = email_links[0]['href'].replace('mailto:', '')
        
        # Extract additional website if different from item URL
        website_links = soup.select('a[href^="http"]:not([href^="mailto"]):not([href^="tel"])')
        for link in website_links:
            href = link.get('href', '')
            if href and 'onedoc.ch' not in href:
                details['website'] = href
                break
        
        # Rate limiting
        delay = random.uniform(0.5, 2)
        time.sleep(delay)
        
        return details

def main():
    """Entry point"""
    scraper = ClinicsScraper()
    try:
        result = scraper.run()
        print(f"Scraping completed. Processed {result} swiss clinics from onedoc.ch.")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        scraper.session.logger.error(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()
