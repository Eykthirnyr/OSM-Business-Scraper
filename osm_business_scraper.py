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

def fetch_businesses():
    try:
        latitude = float(entry_latitude.get())
        longitude = float(entry_longitude.get())
        radius = float(entry_radius.get())  # Radius in kilometers
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numerical values.")
        return

    # Build the Overpass API query to fetch only businesses
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node
        (around:{radius * 1000},{latitude},{longitude})
        ["name"]
        ["shop"];
      node
        (around:{radius * 1000},{latitude},{longitude})
        ["name"]
        ["amenity"~"restaurant|cafe|bar|pub|fast_food|bank|pharmacy|hospital|clinic|dentist|doctors|theatre|cinema|nightclub|kindergarten|library|college|university"];
      node
        (around:{radius * 1000},{latitude},{longitude})
        ["name"]
        ["office"];
      way
        (around:{radius * 1000},{latitude},{longitude})
        ["name"]
        ["shop"];
      way
        (around:{radius * 1000},{latitude},{longitude})
        ["name"]
        ["amenity"~"restaurant|cafe|bar|pub|fast_food|bank|pharmacy|hospital|clinic|dentist|doctors|theatre|cinema|nightclub|kindergarten|library|college|university"];
      way
        (around:{radius * 1000},{latitude},{longitude})
        ["name"]
        ["office"];
    );
    out center;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    global all_results  # Make all_results global to access it in other functions
    all_results = []
    processed_count = 0

    for element in data['elements']:
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

# Checkbox to exclude entries without phone numbers
var_exclude_no_phone = tk.BooleanVar()
checkbox_exclude_no_phone = tk.Checkbutton(root, text="Exclude entries without phone number", variable=var_exclude_no_phone)
checkbox_exclude_no_phone.grid(row=3, column=0, columnspan=2, pady=5)

button_fetch = tk.Button(root, text="Fetch Businesses", command=fetch_businesses)
button_fetch.grid(row=4, column=0, columnspan=2, pady=5)

button_remove_duplicates = tk.Button(root, text="Remove Duplicate Names", command=remove_duplicates)
button_remove_duplicates.grid(row=5, column=0, columnspan=2, pady=5)

button_save = tk.Button(root, text="Save Data", command=save_data)
button_save.grid(row=6, column=0, columnspan=2, pady=5)

label_counter = tk.Label(root, text="Processed: 0")
label_counter.grid(row=7, column=0, columnspan=2)

root.mainloop()
