import csv
import time
import random
import os
import sys
import requests
from urllib.parse import urlparse

# Global counter for rate limit errors.
rate_limit_errors = 0

# Banned domains to skip.
banned_domains = ["onedoc.ch", "comparis.ch", "doktor.ch"]

# SearchAPI details
API_KEY = "VQxddzhtWBd9ANBGbtLGd3dk"
SEARCH_URL = "https://www.searchapi.io/api/v1/search"

def format_time(seconds):
    """Format seconds into H:MM:SS string."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}"

def fetch_company_url(company_name, city, max_retries=3):
    """
    Build a search query using the company name and, if applicable,
    the city (if not already in the company name). Retries on rate limit errors.
    Replaces the old DuckDuckGo search logic with SearchAPI's Google engine.
    """
    global rate_limit_errors

    # Construct the search query
    query = company_name
    if city and city.lower() not in company_name.lower():
        query += f" {city}"

    attempt = 0
    while attempt < max_retries:
        try:
            # Prepare query params for the new API
            params = {
                "engine": "google",
                "q": query,
                "api_key": API_KEY,
                "num": 1  # get only the top result
            }
            headers = {
                # A generic User-Agent to avoid 403 responses
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0 Safari/537.36"
                )
            }
            # Increased timeout to 20 seconds
            response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=20)
            
            # Treat a 429 or 403 as a rate-limit or block
            if response.status_code in [429, 403]:
                raise requests.exceptions.RequestException(
                    f"Rate limit / Block encountered (status {response.status_code})"
                )

            # Raise an error for other unsuccessful requests
            response.raise_for_status()

            data = response.json()
            # Extract the first organic result link, if present
            if "organic_results" in data and len(data["organic_results"]) > 0:
                return data["organic_results"][0].get("link", "")
            return ""

        except requests.exceptions.RequestException as e:
            rate_limit_errors += 1
            print(f"\033[93m⚠️  Error fetching URL for '{company_name}' (attempt {attempt+1}/{max_retries}): {e}\033[0m")
            # Shorter backoff for error retries
            wait_time = random.uniform(5, 10) * (attempt + 1)
            time.sleep(wait_time)
            attempt += 1

    return ""

def check_zuweisung(url):
    """
    Fetch the webpage at the given URL and search for German and French keywords.
    Returns a tuple (flag, triggered_keywords) where flag is 1 if any keyword is found,
    and triggered_keywords is a list of keywords that were detected.
    """
    try:
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/115.0 Safari/537.36')
        }
        # Increased timeout here to 20 seconds as well
        response = requests.get(url, timeout=20, headers=headers)
        if response.status_code != 200:
            return 0, []
        content = response.text
        german_keywords = ["Zuweisung", "Überweisung", "Zuweiser", "für Ärzte"]
        french_keywords = ["référence", "pour médecins"]
        keywords = german_keywords + french_keywords
        triggered = []
        for kw in keywords:
            if kw.lower() in content.lower():
                triggered.append(kw)
        flag = 1 if triggered else 0
        return flag, triggered
    except Exception as e:
        print(f"\033[91m❌ Error fetching website {url}: {e}\033[0m")
        return 0, []

def is_banned_url(url):
    """Check if the URL belongs to any banned domain."""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        for banned in banned_domains:
            if banned in domain:
                return True
        return False
    except Exception as e:
        print(f"\033[91m❌ Error parsing URL {url}: {e}\033[0m")
        return False

def print_final_summary(active_count, initial_active, total_rows, active_durations, start_time):
    elapsed = time.time() - start_time
    avg_time = sum(active_durations) / len(active_durations) if active_durations else 0
    remaining_active = initial_active - active_count
    estimated_remaining = avg_time * remaining_active
    progress_percent = (active_count / initial_active) * 100 if initial_active else 100
    print("\n\033[96m========================================")
    print("              FINAL SUMMARY")
    print("========================================")
    print(f"Total elements in file    : {total_rows}")
    print(f"Already processed         : {total_rows - initial_active}")
    print(f"Processed this run        : {active_count} / {initial_active} ({progress_percent:.2f}%)")
    print(f"Average time per row      : {avg_time:.2f} s")
    print(f"Estimated time remaining  : {format_time(estimated_remaining)}")
    print(f"Total elapsed time        : {format_time(elapsed)}")
    print(f"Rate limit errors         : {rate_limit_errors}")
    print("========================================\033[0m\n")

def main():
    input_file = "all_hospitals.csv"             # Input CSV file
    output_file = "all_hospitals_with_urls.csv"  # Output CSV file
    
    # Load all rows to determine total count.
    with open(input_file, newline='', encoding='utf-8') as infile:
        all_rows = list(csv.DictReader(infile))
    total_rows = len(all_rows)
    
    # Build a set of company names already processed from the output file.
    processed_names = set()
    if os.path.exists(output_file):
        with open(output_file, newline='', encoding='utf-8') as outfile:
            reader = csv.DictReader(outfile)
            for row in reader:
                if row.get("name"):
                    processed_names.add(row["name"])
    
    initial_active = total_rows - len(processed_names)
    
    # Display header with total numbers.
    print("\n\033[96m===============================")
    print("        PROCESSING REPORT")
    print("===============================")
    print(f"Total elements in file    : {total_rows}")
    print(f"Already processed         : {len(processed_names)}")
    print(f"To process this run       : {initial_active}")
    print("===============================\033[0m\n")
    
    start_time = time.time()
    active_count = 0          # Count of rows processed this run (active rows)
    active_durations = []     # List to store total time for each active row
    
    try:
        # Open the output file in append mode.
        with open(output_file, 'a', newline='', encoding='utf-8') as outfile:
            # Use header from the input file and add new columns if missing.
            fieldnames = list(all_rows[0].keys())
            if "official_website" not in fieldnames:
                fieldnames.append("official_website")
            if "Zuweisung" not in fieldnames:
                fieldnames.append("Zuweisung")
            if "Triggered_Keywords" not in fieldnames:
                fieldnames.append("Triggered_Keywords")
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            
            # Write header if the output file is new/empty.
            if os.stat(output_file).st_size == 0:
                writer.writeheader()
            
            for row in all_rows:
                company_name = row.get("name", "").strip()
                # Skip already processed rows.
                if company_name in processed_names:
                    continue
                
                # Start timing for this row
                row_start = time.time()
                
                city = row.get("city", "").strip()
                if company_name:
                    url = fetch_company_url(company_name, city)
                    if url and is_banned_url(url):
                        print(f"\033[95m🚫 Skipping banned URL for {company_name}: {url}\033[0m")
                        url = ""
                        zuweisung_flag = 0
                        triggered_keywords = []
                    else:
                        print(f"\033[92m🚀 Found URL for {company_name}: {url}\033[0m")
                        if url:
                            zuweisung_flag, triggered_keywords = check_zuweisung(url)
                            print(f"\033[94m🔍 Zuweisung flag for {company_name}: {zuweisung_flag} | Triggered: {triggered_keywords}\033[0m")
                        else:
                            zuweisung_flag = 0
                            triggered_keywords = []
                    row["official_website"] = url
                    row["Zuweisung"] = zuweisung_flag
                    row["Triggered_Keywords"] = ", ".join(triggered_keywords)
                else:
                    row["official_website"] = ""
                    row["Zuweisung"] = 0
                    row["Triggered_Keywords"] = ""
                
                # Write the updated row to the CSV.
                writer.writerow(row)
                processed_names.add(company_name)
                active_count += 1
                
                # Measure the time taken to process this row.
                row_duration = time.time() - row_start
                active_durations.append(row_duration)
                
                # Calculate and print progress statistics.
                elapsed = time.time() - start_time
                avg_time = sum(active_durations) / len(active_durations)
                remaining_active = initial_active - active_count
                estimated_remaining = avg_time * remaining_active
                progress_percent = (active_count / initial_active) * 100 if initial_active else 100
                
                print("\033[96m----------------------------------------")
                print(f"Processed this run        : {active_count} / {initial_active}")
                print(f"Total in file             : {total_rows}")
                print(f"Avg time per row          : {avg_time:.2f} s")
                print(f"Estimated time remaining  : {format_time(estimated_remaining)}")
                print(f"Elapsed time              : {format_time(elapsed)}")
                print(f"Rate limit errors         : {rate_limit_errors}")
                print("----------------------------------------\033[0m\n")

    except KeyboardInterrupt:
        print("\n\033[93m✋ Ctrl+C pressed. Stopping gracefully...\033[0m")
        print_final_summary(active_count, initial_active, total_rows, active_durations, start_time)
        sys.exit(0)
    
    # Final summary if completed normally.
    print_final_summary(active_count, initial_active, total_rows, active_durations, start_time)

if __name__ == "__main__":
    main()
