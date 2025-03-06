import csv

def add_google_search_column(input_csv, output_csv):
    """
    Reads `input_csv` and writes a new CSV (`output_csv`) that has one extra column:
    'google_search_url' containing a link to Google.ch with a query for each practice.
    """
    with open(input_csv, mode='r', encoding='utf-8', newline='') as infile, \
         open(output_csv, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile)
        rows = list(reader)
        
        if not rows:
            print(f"No data found in {input_csv}. Exiting.")
            return
        
        header = rows[0]
        
        # Try to find "name" and "city" columns
        try:
            name_index = header.index("name")
        except ValueError:
            raise ValueError("Couldn't find a 'name' column in the CSV header.")
        
        try:
            city_index = header.index("city")
        except ValueError:
            raise ValueError("Couldn't find a 'city' column in the CSV header.")
        
        # Add a new header column for the Google URL
        new_header = header + ["google_search_url"]
        
        writer = csv.writer(outfile)
        writer.writerow(new_header)
        
        # We'll keep a count of how many data rows we process
        row_count = 0
        
        # Process each data row
        for row in rows[1:]:
            row_count += 1
            
            # Extract the name and city
            practice_name = row[name_index].strip()
            practice_city = row[city_index].strip()
            
            # Build the query
            query = practice_name.replace(' ', '+')
            
            # Append city if not already in name (case-insensitive)
            if practice_city and (practice_city.lower() not in practice_name.lower()):
                query += '+' + practice_city.replace(' ', '+')
            
            google_url = f"https://www.google.ch/search?q={query}"
            
            # Write original row + new URL column
            new_row = row + [google_url]
            writer.writerow(new_row)
        
        print(f"Successfully processed {row_count} rows.")
        print(f"Output saved to: {output_csv}")


if __name__ == "__main__":
    input_file = "all_hospitals_with_urls.csv"
    output_file = "all_hospitals_with_google_urls.csv"
    
    add_google_search_column(input_file, output_file)
