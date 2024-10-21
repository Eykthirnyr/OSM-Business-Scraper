# OpenStreetMap Business Scraper

A Python application with a graphical user interface (GUI) that allows you to fetch business information from **OpenStreetMap** within a specified radius around given coordinates. Features include filtering businesses with or without phone numbers, removing duplicate entries, and exporting the results to an Excel file.

**Features**

**Graphical User Interface (GUI):** Easy-to-use interface built with Tkinter.

**Fetch Business Data:** Retrieve businesses from OpenStreetMap within a specified radius.

**Filter Options:**

Exclude entries without phone numbers.

Remove duplicate business names.

**Data Export:** Save the collected data to an Excel file (businesses.xlsx).

**Automatic Dependency Installation:** The script checks for required modules and installs them if missing.

**Prerequisites**

**Python 3.x** installed on your system.

Internet connection to access the Overpass API.

**Installation**

**Install Dependencies:**

The script will automatically check and install missing dependencies when you run it. Alternatively, you can manually install the required packages:

pip install requests tkinter openpyxl

**Note:** On some systems, you may need to use pip3 instead of pip.

**Fetching Businesses**

**Enter Coordinates:**

**Latitude:** Enter the latitude of the center point.

**Longitude:** Enter the longitude of the center point.

**Enter Radius:**

**Radius (km):** Specify the radius around the center point in kilometers.

**Fetch Businesses:**

Click the **"Fetch Businesses"** button to retrieve data.

**Excluding Entries Without Phone Numbers**

**Exclude Entries Without Phone Number:**

Check the box labeled **"Exclude entries without phone number"** if you want to filter out businesses that do not have a phone number listed.

**Removing Duplicate Names**

**Remove Duplicate Names:**

After fetching businesses, click the **"Remove Duplicate Names"** button to eliminate entries with duplicate names from the dataset.

**Saving Data**

**Save Data:**

Click the **"Save Data"** button to export the processed data to an Excel file (businesses.xlsx).

**Output**

The application saves the collected business data to an Excel file named **businesses.xlsx** in the project directory.

The Excel file includes the following columns:

**Name:** The name of the business.

**Address:** The address constructed from available OpenStreetMap tags.

**Phone:** The phone number of the business (if available).

**Dependencies**

The script uses the following Python libraries:

**requests:** For making HTTP requests to the Overpass API.

**tkinter****:** For building the graphical user interface.

**openpyxl****:** For creating and manipulating Excel files.

The script includes a dependency check and will attempt to install any missing modules automatically.

**Acknowledgments**

**OpenStreetMap Contributors:** This application uses data from OpenStreetMap, which is made available under the Open Database License (ODbL).

**Overpass API:** For providing the API to query OpenStreetMap data.

**Attribution:** Contains information from OpenStreetMap, which is made available here under the Open Database License (ODbL).



**Disclaimer:** This application is intended for educational and personal use. Ensure compliance with the Open Database License (ODbL) when using and sharing the data collected by this application.

