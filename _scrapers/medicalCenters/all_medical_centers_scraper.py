import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import random
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Base URL for the overview page
overview_url = "https://www.onedoc.ch/de/medizinisches-zentrum"

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

def fetch_page(url, max_retries=3, retry_delay=10):
    """Fetch HTML content from a URL with retry logic"""
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
            response = session.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            print(f"Response status: {response.status_code}")
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

def get_max_page_number(html):
    """Determine the maximum number of pages in the pagination"""
    if not html:
        return 1
    
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find('ul', class_='pagination')
    
    if not pagination:
        print("No pagination found, assuming single page")
        return 1
    
    # Find all page links and extract the highest page number
    max_page = 1
    page_links = pagination.find_all('a')
    for link in page_links:
        try:
            page_num = int(link.get_text().strip())
            max_page = max(max_page, page_num)
        except (ValueError, TypeError):
            continue
    
    return max_page

def extract_medical_centers(html, canton_name):
    """Extract medical centers data from a canton page"""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    center_items = soup.find_all('div', class_='directory-item')
    
    centers = []
    for item in center_items:
        # Extract center name and URL
        name_element = item.find('a')
        name = name_element.text.strip() if name_element else "Unknown"
        center_url = "https://www.onedoc.ch" + name_element['href'] if name_element and name_element.has_attr('href') else "Unknown"
        
        # Extract address
        address_element = item.find('div', class_='directory-item-text-normal')
        address = address_element.text.strip() if address_element else "Unknown"
        
        centers.append({
            'name': name,
            'address': address,
            'url': center_url,
            'canton': canton_name
        })
    
    return centers

def save_to_csv(data, filename="medical_centers.csv"):
    """Save the centers data to a CSV file"""
    if not data:
        print("No data to save")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'address', 'canton', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Saved {len(data)} medical centers to {filename}")
    print(f"File saved at: {os.path.abspath(filename)}")

def save_progress(data, filename="medical_centers_progress.csv"):
    """Save progress data to a CSV file, appending if it exists"""
    if not data:
        return
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'address', 'canton', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(data)
    
    print(f"Saved progress: {len(data)} centers appended to {filename}")

def main():
    all_centers = []
    
    # Fetch the overview page
    overview_html = fetch_page(overview_url)
    if not overview_html:
        print("Failed to fetch overview page. Exiting.")
        return
    
    # Extract canton links
    canton_links = extract_canton_links(overview_html)
    
    # Process each canton
    for canton in canton_links:
        canton_name = canton['name']
        canton_url = canton['url']
        
        print(f"\nProcessing canton: {canton_name}")
        
        # Fetch the first page of the canton
        canton_html = fetch_page(canton_url)
        if not canton_html:
            print(f"Failed to fetch canton page for {canton_name}. Skipping.")
            continue
        
        # Get the maximum page number
        max_page = get_max_page_number(canton_html)
        print(f"Canton {canton_name} has {max_page} pages")
        
        # Process first page
        centers_page1 = extract_medical_centers(canton_html, canton_name)
        print(f"Found {len(centers_page1)} centers on page 1")
        all_centers.extend(centers_page1)
        
        # Save progress after each page
        save_progress(centers_page1)
        
        # Process remaining pages
        for page_num in range(2, max_page + 1):
            page_url = f"{canton_url}?page={page_num}"
            page_html = fetch_page(page_url)
            
            if not page_html:
                print(f"Failed to fetch page {page_num} for {canton_name}. Skipping.")
                continue
            
            centers = extract_medical_centers(page_html, canton_name)
            print(f"Found {len(centers)} centers on page {page_num}")
            all_centers.extend(centers)
            
            # Save progress after each page
            save_progress(centers)
            
            # Add a small delay between requests
            delay = random.uniform(1, 3)
            print(f"Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)
    
    # Save all results to final CSV
    save_to_csv(all_centers, "all_medical_centers.csv")
    print(f"Scraping completed. Total centers found: {len(all_centers)}")

if __name__ == "__main__":
    main()
