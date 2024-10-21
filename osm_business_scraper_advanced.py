import sys
import subprocess

# Check for required modules and install if missing
required_modules = ['requests', 'tkinter', 'openpyxl']
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        print(f"The '{module}' module is not installed. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module])

import requests
import tkinter as tk
from tkinter import messagebox
from openpyxl import Workbook
from openpyxl.styles import Font
from collections import defaultdict

def fetch_businesses():
    try:
        latitude = float(entry_latitude.get())
        longitude = float(entry_longitude.get())
        radius = float(entry_radius.get())  # Radius in kilometers
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numerical values.")
        return

    # Collect selected categories
    selected_categories = []
    for (tag, value), var in category_vars.items():
        if var.get():
            selected_categories.append((tag, value))

    if not selected_categories:
        messagebox.showerror("Selection Error", "Please select at least one category.")
        return

    # Build the Overpass API query based on selected categories
    overpass_url = "http://overpass-api.de/api/interpreter"

    # Group selected categories by tag
    tag_values = defaultdict(list)
    for tag, value in selected_categories:
        tag_values[tag].append(value)

    # Build query parts
    query_parts = []
    for tag, values in tag_values.items():
        if None in values:
            # For tags without specific values (e.g., 'shop', 'office')
            query_parts.append(f'  node(around:{radius * 1000},{latitude},{longitude})["name"]["{tag}"];')
            query_parts.append(f'  way(around:{radius * 1000},{latitude},{longitude})["name"]["{tag}"];')
        else:
            # For tags with specific values
            regex = '|'.join(values)
            query_parts.append(f'  node(around:{radius * 1000},{latitude},{longitude})["name"]["{tag}"~"{regex}"];')
            query_parts.append(f'  way(around:{radius * 1000},{latitude},{longitude})["name"]["{tag}"~"{regex}"];')

    overpass_query = f"""
    [out:json];
    (
    {'\n'.join(query_parts)}
    );
    out center;
    """

    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    global all_results  # Make all_results global to access it in other functions
    all_results = []
    processed_count = 0

    for element in data.get('elements', []):
        tags = element.get('tags', {})
        name = tags.get('name')
        address = construct_address(tags)
        phone = tags.get('phone', None)  # Get phone number, None if not present

        # Check if the "Exclude entries without phone number" checkbox is selected
        exclude_no_phone = var_exclude_no_phone.get()

        # Determine whether to include this entry
        include_entry = True
        if exclude_no_phone and not phone:
            include_entry = False

        if name and include_entry:
            all_results.append({
                'Name': name,
                'Address': address,
                'Phone': phone if phone else 'N/A'
            })
            processed_count += 1
            label_counter.config(text=f"Processed: {processed_count}")
            root.update_idletasks()

    if all_results:
        messagebox.showinfo("Data Fetched", f"Data fetched successfully. Total businesses: {processed_count}")
    else:
        messagebox.showinfo("No Data", "No businesses found with the specified criteria.")

def remove_duplicates():
    global all_results
    if not all_results:
        messagebox.showinfo("No Data", "No data to process. Please fetch businesses first.")
        return

    unique_results = []
    seen_names = set()

    for entry in all_results:
        name = entry['Name']
        if name not in seen_names:
            seen_names.add(name)
            unique_results.append(entry)

    duplicates_removed = len(all_results) - len(unique_results)
    all_results = unique_results  # Update the global all_results with unique entries

    label_counter.config(text=f"Processed: {len(all_results)}")
    root.update_idletasks()
    messagebox.showinfo("Duplicates Removed", f"{duplicates_removed} duplicate entries removed.")

def save_data():
    if not all_results:
        messagebox.showinfo("No Data", "No data to save. Please fetch businesses first.")
        return

    save_to_excel(all_results)
    messagebox.showinfo("Success", f"Data saved to 'businesses.xlsx'. Total businesses: {len(all_results)}")

def construct_address(tags):
    # Construct the address from available tags
    address_parts = []
    for key in ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode', 'addr:country']:
        if tags.get(key):
            address_parts.append(tags[key])
    return ', '.join(address_parts) if address_parts else 'N/A'

def save_to_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Businesses"

    # Define the headers
    headers = ['Name', 'Address', 'Phone']
    ws.append(headers)

    # Apply bold font to headers
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Add data to the worksheet
    for entry in data:
        ws.append([entry['Name'], entry['Address'], entry['Phone']])

    # Adjust column widths
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) for cell in column_cells if cell.value)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    # Save the workbook
    wb.save('businesses.xlsx')

# New functions for "Check All" and "Uncheck All"
def check_all():
    for var in category_vars.values():
        var.set(True)

def uncheck_all():
    for var in category_vars.values():
        var.set(False)

# Initialize global variable
all_results = []

# GUI Setup
root = tk.Tk()
root.title("OpenStreetMap Business Scraper")

tk.Label(root, text="Latitude:").grid(row=0, column=0, sticky='e')
entry_latitude = tk.Entry(root)
entry_latitude.grid(row=0, column=1)

tk.Label(root, text="Longitude:").grid(row=1, column=0, sticky='e')
entry_longitude = tk.Entry(root)
entry_longitude.grid(row=1, column=1)

tk.Label(root, text="Radius (km):").grid(row=2, column=0, sticky='e')
entry_radius = tk.Entry(root)
entry_radius.grid(row=2, column=1)

