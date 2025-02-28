import csv
import time
import random
import os
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

def fetch_company_url(company_name, city, max_retries=3):
    """
    Build a search query using the company name and, if applicable,
    the city (if not already included in the company name). Retries
    on rate limit errors using an increased exponential backoff.
    """
    query = company_name
    if city and city.lower() not in company_name.lower():
        query += f" {city}"
    
    attempt = 0
    while attempt < max_retries:
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=1)
                if results and len(results) > 0:
                    return results[0].get("href", "")
                return ""
        except DuckDuckGoSearchException as e:
            print(f"Error fetching URL for '{company_name}' (attempt {attempt+1}/{max_retries}): {e}")
            # Increase backoff time: wait 10-20 seconds multiplied by the attempt number
            wait_time = random.uniform(10, 20) * (attempt + 1)
            time.sleep(wait_time)
            attempt += 1
    return ""

def main():
    input_file = "all_group_practices.csv"      # Input CSV file
    output_file = "companies_with_urls.csv"       # Output CSV file for progress tracking
    
    # Build a set of company names already processed.
    processed_names = set()
    if os.path.exists(output_file):
        with open(output_file, newline='', encoding='utf-8') as outfile:
            reader = csv.DictReader(outfile)
            for row in reader:
                if row.get("name"):
                    processed_names.add(row["name"])
    
    # Open input and output files.
    with open(input_file, newline='', encoding='utf-8') as infile, \
         open(output_file, 'a', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames.copy()
        if "official_website" not in fieldnames:
            fieldnames.append("official_website")
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        # Write header if the output file is new/empty.
        if os.stat(output_file).st_size == 0:
            writer.writeheader()
        
        # Process each row.
        for row in reader:
            company_name = row.get("name", "").strip()
            if company_name in processed_names:
                continue
            
            city = row.get("city", "").strip()
            if company_name:
                url = fetch_company_url(company_name, city)
                row["official_website"] = url
                print(f"Found URL for {company_name}: {url}")
            else:
                row["official_website"] = ""
            
            writer.writerow(row)
            processed_names.add(company_name)
            # Increase delay between queries to help avoid rate limits.
            time.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    main()
