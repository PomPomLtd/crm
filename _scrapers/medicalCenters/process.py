import pandas as pd
import re

def parse_address(address):
    """Extracts street/number, ZIP code, and city from a full address."""
    try:
        parts = address.split(",", 1)  # Split into street and ZIP/city
        street = parts[0].strip() if len(parts) > 0 else "Unknown Street"

        match = re.search(r"(\d{4})\s(.+)", parts[1]) if len(parts) > 1 else None
        zip_code = match.group(1) if match else "0000"
        city = match.group(2) if match else "Unknown City"

        return street, zip_code, city
    except Exception:
        return "Unknown Street", "0000", "Unknown City"

# Load CSV file
input_file = "all_medical_centers.csv"  # Replace with your actual file path
output_file = "all_medical_centers_modified.csv"

df = pd.read_csv(input_file)

# Apply function to address column
df[["Street / Number", "ZIP Code", "City"]] = df["address"].apply(lambda x: pd.Series(parse_address(x)))

# Save the modified CSV
df.to_csv(output_file, index=False)

print(f"Processed file saved as {output_file}")

