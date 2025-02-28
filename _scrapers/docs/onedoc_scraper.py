def clean_old_progress_files(current_page, keep_latest=3):
    """Delete older progress files, keeping only the most recent ones"""
    files_to_check = []
    
    # Generate names of potential progress files
    for page in range(5, current_page, 5):  # We save every 5 pages
        files_to_check.append(f"onedoc_progress_to_page{page}.csv")
    
    # Also check for any potential intermediate files
    for filename in os.listdir('.'):
        if filename.startswith('onedoc_progress_to_page') and filename.endswith('.csv'):
            if filename not in files_to_check:
                files_to_check.append(filename)
    
    # Sort files by page number
    files_to_check.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
    
    # Keep only the most recent files
    files_to_delete = files_to_check[:-keep_latest] if len(files_to_check) > keep_latest else []
    
    # Delete older files
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Deleted old progress file: {file}")
            except:
                print(f"Failed to delete file: {file}")
import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import random
import argparse
import json

# Base URL for the directory
base_url = "https://www.onedoc.ch/de/verzeichnis"

# Headers to make the request look like it's coming from a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7',
}

def scrape_page(url):
    """Scrape a single page of the directory"""
    print(f"Fetching URL: {url}")
    
    # Request the page
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all doctor entries
    directory_items = soup.find_all('div', class_='directory-item')
    print(f"Found {len(directory_items)} doctors on this page")
    
    # If no items found, check if this is actually a valid page
    if len(directory_items) == 0:
        # Check if this is an empty page or error page
        if "Keine Ergebnisse" in response.text or "404" in response.text:
            print("This appears to be an empty or error page")
            return []
    
    results = []
    for item in directory_items:
        # Extract doctor name
        name_element = item.find('a')
        name = name_element.text.strip() if name_element else "Unknown"
        
        # Extract profession
        profession_element = item.find('div', class_='directory-item-text-italic')
        profession = profession_element.text.strip() if profession_element else "Unknown"
        
        # Extract address
        address_element = item.find('div', class_='directory-item-text-normal')
        address = address_element.text.strip() if address_element else "Unknown"
        
        # Extract URL
        url = f"https://www.onedoc.ch{name_element['href']}" if name_element and name_element.has_attr('href') else "Unknown"
        
        # Store the data
        results.append({
            'name': name,
            'profession': profession,
            'address': address,
            'url': url
        })
    
    return results

def save_to_csv(data, filename):
    """Save data to a CSV file"""
    if not data:
        print("No data to save")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'profession', 'address', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Saved {len(data)} records to {filename}")
    print(f"File saved at: {os.path.abspath(filename)}")

def save_state(state, filename="scraper_state.json"):
    """Save current scraping state to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(state, f)
    print(f"Saved state to {filename}")

def load_state(filename="scraper_state.json"):
    """Load scraping state from a file"""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(f"Loaded state from {filename}")
        return state
    except:
        print(f"Failed to load state from {filename}")
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape the OneDoc directory')
    parser.add_argument('--start', type=int, default=None, help='Page to start scraping from')
    parser.add_argument('--end', type=int, default=553, help='Page to end scraping at')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds')
    parser.add_argument('--resume', action='store_true', help='Resume from last saved state')
    parser.add_argument('--keep', type=int, default=3, help='Number of recent progress files to keep')
    args = parser.parse_args()
    
    # Determine start page and load existing data if resuming
    all_doctors = []
    start_page = args.start or 1
    end_page = args.end
    
    if args.resume:
        state = load_state()
        if state:
            start_page = state.get('next_page', 1)
            
            # Load existing data
            data_file = state.get('data_file')
            if data_file and os.path.exists(data_file):
                try:
                    with open(data_file, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        all_doctors = list(reader)
                    print(f"Loaded {len(all_doctors)} existing records")
                except:
                    print(f"Failed to load existing data from {data_file}")
    
    print(f"Starting scrape from page {start_page} to {end_page}")
    
    # Setup progress tracking
    successful_pages = 0
    
    # Scrape pages from start to end
    for page in range(start_page, end_page + 1):
        url = base_url
        if page > 1:
            url = f"{base_url}/{page}"
        
        # Scrape the page
        doctors = scrape_page(url)
        
        if doctors:
            all_doctors.extend(doctors)
            successful_pages += 1
            
            # Save progress every 5 pages or on the last page
            if page % 5 == 0 or page == end_page:
                # Save progress file
                progress_file = f"onedoc_progress_to_page{page}.csv"
                save_to_csv(all_doctors, progress_file)
                
                # Always maintain a combined file that has all data so far
                combined_file = "onedoc_combined.csv"
                save_to_csv(all_doctors, combined_file)
                
                # Save state for potential resume
                save_state({
                    'next_page': page + 1,
                    'data_file': combined_file,
                    'successful_pages': page - start_page + 1,
                    'total_doctors': len(all_doctors)
                })
                
                # Clean up older progress files
                clean_old_progress_files(page, keep_latest=args.keep)
                
                print(f"Progress: {len(all_doctors)} doctors collected from {successful_pages} pages")
                print(f"Combined data always available in: {combined_file}")
        else:
            print(f"No doctors found on page {page}")
        
        # Add a small delay between requests
        if page < end_page:
            delay = random.uniform(max(0.5, args.delay - 0.5), args.delay + 0.5)
            print(f"Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)
    
    # Save final results
    final_file = "onedoc_complete.csv"
    save_to_csv(all_doctors, final_file)
    print(f"Total doctors found: {len(all_doctors)} from {successful_pages} pages")
    print(f"Final complete dataset saved to: {final_file}")
    print("Scraping completed successfully!")

if __name__ == "__main__":
    main()