# Categories for selection
categories = [
    ('Shop', 'shop', None),
    ('Office', 'office', None),
    ('Restaurant', 'amenity', 'restaurant'),
    ('Cafe', 'amenity', 'cafe'),
    ('Bar', 'amenity', 'bar'),
    ('Pub', 'amenity', 'pub'),
    ('Fast Food', 'amenity', 'fast_food'),
    ('Bank', 'amenity', 'bank'),
    ('Pharmacy', 'amenity', 'pharmacy'),
    ('Hospital', 'amenity', 'hospital'),
    ('Clinic', 'amenity', 'clinic'),
    ('Dentist', 'amenity', 'dentist'),
    ('Doctors', 'amenity', 'doctors'),
    ('Theatre', 'amenity', 'theatre'),
    ('Cinema', 'amenity', 'cinema'),
    ('Nightclub', 'amenity', 'nightclub'),
    ('Kindergarten', 'amenity', 'kindergarten'),
    ('Library', 'amenity', 'library'),
    ('College', 'amenity', 'college'),
    ('University', 'amenity', 'university'),
    # Additional tags
    ('Parking', 'amenity', 'parking'),
    ('Fuel Station', 'amenity', 'fuel'),
    ('Hotel', 'tourism', 'hotel'),
    ('Motel', 'tourism', 'motel'),
    ('Guest House', 'tourism', 'guest_house'),
    ('Supermarket', 'shop', 'supermarket'),
    ('Convenience Store', 'shop', 'convenience'),
    ('Bakery', 'shop', 'bakery'),
    ('Butcher', 'shop', 'butcher'),
    ('Clothes Store', 'shop', 'clothes'),
    ('Electronics Store', 'shop', 'electronics'),
    ('Furniture Store', 'shop', 'furniture'),
    ('Jewelry Store', 'shop', 'jewelry'),
    ('Sports Shop', 'shop', 'sports'),
    ('Hairdresser', 'shop', 'hairdresser'),
    ('Beauty Salon', 'shop', 'beauty'),
    ('Museum', 'tourism', 'museum'),
    ('Park', 'leisure', 'park'),
    ('ATM', 'amenity', 'atm'),
    ('Post Office', 'amenity', 'post_office'),
    ('Police Station', 'amenity', 'police'),
    ('Fire Station', 'amenity', 'fire_station'),
    ('Embassy', 'amenity', 'embassy'),
    ('Court', 'amenity', 'courthouse'),
    ('Place of Worship', 'amenity', 'place_of_worship'),
    ('Veterinary Clinic', 'amenity', 'veterinary'),
    ('Swimming Pool', 'leisure', 'swimming_pool'),
    ('Gym', 'leisure', 'fitness_centre'),
    ('Playground', 'leisure', 'playground'),
    ('Bus Station', 'amenity', 'bus_station'),
    ('Train Station', 'railway', 'station'),
    ('Airport', 'aeroway', 'aerodrome'),
    ('Taxi Stand', 'amenity', 'taxi'),
    ('Car Rental', 'amenity', 'car_rental'),
    ('Car Wash', 'amenity', 'car_wash'),
    ('Charging Station', 'amenity', 'charging_station'),
    ('School', 'amenity', 'school'),
    ('Casino', 'amenity', 'casino'),
    ('Artwork', 'tourism', 'artwork'),
    ('Information', 'tourism', 'information'),
    ('Viewpoint', 'tourism', 'viewpoint'),
    ('Zoo', 'tourism', 'zoo'),
    ('Theme Park', 'tourism', 'theme_park'),
    ('Water Park', 'leisure', 'water_park'),
]

# Frame for checkboxes
frame_checkboxes = tk.LabelFrame(root, text="Categories to Include")
frame_checkboxes.grid(row=3, column=0, columnspan=2, pady=5)

category_vars = {}
for idx, (display_name, tag, value) in enumerate(categories):
    var = tk.BooleanVar(value=True)  # default to selected
    category_vars[(tag, value)] = var
    checkbox = tk.Checkbutton(frame_checkboxes, text=display_name, variable=var)
    checkbox.grid(row=idx//2, column=idx%2, sticky='w')

# Calculate the number of rows in the checkbox grid
num_rows = (len(categories) + 1) // 2  # Add 1 before division to handle odd number of categories

# Add "Check All" and "Uncheck All" buttons
button_check_all = tk.Button(frame_checkboxes, text="Check All", command=check_all)
button_check_all.grid(row=num_rows, column=0, pady=5)

button_uncheck_all = tk.Button(frame_checkboxes, text="Uncheck All", command=uncheck_all)
button_uncheck_all.grid(row=num_rows, column=1, pady=5)

# Checkbox to exclude entries without phone numbers
var_exclude_no_phone = tk.BooleanVar()
checkbox_exclude_no_phone = tk.Checkbutton(root, text="Exclude entries without phone number", variable=var_exclude_no_phone)
checkbox_exclude_no_phone.grid(row=4, column=0, columnspan=2, pady=5)

button_fetch = tk.Button(root, text="Fetch Businesses", command=fetch_businesses)
button_fetch.grid(row=5, column=0, columnspan=2, pady=5)

button_remove_duplicates = tk.Button(root, text="Remove Duplicate Names", command=remove_duplicates)
button_remove_duplicates.grid(row=6, column=0, columnspan=2, pady=5)

button_save = tk.Button(root, text="Save Data", command=save_data)
button_save.grid(row=7, column=0, columnspan=2, pady=5)

label_counter = tk.Label(root, text="Processed: 0")
label_counter.grid(row=8, column=0, columnspan=2)

root.mainloop()
