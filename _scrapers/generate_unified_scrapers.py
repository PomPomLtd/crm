#!/usr/bin/env python3
"""
Generate unified scrapers for all scraper types.
Creates consistent, maintainable scrapers using the base class.
"""

import os
import json
from pathlib import Path

# Template for unified scrapers
UNIFIED_SCRAPER_TEMPLATE = '''#!/usr/bin/env python3
"""
{scraper_name} Data Scraper (Unified Version)
Scrapes {description} using unified base scraper class.
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

class {class_name}Scraper(BaseHealthcareScraper):
    """{scraper_name} data scraper using unified base class"""
    
    def __init__(self):
        super().__init__('{scraper_key}')
    
    def get_scraper_type(self) -> str:
        """Return the type string for standardization"""
        return '{scraper_type}'
    
    def extract_item_details(self, url: str, item_name: str, index: int, total: int) -> Dict[str, Any]:
        """Extract detailed information from {description} page"""
        details = {{
            'phone_number': "",
            'professions': [],
            'email': "",
            'website': ""
        }}
        
        self.session.logger.info(f"[{{index}}/{{total}}] Getting details for: {{item_name}}")
        
        response = self.session.fetch_page(url)
        if not response:
            self.session.logger.warning(f"Failed to get details for {{item_name}}")
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
    scraper = {class_name}Scraper()
    try:
        result = scraper.run()
        print(f"Scraping completed. Processed {{result}} {description}.")
    except KeyboardInterrupt:
        print("\\nScraping interrupted by user")
    except Exception as e:
        scraper.session.logger.error(f"Scraping failed: {{e}}")
        raise

if __name__ == "__main__":
    main()
'''

def generate_class_name(scraper_key: str) -> str:
    """Generate a class name from scraper key"""
    # Split on hyphens and capitalize each word
    words = scraper_key.replace('-', ' ').split()
    return ''.join(word.capitalize() for word in words)

def get_scraper_type(scraper_key: str) -> str:
    """Get standardized scraper type for data categorization"""
    type_map = {
        'hospitals': 'hospital',
        'clinics': 'clinic',
        'group-practices': 'group_practice',
        'medical-clinics': 'medical_clinic',
        'medical-centers': 'medical_center',
        'complete-directory': 'healthcare_provider'
    }
    return type_map.get(scraper_key, 'healthcare_provider')

def create_unified_scraper(scraper_key: str, config: dict) -> str:
    """Create unified scraper code from template"""
    class_name = generate_class_name(scraper_key)
    scraper_type = get_scraper_type(scraper_key)
    
    return UNIFIED_SCRAPER_TEMPLATE.format(
        scraper_name=config['name'],
        description=config['description'].lower(),
        scraper_key=scraper_key,
        class_name=class_name,
        scraper_type=scraper_type
    )

def main():
    """Generate all unified scrapers"""
    print("Generating unified scrapers...")
    
    # Load configuration
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    generated_count = 0
    
    for scraper_key, scraper_config in config['scrapers'].items():
        print(f"\\nProcessing {scraper_key}...")
        
        # Determine the directory and filename
        main_script = scraper_config['main_script']
        script_dir = os.path.dirname(main_script)
        script_name = os.path.basename(main_script)
        
        # Generate unified filename
        unified_name = script_name.replace('.py', '-unified.py')
        unified_path = os.path.join(script_dir, unified_name)
        
        # Create directory if it doesn't exist
        os.makedirs(script_dir, exist_ok=True)
        
        # Generate unified scraper code
        unified_code = create_unified_scraper(scraper_key, scraper_config)
        
        # Write the file
        with open(unified_path, 'w', encoding='utf-8') as f:
            f.write(unified_code)
        
        # Make executable
        os.chmod(unified_path, 0o755)
        
        print(f"✅ Created: {unified_path}")
        generated_count += 1
    
    print(f"\\n🎉 Generated {generated_count} unified scrapers!")
    print("\\nAll scrapers now use consistent:")
    print("- Base class inheritance")
    print("- Error handling and logging") 
    print("- Progress tracking and resumption")
    print("- Rate limiting and retry logic")
    print("- Standardized data output")
    
    print("\\nTo test a unified scraper:")
    print("python hospitals/get-hospitals-unified.py")
    print("\\nTo use via manager:")
    print("python scraper_manager.py run hospitals")

if __name__ == "__main__":
    main()