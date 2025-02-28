import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import random
import socket
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Base URL for the medical practices overview page
overview_url = "https://www.onedoc.ch/de/medizinische-praxis"  # Updated URL

# Headers to make the request look like it's coming from a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Create a session with retry logic
def create_session():
    session = requests.Session()
    # Configure retry strategy
    retry_strategy = Retry(
        total=5,  # Maximum number of retries
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["GET"],
        backoff_factor=2,  # Exponential backoff factor
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        # Try to resolve Google's DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except (socket.timeout, socket.gaierror, OSError):
        return False

def fetch_page(url, max_retries=3, retry_delay=10, check_redirect=False):
    """Fetch HTML content from a URL with retry logic, optionally checking for redirects"""
    print(f"Fetching URL: {url}")
    
    # Check internet connection first
    if not check_internet_connection():
        print("No internet connection detected. Waiting before retry...")
        time.sleep(retry_delay)
        if not check_internet_connection():
            print("Still no internet connection. Please check your network.")
            return None
    
    session = create_session()
    
    # Try to fetch the page with retries
    for attempt in range(max_retries):
        try:
            # Use allow_redirects=True to follow redirects
            response = session.get(url, headers=headers, timeout=20, allow_redirects=True)
            response.raise_for_status()
            print(f"Response status: {response.status_code}")
            
            # If we're checking for redirects, see if we've been redirected to a different page
            if check_redirect:
                final_url = response.url
                # Check if we've been redirected to page 1 or the base URL
                if "page=1" in final_url or "?page=" not in final_url:
                    print(f"Redirect detected! URL {url} redirected to {final_url}")
                    return None  # Return None to indicate this page doesn't exist
            
            return response.text
        except (requests.RequestException, socket.gaierror, socket.timeout) as e:
            print(f"Error on attempt {attempt+1}/{max_retries}: {e}")
            
            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = retry_delay * (2 ** attempt)
                print(f"Waiting {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
                
                # Check internet connection again before retry
                if not check_internet_connection():
                    print("No internet connection detected. Waiting for connection...")
                    # Wait up to 2 minutes for internet connection
                    for _ in range(12):  # 12 * 10s = 120s = 2 minutes
                        time.sleep(10)
                        if check_internet_connection():
                            print("Internet connection restored!")
                            break
                    else:
                        print("Still no internet connection after waiting.")
            else:
                print(f"Failed to fetch {url} after {max_retries} attempts")
    
    return None

def extract_canton_links(html):
    """Extract links to canton pages from the overview page"""
    if not html:
        return []
    
    canton_links = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all canton headings
    canton_headings = soup.select('.top-states h2 a')
    
    for heading in canton_headings:
        canton_url = "https://www.onedoc.ch" + heading['href']
        canton_name = heading.text.strip()
        canton_links.append({'name': canton_name, 'url': canton_url})
    
    print(f"Found {len(canton_links)} canton links")
    return canton_links

def get_max_page_number(html, canton_url):
    """Determine the maximum number of pages by examining the pagination on different pages"""
    if not html:
        return 1
    
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find('ul', class_='pagination')
    
    if not pagination:
        print("No pagination found, assuming single page")
        return 1
    
    # First get all visible page numbers from the first page
    visible_pages = []
    page_links = pagination.find_all('a')
    for link in page_links:
        try:
            page_num = int(link.text.strip())
            visible_pages.append(page_num)
        except (ValueError, TypeError):
            continue
    
    if not visible_pages:
        return 1
    
    # Get the highest visible page number from the first page
    highest_visible = max(visible_pages)
    print(f"Highest visible page number on first page is {highest_visible}")
    
    # Now fetch the page with the highest visible number to see more pages
    next_check_url = f"{canton_url}?page={highest_visible}"
    print(f"Checking pagination on page {highest_visible}...")
    next_page_html = fetch_page(next_check_url)
    
    if not next_page_html:
        print(f"Could not fetch page {highest_visible}. Using it as the maximum.")
        return highest_visible
    
    # Parse the pagination from this page
    next_soup = BeautifulSoup(next_page_html, 'html.parser')
    next_pagination = next_soup.find('ul', class_='pagination')
    
    if not next_pagination:
        print(f"No pagination found on page {highest_visible}. Using it as the maximum.")
        return highest_visible
    
    # Get all visible page numbers from this next page
    next_visible_pages = []
    next_page_links = next_pagination.find_all('a')
    for link in next_page_links:
        try:
            page_num = int(link.text.strip())
            next_visible_pages.append(page_num)
        except (ValueError, TypeError):
            continue
    
    # If we found new page numbers, repeat the process
    if next_visible_pages and max(next_visible_pages) > highest_visible:
        new_highest = max(next_visible_pages)
        print(f"Found higher page number: {new_highest} on page {highest_visible}")
        
        # If the new highest is significantly higher, we might need another iteration
        while True:
            previous_highest = new_highest
            check_url = f"{canton_url}?page={new_highest}"
            print(f"Checking pagination on page {new_highest}...")
            check_html = fetch_page(check_url)
            
            if not check_html:
                print(f"Could not fetch page {new_highest}. Using previous highest: {previous_highest}.")
                return previous_highest
            
            check_soup = BeautifulSoup(check_html, 'html.parser')
            check_pagination = check_soup.find('ul', class_='pagination')
            
            if not check_pagination:
                print(f"No pagination found on page {new_highest}. Using it as the maximum.")
                return new_highest
            
            check_visible_pages = []
            for link in check_pagination.find_all('a'):
                try:
                    page_num = int(link.text.strip())
                    check_visible_pages.append(page_num)
                except (ValueError, TypeError):
                    continue
            
            # If we don't find any higher page numbers, we've reached the max
            if not check_visible_pages or max(check_visible_pages) <= new_highest:
                print(f"No higher page numbers found. Maximum page is {new_highest}.")
                return new_highest
            
            # If we found higher page numbers, update and continue
            if max(check_visible_pages) > new_highest:
                new_highest = max(check_visible_pages)
                print(f"Found even higher page number: {new_highest}")
                
                # If we're not making significant progress, we might be in a loop
                if new_highest - previous_highest < 5:
                    # Do a direct check of a page well beyond this to verify
                    test_page = new_highest + 10
                    test_url = f"{canton_url}?page={test_page}"
                    print(f"Validating by directly checking page {test_page}...")
                    test_html = fetch_page(test_url)
                    
                    if not test_html:
                        print(f"Page {test_page} does not exist. Continuing with incremental search.")
                    else:
                        # The page exists, check its content
                        test_soup = BeautifulSoup(test_html, 'html.parser')
                        test_items = test_soup.find_all('div', class_='directory-item')
                        
                        if test_items:
                            print(f"Page {test_page} exists and has {len(test_items)} items!")
                            # There are legitimately more pages, continue from this higher number
                            new_highest = test_page
                            continue
        
        return new_highest
    else:
        print(f"No higher page numbers found. Maximum page is {highest_visible}.")
        return highest_visible

def extract_practice_details(url, practice_name, practice_index, total_practices):
    """Extract additional details (phone number and professions) from a practice detail page"""
    details = {
        'phone_number': "Not available",
        'professions': []
    }
    
    # Display progress for detail page
    print(f"[{practice_index}/{total_practices}] Getting details for: {practice_name}")
    
    # Fetch the detail page
    html = fetch_page(url)
    if not html:
        print(f"  ❌ Failed to get details for {practice_name}")
        return details
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract phone number - look for the pattern in a paragraph with phone link
    phone_link = soup.select_one('a[href^="tel:"]')
    if phone_link:
        details['phone_number'] = phone_link.text.strip()
        print(f"  ✓ Found phone: {details['phone_number']}")
    else:
        print(f"  ⚠ No phone number found")
    
    # Extract professions from the chips
    profession_chips = soup.select('.od-profile-chip')
    if profession_chips:
        details['professions'] = [chip.text.strip() for chip in profession_chips]
        print(f"  ✓ Found {len(details['professions'])} professions")
    else:
        print(f"  ⚠ No professions found")
    
    return details

def extract_practices(html, canton_name):
    """Extract practice data from a canton page"""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    practice_items = soup.find_all('div', class_='directory-item')
    
    total_items = len(practice_items)
    print(f"Found {total_items} practices on this page")
    
    practices = []
    for index, item in enumerate(practice_items, 1):
        # Extract practice name and URL
        name_element = item.find('a')
        name = name_element.text.strip() if name_element else "Unknown"
        practice_url = "https://www.onedoc.ch" + name_element['href'] if name_element and name_element.has_attr('href') else "Unknown"
        
        # Extract address
        address_element = item.find('div', class_='directory-item-text-normal')
        address = address_element.text.strip() if address_element else "Unknown"
        
        # Parse address into components (street, postal code, city)
        street = ""
        postal_code = ""
        city = ""
        
        if address != "Unknown" and ", " in address:
            address_parts = address.split(", ")
            street = address_parts[0]
            
            if len(address_parts) > 1:
                postal_city = address_parts[1]
                # Extract postal code (usually 4 digits) and city
                postal_match = re.search(r'(\d{4})\s+(.*)', postal_city)
                if postal_match:
                    postal_code = postal_match.group(1)
                    city = postal_match.group(2)
                else:
                    city = postal_city
        
        # Create basic practice data
        practice_data = {
            'name': name,
            'address': address,
            'street': street,
            'postal_code': postal_code,
            'city': city,
            'url': practice_url,
            'canton': canton_name,
            'phone_number': "Not available",
            'professions': ""
        }
        
        # Fetch additional details from the practice detail page if URL is valid
        if practice_url != "Unknown":
            details = extract_practice_details(practice_url, name, index, total_items)
            practice_data['phone_number'] = details['phone_number']
            practice_data['professions'] = ", ".join(details['professions'])
            
            # Add a small random delay between detail page requests
            delay = random.uniform(0.5, 2)
            print(f"  ⏱ Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)
        
        practices.append(practice_data)
        
        # Show progress after each practice
        print(f"Progress: {index}/{total_items} practices processed on this page")
    
    return practices

def save_to_csv(data, filename="medical_practices.csv"):
    """Save the practices data to a CSV file"""
    if not data:
        print("No data to save")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'address', 'street', 'postal_code', 'city', 'canton', 'phone_number', 'professions', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Saved {len(data)} practices to {filename}")
    print(f"File saved at: {os.path.abspath(filename)}")

def save_progress(data, filename="practices_progress.csv"):
    """Save progress data to a CSV file, appending if it exists"""
    if not data:
        return
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'address', 'street', 'postal_code', 'city', 'canton', 'phone_number', 'professions', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(data)
    
    print(f"Saved progress: {len(data)} practices appended to {filename}")

def check_processed_pages():
    """Load already processed pages from a tracking file"""
    processed = {}
    if os.path.exists('processed_pages.csv'):
        with open('processed_pages.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    canton = row[0]
                    page = int(row[1])
                    if canton not in processed:
                        processed[canton] = set()
                    processed[canton].add(page)
    return processed

def mark_page_processed(canton, page_num):
    """Mark a page as processed in the tracking file"""
    with open('processed_pages.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([canton, page_num])

def load_already_scraped_practices():
    """Load already scraped practices to avoid duplicates"""
    scraped_urls = set()
    if os.path.exists('practices_progress.csv'):
        with open('practices_progress.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scraped_urls.add(row.get('url', ''))
    return scraped_urls

def extract_practices_with_progress(html, canton_name, scraped_urls):
    """Extract practice data from a canton page with progress display"""
    practices = extract_practices(html, canton_name)
    
    # Filter out already scraped practices
    new_practices = []
    for practice in practices:
        if practice['url'] not in scraped_urls:
            new_practices.append(practice)
            scraped_urls.add(practice['url'])
    
    return new_practices

def main():
    all_practices = []
    total_count = 0
    
    # Load resumption data
    processed_pages = check_processed_pages()
    scraped_urls = load_already_scraped_practices()
    print(f"Found {len(scraped_urls)} already scraped practices")
    
    # Fetch the overview page
    overview_html = fetch_page(overview_url)
    if not overview_html:
        print("Failed to fetch overview page. Exiting.")
        return
    
    # Extract canton links
    canton_links = extract_canton_links(overview_html)
    
    # Process each canton
    for canton_index, canton in enumerate(canton_links):
        canton_name = canton['name']
        canton_url = canton['url']
        
        print(f"\n[{canton_index+1}/{len(canton_links)}] Processing canton: {canton_name}")
        
        # Skip already fully processed cantons
        if canton_name in processed_pages and len(processed_pages[canton_name]) > 0:
            print(f"Resuming canton {canton_name}, some pages already processed")
        
        # Fetch the first page of the canton if not processed
        first_page_processed = canton_name in processed_pages and 1 in processed_pages[canton_name]
        if not first_page_processed:
            canton_html = fetch_page(canton_url)
            if not canton_html:
                print(f"Failed to fetch canton page for {canton_name}. Skipping.")
                continue
            
            # Get the maximum page number
            max_page = get_max_page_number(canton_html, canton_url)
            print(f"Canton {canton_name} has {max_page} pages")
            
            # Process first page
            print(f"Processing page 1/{max_page} for {canton_name}")
            practices_page1 = extract_practices_with_progress(canton_html, canton_name, scraped_urls)
            print(f"Found {len(practices_page1)} new practices on page 1")
            
            all_practices.extend(practices_page1)
            total_count += len(practices_page1)
            
            # Save progress after each page
            save_progress(practices_page1)
            mark_page_processed(canton_name, 1)
            
            # Display overall progress
            print(f"Overall progress: {total_count} practices scraped so far")
        else:
            # If first page was already processed, we still need to get max_page
            canton_html = fetch_page(canton_url)
            max_page = get_max_page_number(canton_html, canton_url) if canton_html else 1
            print(f"Canton {canton_name} has {max_page} pages (resuming)")
        
        # Process remaining pages
        for page_num in range(2, max_page + 1):
            # Skip already processed pages
            if canton_name in processed_pages and page_num in processed_pages[canton_name]:
                print(f"Skipping already processed page {page_num}/{max_page} for {canton_name}")
                continue
                
            print(f"Processing page {page_num}/{max_page} for {canton_name}")
            page_url = f"{canton_url}?page={page_num}"
            page_html = fetch_page(page_url)
            
            if not page_html:
                print(f"Failed to fetch page {page_num} for {canton_name}. Skipping.")
                continue
            
            practices = extract_practices_with_progress(page_html, canton_name, scraped_urls)
            print(f"Found {len(practices)} new practices on page {page_num}")
            
            all_practices.extend(practices)
            total_count += len(practices)
            
            # Save progress after each page
            save_progress(practices)
            mark_page_processed(canton_name, page_num)
            
            # Display overall progress
            print(f"Overall progress: {total_count} practices scraped so far")
            
            # Add a small delay between requests
            delay = random.uniform(0.5, 2)
            print(f"Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)
    
    # Save all results to final CSV
    save_to_csv(all_practices, "all_medical_practices.csv")
    print(f"Scraping completed. Total new practices found: {len(all_practices)}")
    print(f"Total practices overall: {total_count}")

if __name__ == "__main__":
    main()