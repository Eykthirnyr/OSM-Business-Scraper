
# OpenStreetMap Business Scraper

This Python application allows you to fetch businesses from the OpenStreetMap database within a specified radius of a given latitude and longitude. The results include business names, addresses, and phone numbers. The app provides a graphical user interface (GUI) to enter location information, fetch data, remove duplicates, and save the results to an Excel file.

## Features

- Fetch businesses (shops, offices, amenities) within a given radius of a location.
- Option to exclude businesses without phone numbers.
- Remove duplicate entries by name.
- Save the fetched businesses into an Excel file (`businesses.xlsx`).
- Easy-to-use GUI for input and operations.

## Requirements

The following Python libraries are required:

- `requests`
- `tkinter`
- `openpyxl`

The script checks for missing dependencies and installs them automatically if necessary.

## Installation

Clone this repository and navigate to the project directory:

```bash
git clone https://github.com/yourusername/osm-business-scraper.git
cd osm-business-scraper
```

You can run the script directly. If any of the required modules are missing, they will be installed automatically.

```bash
python osm_business_scraper.py
```

## How It Works

1. **Fetch Businesses:**
   - Enter the latitude, longitude, and radius (in kilometers).
   - Click "Fetch Businesses" to retrieve business information.
   - The data is fetched from the Overpass API using OpenStreetMap data.

2. **Remove Duplicate Names:**
   - If the same business appears multiple times, you can remove duplicates based on their names.

3. **Save Data:**
   - Once businesses are fetched, save the results into an Excel file (`businesses.xlsx`).
   - The saved data includes the business name, address, and phone number (if available).

## GUI Components

- **Latitude, Longitude, and Radius Input:** Specify the geographic coordinates and the search radius.
- **Exclude Phone Numbers Checkbox:** Exclude entries without phone numbers.
- **Buttons:** Fetch businesses, remove duplicate names, and save the data.
- **Status Label:** Displays the number of processed businesses.

## Code Structure

- **fetch_businesses:** Queries OpenStreetMap for businesses within the specified radius and processes the results.
- **remove_duplicates:** Removes entries with duplicate names from the fetched data.
- **save_data:** Exports the results to an Excel file with proper formatting and column adjustments.
- **construct_address:** Helper function to construct the full address from available OpenStreetMap tags.

## Example Usage

After running the script, input the latitude, longitude, and radius, then click the "Fetch Businesses" button. The data is processed in real-time and displayed in a pop-up once the process is completed. You can remove duplicate entries and save the cleaned data to an Excel file.

```bash
# Fetch data around latitude 48.8566, longitude 2.3522 (Paris), with a radius of 2km.
```

Clément GHANEME - 2024/10

