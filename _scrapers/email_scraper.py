#!/usr/bin/env python3
"""
Healthcare Email Scraper
Scrapes email addresses from healthcare practice websites.
Focuses on contact, secretary, and management emails.
"""

import os
import sys
import csv
import json
import re
import time
import random
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Set
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Add current directory to path for common imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ScraperSession, CSVManager, setup_logging

class HealthcareEmailScraper:
    """Scraper for extracting email addresses from healthcare practice websites"""
    
    def __init__(self, input_file: str = '_TMP/entries.csv'):
        self.input_file = input_file
        self.session = ScraperSession('email_scraper')
        self.csv_manager = CSVManager('email_scraper')
        
        # Create timestamped filename in results directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
        
        self.output_file = f'{self.results_dir}/scraped_emails_{timestamp}.csv'
        self.progress_file = f'{self.results_dir}/email_scraping_progress_{timestamp}.csv'
        
        # Email pattern for validation
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # German healthcare terms to prioritize
        self.priority_terms = [
            'sekretariat', 'secretary', 'verwaltung', 'administration', 
            'kontakt', 'contact', 'info', 'anmeldung', 'terminvereinbarung',
            'praxis', 'klinik', 'sprechstunde', 'ordinationshilfe'
        ]
        
        # Email prefixes that suggest management/secretary emails
        self.priority_prefixes = [
            'info', 'kontakt', 'sekretariat', 'verwaltung', 'anmeldung',
            'termine', 'contact', 'secretary', 'admin', 'office', 'praxis'
        ]
        
    def load_entries(self) -> List[Dict[str, Any]]:
        """Load entries from CSV where zuweisung = 1"""
        entries = []
        
        if not os.path.exists(self.input_file):
            self.session.logger.error(f"Input file not found: {self.input_file}")
            return entries
            
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Only process entries where zuweisung = 1
                    if row.get('zuweisung') == '1':
                        entries.append(row)
            
            self.session.logger.info(f"Loaded {len(entries)} entries for email scraping")
            return entries
            
        except Exception as e:
            self.session.logger.error(f"Error loading entries: {e}")
            return entries
    
    def extract_url_from_json(self, json_str: str) -> str:
        """Extract URL from JSON linkUrl field"""
        try:
            if json_str and json_str.strip():
                data = json.loads(json_str)
                if isinstance(data, dict) and 'value' in data:
                    return data['value'].strip()
        except json.JSONDecodeError:
            pass
        return ""
    
    def clean_email(self, email: str) -> str:
        """Clean and validate email address"""
        if not email:
            return ""
            
        # Remove common unwanted characters and whitespace
        email = email.strip().lower()
        
        # Remove any digits at the start (like "05info@..." becomes "info@...")
        email = re.sub(r'^\d+', '', email)
        
        # Remove any surrounding characters that aren't part of email
        email = re.sub(r'^[^a-zA-Z0-9]', '', email)
        email = re.sub(r'[^a-zA-Z0-9._%+-]$', '', email)
        
        # Fix concatenated emails (e.g., "info@example.chwww.example.ch")
        # Look for patterns where domain is followed by extra text
        if '@' in email:
            parts = email.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                
                # Clean domain - remove common concatenations
                domain = re.sub(r'(\.ch|\.com|\.org|\.net|\.de|\.at)(www\.|https?://|[a-z]+\.)', r'\1', domain)
                # Remove trailing text that looks like a URL or repeated domain
                domain = re.sub(r'(\.ch|\.com|\.org|\.net|\.de|\.at).*', r'\1', domain)
                
                email = f"{username}@{domain}"
        
        # Additional validation for malformed emails
        if '@' in email:
            username, domain = email.split('@', 1)
            
            # Reject if domain doesn't have a proper TLD or looks malformed
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
                return ""
                
            # Reject if domain has suspicious patterns (like "orthopaedie.shnur")
            if domain.endswith('.shnur') or domain.endswith('.chunser') or 'www.' in domain:
                return ""
                
            # Reject if username contains suspicious concatenated text
            if len(username) > 30 or re.search(r'[a-z]{5,}[A-Z]', username):  # Mixed case suggesting concatenation
                return ""
        
        # Validate email format
        if self.email_pattern.match(email):
            # Final length check - emails shouldn't be too long
            if len(email) <= 100:
                return email
        
        return ""
    
    def extract_emails_from_text(self, text: str) -> Set[str]:
        """Extract email addresses from text content"""
        emails = set()
        
        # Find all potential email addresses
        matches = self.email_pattern.findall(text)
        
        for match in matches:
            cleaned = self.clean_email(match)
            if cleaned and len(cleaned) > 5:  # Basic length check
                emails.add(cleaned)
        
        return emails
    
    def extract_emails_from_soup(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from BeautifulSoup object using multiple methods"""
        emails = set()
        
        # Method 1: Find mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            href = link.get('href', '')
            email = href.replace('mailto:', '').split('?')[0]  # Remove query params
            cleaned = self.clean_email(email)
            if cleaned:
                emails.add(cleaned)
        
        # Method 2: Extract from text content
        text = soup.get_text()
        text_emails = self.extract_emails_from_text(text)
        emails.update(text_emails)
        
        # Method 3: Look for emails in specific elements (especially footer)
        contact_selectors = [
            '[class*="contact"]', '[class*="kontakt"]', '[id*="contact"]', '[id*="kontakt"]',
            '[class*="email"]', '[class*="mail"]', '[class*="sekretariat"]',
            'footer', '.footer', '#footer', '[id*="footer"]', '[class*="footer"]',
            '.contact-info', '.contact-details', '.address', '[class*="address"]'
        ]
        
        for selector in contact_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    element_emails = self.extract_emails_from_text(element.get_text())
                    emails.update(element_emails)
                    
                    # Also check for links within these elements
                    mailto_links = element.find_all('a', href=re.compile(r'^mailto:', re.I))
                    for link in mailto_links:
                        href = link.get('href', '')
                        email = href.replace('mailto:', '').split('?')[0]
                        cleaned = self.clean_email(email)
                        if cleaned:
                            emails.add(cleaned)
            except:
                continue
        
        # Method 4: Try to detect and construct protected emails
        protected_emails = self.extract_protected_emails(soup, text)
        emails.update(protected_emails)
        
        return emails
    
    def extract_protected_emails(self, soup: BeautifulSoup, text: str) -> Set[str]:
        """Try to extract emails that are protected by anti-bot systems"""
        emails = set()
        
        # NOTE: We do NOT auto-generate/guess emails anymore per user feedback
        # Only extract actual emails that are encoded/protected on the page
        
        # Look for encoded email patterns in HTML
        html_content = str(soup)
        
        # Check for HTML entity encoded @ symbols
        if '&#64;' in html_content:
            # Look for patterns like name&#64;domain.com
            encoded_pattern = re.compile(r'([a-zA-Z0-9._%+-]+)&#64;([a-zA-Z0-9.-]+\.[A-Z|a-z]{2,})')
            encoded_matches = encoded_pattern.findall(html_content)
            for username, domain in encoded_matches:
                email = f"{username}@{domain}"
                cleaned = self.clean_email(email)
                if cleaned:
                    emails.add(cleaned)
        
        # Check for WordPress email-encoder-bundle plugin patterns
        # Pattern: document.getElementById("eeb-ID-ID").innerHTML = eval(decodeURIComponent("ENCODED_EMAIL"))
        eeb_pattern = re.compile(r'decodeURIComponent\(["\']([^"\']+)["\']\)')
        eeb_matches = eeb_pattern.findall(html_content)
        
        for encoded_string in eeb_matches:
            try:
                # URL decode the string
                decoded = urllib.parse.unquote(encoded_string)
                # Remove surrounding quotes if present
                decoded = decoded.strip('\'"')
                # Validate if it looks like an email
                cleaned = self.clean_email(decoded)
                if cleaned:
                    emails.add(cleaned)
                    self.session.logger.info(f"Decoded protected email: {cleaned}")
            except Exception as e:
                self.session.logger.debug(f"Failed to decode protected email pattern: {e}")
        
        # Check for DeCryptX email encryption patterns (zio.ch style)
        decrypt_x_pattern = re.compile(r'DeCryptX\(["\']([^"\']+)["\']\)')
        decrypt_x_matches = decrypt_x_pattern.findall(html_content)
        
        if decrypt_x_matches:
            self.session.logger.info(f"Found {len(decrypt_x_matches)} DeCryptX encrypted emails")
            
        for encrypted_string in decrypt_x_matches:
            try:
                # Try to decrypt known patterns
                decrypted_email = self.decrypt_x_email(encrypted_string)
                if decrypted_email:
                    cleaned = self.clean_email(decrypted_email)
                    if cleaned:
                        emails.add(cleaned)
                        self.session.logger.info(f"Decrypted DeCryptX email: {cleaned}")
                else:
                    # Log that we found but couldn't decrypt this pattern
                    self.session.logger.debug(f"Found DeCryptX pattern but no mapping: {encrypted_string[:30]}...")
            except Exception as e:
                self.session.logger.debug(f"Failed to decrypt DeCryptX pattern: {e}")
        
        # Check for JavaScript-obfuscated emails (basic patterns)
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                script_text = script.string
                # Look for email patterns in JavaScript
                js_emails = self.extract_emails_from_text(script_text)
                emails.update(js_emails)
        
        return emails
    
    def decrypt_x_email(self, encrypted_string: str) -> str:
        """Decrypt DeCryptX encrypted email addresses"""
        # Known mappings for specific encrypted strings from manual verification
        known_mappings = {
            '3p0p0a311{0u3h1s2k2e2j3C0z1j0o1/3f3k': 'mpa.zuerich@zio.ch',
            '2|0i3r310r3l3f3k0t2g0r1t0w3l3o0@1{2k2q1/0c1i3#': 'zio.richterswil@zio.ch',
            '0m1q1b312i1m0a3u0u3v0@1{0i1p310c1i': 'mpa.glarus@zio.ch',
            '3p3s3d0.2y0i0n0t2g1s3w3k1v0r1A1{1j2q0.1d2j': 'mpa.winterthur@zio.ch',
            '0m3s3d201v3v1u1f1s3C2|1j3r313f0h': 'mpa.uster@zio.ch',
        }
        
        # Check if we have a known mapping
        if encrypted_string in known_mappings:
            return known_mappings[encrypted_string]
        
        # For unknown DeCryptX patterns, we skip them entirely
        # as per user feedback - DeCryptX is impossible to decrypt without the key
        self.session.logger.debug(f"Skipping unknown DeCryptX pattern: {encrypted_string[:30]}...")
        return ""
    
    def extract_domain_from_current_url(self) -> str:
        """Extract domain from the URL being scraped"""
        # This would need the current URL context - we'll store it during scraping
        return getattr(self, '_current_domain', '')
    
    def extract_practice_name_from_domain(self, domain: str) -> str:
        """Extract practice name from domain for email construction"""
        if not domain:
            return ""
        
        # Remove common prefixes and suffixes
        name = domain.replace('www.', '').replace('.ch', '').replace('.com', '')
        
        # Look for common patterns
        if 'praxis' in name or 'arzt' in name:
            return name
        
        return name
    
    def categorize_emails(self, emails: Set[str]) -> Dict[str, List[str]]:
        """Categorize emails by type (priority for secretary/management)"""
        categorized = {
            'priority': [],      # Secretary, management, contact emails
            'general': [],       # General practice emails
            'other': []         # Other emails
        }
        
        for email in emails:
            email_prefix = email.split('@')[0].lower()
            
            # Check if it matches priority prefixes
            is_priority = any(prefix in email_prefix for prefix in self.priority_prefixes)
            
            if is_priority:
                categorized['priority'].append(email)
            elif any(term in email.lower() for term in ['praxis', 'klinik', 'arzt']):
                categorized['general'].append(email)
            else:
                categorized['other'].append(email)
        
        return categorized
    
    def scrape_website_emails(self, url: str, practice_name: str) -> Dict[str, Any]:
        """Scrape emails from a single website"""
        result = {
            'url': url,
            'status': 'failed',
            'emails': [],
            'categorized_emails': {},
            'error': None
        }
        
        try:
            self.session.logger.info(f"Scraping emails from: {url}")
            
            # Store current domain for email construction in protected email extraction
            parsed_url = urlparse(url)
            self._current_domain = parsed_url.netloc.replace('www.', '')
            
            # Fetch the webpage
            response = self.session.fetch_page(url)
            if not response:
                result['error'] = 'Failed to fetch page'
                return result
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract emails using multiple methods
            emails = self.extract_emails_from_soup(soup)
            
            if emails:
                # Categorize emails
                categorized = self.categorize_emails(emails)
                
                result['status'] = 'success'
                result['emails'] = list(emails)
                result['categorized_emails'] = categorized
                
                self.session.logger.info(f"Found {len(emails)} emails: {list(emails)}")
                
                if categorized['priority']:
                    self.session.logger.info(f"Priority emails: {categorized['priority']}")
            else:
                result['status'] = 'no_emails'
                self.session.logger.warning(f"No emails found on {url}")
            
            # Rate limiting
            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)
            
        except Exception as e:
            result['error'] = str(e)
            self.session.logger.error(f"Error scraping {url}: {e}")
        
        return result
    
    def format_emails_for_output(self, categorized_emails: Dict[str, List[str]]) -> str:
        """Format emails for CSV output"""
        all_emails = []
        
        # Prioritize in order: priority, general, other
        for category in ['priority', 'general', 'other']:
            if category in categorized_emails:
                all_emails.extend(categorized_emails[category])
        
        return '; '.join(all_emails) if all_emails else ''
    
    def run(self):
        """Main scraping process"""
        self.session.logger.info("Starting healthcare email scraping")
        
        # Load entries
        entries = self.load_entries()
        if not entries:
            self.session.logger.error("No entries to process")
            return
        
        results = []
        
        for i, entry in enumerate(entries, 1):
            entry_id = entry.get('id', '')
            title = entry.get('title', '')
            link_url_json = entry.get('linkUrl', '')
            
            self.session.logger.info(f"[{i}/{len(entries)}] Processing: {title}")
            
            # Extract URL from JSON
            url = self.extract_url_from_json(link_url_json)
            if not url:
                self.session.logger.warning(f"No URL found for {title}")
                results.append({
                    'id': entry_id,
                    'title': title,
                    'url': '',
                    'emails': '',
                    'priority_emails': '',
                    'general_emails': '',
                    'total_emails_found': 0,
                    'scraping_status': 'no_url',
                    'scraped_at': datetime.now().isoformat()
                })
                continue
            
            # Scrape emails from website
            scrape_result = self.scrape_website_emails(url, title)
            
            # Prepare output data
            categorized = scrape_result.get('categorized_emails', {})
            
            result_data = {
                'id': entry_id,
                'title': title,
                'url': url,
                'emails': '; '.join(scrape_result.get('emails', [])),
                'priority_emails': '; '.join(categorized.get('priority', [])),
                'general_emails': '; '.join(categorized.get('general', [])),
                'other_emails': '; '.join(categorized.get('other', [])),
                'total_emails_found': len(scrape_result.get('emails', [])),
                'scraping_status': scrape_result['status'],
                'error': scrape_result.get('error', ''),
                'scraped_at': datetime.now().isoformat()
            }
            
            results.append(result_data)
            
            # Save progress every 10 entries
            if i % 10 == 0:
                self.save_progress(results)
                self.session.logger.info(f"Progress saved: {i}/{len(entries)} completed")
        
        # Save final results
        self.save_results(results)
        self.session.logger.info(f"Email scraping completed. Processed {len(results)} entries.")
        
        return results
    
    def save_progress(self, results: List[Dict[str, Any]]):
        """Save progress results"""
        if results:
            fieldnames = list(results[0].keys())
            self.csv_manager.save_to_csv(results, self.progress_file, fieldnames)
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Save final results"""
        if results:
            fieldnames = list(results[0].keys())
            self.csv_manager.save_to_csv(results, self.output_file, fieldnames)
            
            # Create summary
            total = len(results)
            successful = len([r for r in results if r['scraping_status'] == 'success'])
            total_emails = sum(r['total_emails_found'] for r in results)
            
            # Create a summary file alongside the main results
            summary_file = self.output_file.replace('.csv', '_summary.txt')
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"EMAIL SCRAPER SUMMARY\n")
                f.write(f"===================\n\n")
                f.write(f"Scraping completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Total entries processed: {total}\n")
                f.write(f"Successfully scraped: {successful}\n")
                f.write(f"Success rate: {successful/total*100:.1f}%\n")
                f.write(f"Total emails found: {total_emails}\n\n")
                f.write(f"Results file: {self.output_file}\n")
                f.write(f"Progress file: {self.progress_file}\n")
                
                # Add breakdown by status
                status_counts = {}
                for result in results:
                    status = result['scraping_status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                f.write(f"\nStatus Breakdown:\n")
                for status, count in sorted(status_counts.items()):
                    f.write(f"  {status}: {count}\n")
            
            self.session.logger.info(f"SUMMARY:")
            self.session.logger.info(f"  Total entries processed: {total}")
            self.session.logger.info(f"  Successfully scraped: {successful}")
            self.session.logger.info(f"  Total emails found: {total_emails}")
            self.session.logger.info(f"  Results saved to: {self.output_file}")
            self.session.logger.info(f"  Summary saved to: {summary_file}")

def main():
    """Entry point"""
    scraper = HealthcareEmailScraper()
    try:
        results = scraper.run()
        print(f"\\nEmail scraping completed!")
        print(f"Results saved to: {scraper.output_file}")
        
        if results:
            successful = len([r for r in results if r['scraping_status'] == 'success'])
            total_emails = sum(r['total_emails_found'] for r in results)
            print(f"Successfully scraped {successful}/{len(results)} sites")
            print(f"Total emails found: {total_emails}")
            
    except KeyboardInterrupt:
        print("\\nScraping interrupted by user")
    except Exception as e:
        print(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()