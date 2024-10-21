# OpenStreetMap Business Scraper

This is a Python application that fetches business data from OpenStreetMap using the Overpass API. The application allows you to input geographical coordinates, radius, and business categories, then retrieves relevant data such as name, address, and phone number. The fetched data can be saved to an Excel file, and duplicate entries can be removed.

## Features
- Input latitude, longitude, and search radius (in kilometers)
- Select business categories from a predefined list (e.g., restaurants, banks, shops)
- Fetch business data based on the selected categories
- Remove duplicate business names
- Save the results in an Excel file (`businesses.xlsx`)
- Exclude businesses without a phone number

## Requirements
The app requires the following Python modules:
- `requests`
- `tkinter`
- `openpyxl`

If the modules are not installed, the app will automatically install them.

## Installation
1. Clone the repository or download the script.
2. Run the script, and it will check for required modules and install them if missing.

## Usage
1. Enter the latitude, longitude, and search radius.
2. Select the business categories you want to include.
3. Click `Fetch Businesses` to retrieve the data from OpenStreetMap.
4. Click `Remove Duplicate Names` to remove any duplicate businesses from the results.
5. Click `Save Data` to save the results in an Excel file.

## Acknowledgments
- Data fetched from [OpenStreetMap](https://www.openstreetmap.org/)
- Overpass API for querying OpenStreetMap data

Clément GHANEME - 2024/10

