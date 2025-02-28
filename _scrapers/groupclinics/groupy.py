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
import json
import datetime

# Base URL for the group practices overview page
overview_url = "https://www.onedoc.ch/de/gruppenpraxis"

# Headers to make the request look like it's coming from a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7',
}

def create_session():
    session = requests.Session()
    # Configure retry strategy
    retry_strategy = Retry(
        total=5,  # Maximum number of retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=2,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except (socket.timeout, socket.gaierror, OSError):
        return False

def fetch_page(url, max_retries=3, retry_delay=10):
    """Fetch HTML content from a URL with retry logic"""
    print(f"Fetching URL: {url}")
    if not check_internet_connection():
        print("No internet connection detected. Waiting before retry...")
        time.sleep(retry_delay)
        if not check_internet_connection():
            print("Still no internet connection. Please check your network.")
            return None

    session = create_session()
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            print(f"Response status: {response.status_code}")
            return response.text
        except (requests.RequestException, socket.gaierror, socket.timeout) as e:
            print(f"Error on attempt {attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                sleep_time = retry_delay * (2 ** attempt)
                print(f"Waiting {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
                if not check_internet_connection():
                    print("No internet connection detected. Waiting for connection...")
                    for _ in range(12):  # Wait up to 2 minutes
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
    
    max_page = 1
    page_links = pagination.find_all('a')
    for link in page_links:
        try:
            page_num = int(link.get_text().strip())
            max_page = max(max_page, page_num)
        except (ValueError, TypeError):
            continue
    return max_page

def build_google_search_url(title, city):
    """Constructs a static Google search URL for a given title and city."""
    if not title or not city or title == "Unknown" or city == "Unknown":
        return "Unknown"
    search_query = f"{title} {city}"
    # Replace spaces with plus signs
    search_query_encoded = search_query.replace(" ", "+")
    url = f"https://www.google.ch/search?q={search_query_encoded}"
    return url

def extract_professions(detail_html):
    """Extract professions from the detail page HTML"""
    if not detail_html:
        return "Unknown"
    
    soup = BeautifulSoup(detail_html, 'html.parser')
    profession_chips = soup.select(".od-profile-chip")
    if profession_chips:
        professions = [chip.text.strip() for chip in profession_chips]
        return ", ".join(professions)
    return "Unknown"

def extract_phone_and_professions(detail_url):
    """Extract phone number and professions from a group practice detail page"""
    print()  # For progress indicator
    detail_html = fetch_page(detail_url)
    if not detail_html:
        return "Unknown", "Unknown"
    
    soup = BeautifulSoup(detail_html, 'html.parser')
    phone_pattern = r'Für weitere Informationen oder um einen Termin zu buchen, können Sie uns auch anrufen:'
    contact_paragraphs = soup.find_all('p')
    
    phone_number = "Unknown"
    for p in contact_paragraphs:
        if p.text and re.search(phone_pattern, p.text):
            phone_link = p.find('a', href=lambda href: href and href.startswith('tel:'))
            if phone_link:
                phone_number = phone_link.text.strip()
                break
    
    if phone_number == "Unknown":
        phone_links = soup.find_all('a', href=lambda href: href and href.startswith('tel:'))
        if phone_links:
            phone_number = phone_links[0].text.strip()
    
    professions = extract_professions(detail_html)
    return phone_number, professions

def extract_group_practices(html, canton_name):
    """Extract group practice data from a canton page"""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    practice_items = soup.find_all('div', class_='directory-item')
    practices = []
    
    for item in practice_items:
        name_element = item.find('a')
        name = name_element.text.strip() if name_element else "Unknown"
        practice_url = "https://www.onedoc.ch" + name_element['href'] if name_element and name_element.has_attr('href') else "Unknown"
        address_element = item.find('div', class_='directory-item-text-normal')
        address = address_element.text.strip() if address_element else "Unknown"
        
        street = ""
        postal_code = ""
        city = ""
        if address != "Unknown" and ", " in address:
            address_parts = address.split(", ")
            street = address_parts[0]
            if len(address_parts) > 1:
                postal_city = address_parts[1]
                postal_match = re.search(r'(\d{4})\s+(.*)', postal_city)
                if postal_match:
                    postal_code = postal_match.group(1)
                    city = postal_match.group(2)
                else:
                    city = postal_city
        
        print(f"Extracting data for: {name}")
        phone_number, professions = "Unknown", "Unknown"
        if practice_url != "Unknown":
            phone_number, professions = extract_phone_and_professions(practice_url)
            time.sleep(random.uniform(1, 2))
        
        # Instead of a DuckDuckGo search, build a static Google search URL
        google_search_url = build_google_search_url(name, city)
        
        practices.append({
            'name': name,
            'address': address,
            'street': street,
            'postal_code': postal_code,
            'city': city,
            'phone': phone_number,
            'professions': professions,
            'official_website': "Unknown",
            'google_search_url': google_search_url,
            'url': practice_url,
            'canton': canton_name,
            'type': 'Gruppenpraxis'
        })
    
    return practices

def save_to_csv(data, filename="group_practices.csv"):
    """Save the group practices data to a CSV file"""
    if not data:
        print("No data to save")
        return
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'address', 'street', 'postal_code', 'city', 'canton', 'phone', 'professions', 'official_website', 'google_search_url', 'type', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} group practices to {filename}")
    print(f"File saved at: {os.path.abspath(filename)}")

def save_progress(data, filename="group_practices_progress.csv"):
    """Save progress data to a CSV file, appending if it exists"""
    if not data:
        return
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'address', 'street', 'postal_code', 'city', 'canton', 'phone', 'professions', 'official_website', 'google_search_url', 'type', 'url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)
    print(f"Saved progress: {len(data)} group practices appended to {filename}")

def main():
    """Main function to run the scraper"""
    state_file = "scraper_state.json"
    print("\n" + "=" * 80)
    print("🏥 ONEDOC GROUP PRACTICE SCRAPER 🏥".center(80))
    print("=" * 80)
    print("Starting the hunt for Swiss medical group practices...".center(80))
    print("-" * 80)
    print(f"⏰ Scraping started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80 + "\n")
    
    all_practices = []
    canton_count = 0
    resume_state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                resume_state = json.load(f)
            print(f"📋 Found saved state - attempting to resume scraping!")
            print(f"   Last processed canton: {resume_state.get('last_canton', 'None')}")
            print(f"   Last processed page: {resume_state.get('last_page', 0)}")
            if os.path.exists("group_practices_progress.csv"):
                try:
                    import pandas as pd
                    progress_df = pd.read_csv("group_practices_progress.csv")
                    all_practices = progress_df.to_dict('records')
                    print(f"   Loaded {len(all_practices)} previously scraped practices")
                except Exception as e:
                    print(f"   ⚠️ Error loading progress file: {e}")
                    all_practices = []
        except Exception as e:
            print(f"⚠️ Error loading state file: {e}")
            resume_state = {}
    
    print("🔍 Exploring the medical landscape of Switzerland...")
    overview_html = fetch_page(overview_url)
    if not overview_html:
        print("❌ Failed to fetch overview page. The medical journey ends before it began!")
        return
    
    canton_links = extract_canton_links(overview_html)
    print(f"🗺️  Found {len(canton_links)} cantons with group practices. Let the tour begin!")
    
    practice_count = len(all_practices)
    total_found_on_page = 0
    resume_canton = resume_state.get('last_canton', None)
    resume_page = resume_state.get('last_page', 0)
    resume_mode = False
    if resume_canton:
        print(f"🔄 Resuming from canton {resume_canton}, page {resume_page+1}")
        resume_mode = True
    
    for canton in canton_links:
        canton_name = canton['name']
        canton_url = canton['url']
        if resume_mode and canton_name != resume_canton:
            print(f"⏩ Skipping canton: {canton_name} (already processed)")
            continue
        elif resume_mode and canton_name == resume_canton:
            print(f"🎯 Resuming with canton: {canton_name}")
            resume_mode = False
        canton_count += 1
        print(f"\n🏔️  [{canton_count}/{len(canton_links)}] Now exploring: {canton_name}")
        print(f"   URL: {canton_url}")
        
        with open(state_file, 'w') as f:
            json.dump({'last_canton': canton_name, 'last_page': 0}, f)
        
        canton_html = fetch_page(canton_url)
        if not canton_html:
            print(f"❌ Failed to access {canton_name}. Moving to the next canton...")
            continue
        
        max_page = get_max_page_number(canton_html)
        if max_page > 1:
            print(f"📚 This canton has {max_page} pages of medical treasures!")
        else:
            print(f"📄 This canton has a single page of medical treasures!")
        
        for page_num in range(1, max_page + 1):
            if resume_mode and page_num <= resume_page:
                print(f"⏩ Skipping page {page_num} (already processed)")
                continue
            with open(state_file, 'w') as f:
                json.dump({'last_canton': canton_name, 'last_page': page_num}, f)
                
            if page_num == 1:
                page_html = canton_html
                print(f"🔍 Scanning page {page_num} of {max_page}...")
            else:
                page_url = f"{canton_url}?page={page_num}"
                print(f"🔍 Scanning page {page_num} of {max_page}...")
                page_html = fetch_page(page_url)
                if not page_html:
                    print(f"❌ Failed to access page {page_num} for {canton_name}. Moving on...")
                    continue
            
            soup = BeautifulSoup(page_html, 'html.parser')
            items_on_page = len(soup.find_all('div', class_='directory-item'))
            total_found_on_page = items_on_page
            print(f"📋 Found {items_on_page} listings on this page")
            item_index = 0
            practices = []
            
            for item in soup.find_all('div', class_='directory-item'):
                item_index += 1
                practice_count += 1
                name_element = item.find('a')
                name = name_element.text.strip() if name_element else "Unknown"
                practice_url = "https://www.onedoc.ch" + name_element['href'] if name_element and name_element.has_attr('href') else "Unknown"
                print(f"\r🔄 Processing: {name} ({item_index}/{items_on_page} on page, {practice_count} total)", end='', flush=True)
                address_element = item.find('div', class_='directory-item-text-normal')
                address = address_element.text.strip() if address_element else "Unknown"
                
                street = ""
                postal_code = ""
                city = ""
                if address != "Unknown" and ", " in address:
                    address_parts = address.split(", ")
                    street = address_parts[0]
                    if len(address_parts) > 1:
                        postal_city = address_parts[1]
                        postal_match = re.search(r'(\d{4})\s+(.*)', postal_city)
                        if postal_match:
                            postal_code = postal_match.group(1)
                            city = postal_match.group(2)
                        else:
                            city = postal_city
                
                phone_number, professions = "Unknown", "Unknown"
                if practice_url != "Unknown":
                    phone_number, professions = extract_phone_and_professions(practice_url)
                    time.sleep(random.uniform(0.5, 1.5))
                
                # Build the static Google search URL (no external requests)
                google_search_url = build_google_search_url(name, city)
                
                practice_data = {
                    'name': name,
                    'address': address,
                    'street': street,
                    'postal_code': postal_code,
                    'city': city,
                    'phone': phone_number,
                    'professions': professions,
                    'official_website': "Unknown",
                    'google_search_url': google_search_url,
                    'url': practice_url,
                    'canton': canton_name,
                    'type': 'Gruppenpraxis'
                }
                
                practices.append(practice_data)
                
                with open('group_practices_individual.jsonl', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(practice_data, ensure_ascii=False) + '\n')
            print()  # Newline after progress indicator
            
            if practices:
                print(f"✅ Processed {len(practices)} group practices on page {page_num}")
                all_practices.extend(practices)
                save_progress(practices)
            else:
                print("😢 No practices found on this page. Strange...")
            
            if page_num < max_page:
                delay = random.uniform(1, 3)
                print(f"😴 Taking a {delay:.2f} second coffee break before the next page...")
                time.sleep(delay)
    
    if os.path.exists(state_file):
        with open(state_file, 'w') as f:
            json.dump({
                'last_canton': "COMPLETED",
                'last_page': 0,
                'completed': True,
                'completion_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f)
    
    print("\n" + "=" * 80)
    print("🎉 SCRAPING COMPLETED! 🎉".center(80))
    print("=" * 80)
    print(f"📊 Total cantons processed: {canton_count}")
    print(f"📊 Total group practices found: {len(all_practices)}")
    
    if all_practices:
        save_to_csv(all_practices, "all_group_practices.csv")
        print(f"💾 Data saved to: {os.path.abspath('all_group_practices.csv')}")
        
        cities = {}
        professions_count = {}
        for practice in all_practices:
            if practice['city'] and practice['city'] != "Unknown":
                cities[practice['city']] = cities.get(practice['city'], 0) + 1
            if practice['professions'] and practice['professions'] != "Unknown":
                for prof in practice['professions'].split(', '):
                    professions_count[prof] = professions_count.get(prof, 0) + 1
        
        top_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\n🏙️  Top 5 cities with the most group practices:")
        for city, count in top_cities:
            print(f"   {city}: {count} practices")
        
        if professions_count:
            top_professions = sorted(professions_count.items(), key=lambda x: x[1], reverse=True)[:5]
            print("\n👨‍⚕️ Top 5 medical specializations:")
            for prof, count in top_professions:
                print(f"   {prof}: {count} practices")
    
    print("\n⏰ Scraping ended at:", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 80)
    print("Thank you for using the OneDoc Group Practice Scraper!".center(80))
    print("=" * 80)

if __name__ == "__main__":
    main()
