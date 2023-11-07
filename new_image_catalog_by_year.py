#!/usr/bin/env python

import argparse
import os
import glob
import json
from datetime import datetime
from tkinter import messagebox


def find_images(start_year, end_year, search_path, ignore_list):
    if not end_year:
        print("Error: End year is required.")
        exit(1)

    if end_year < start_year:
        print("Error: End year should be greater than or equal to start year.")
        exit(1)

    # Define a list of common image file extensions
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.gif"]
    # Use glob to search for files with those extensions in the search_path directory
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(search_path, "**", ext), recursive=True))

    # Filter the files to only include those modified within the date range and not in the ignore list
    filtered_files = []
    for file_path in files:
        ignore_file_check = False
        for ignore_path in ignore_list:
            if any(os.path.normcase(os.path.abspath(file_path)) == os.path.normcase(os.path.abspath(ignore_path)) or os.path.normcase(file_path).startswith(os.path.normcase(ignore_path)) for ignore_path in ignore_list):
                ignore_file_check = True
                break

        if ignore_file_check:
            continue

        modified_date = datetime.fromtimestamp(os.path.getmtime(file_path))
        if start_year <= modified_date.year <= end_year:
            file_path = file_path.replace("\\", "/")
            filtered_files.append(file_path)

    return filtered_files


# Create the argument parser
parser = argparse.ArgumentParser(description='Search for images within a date range and write metadata to a JSON file.')
parser.add_argument('--catalog_path', required=True, help='Path to the directory where the JSON catalog will be saved.')
parser.add_argument('--search_path', required=True, help='Path to the directory to search for image files.')
parser.add_argument('--start_year', type=int, required=True, help='Starting year of the date range.')
parser.add_argument('--end_year', type=int, required=False, help='Ending year of the date range.')
parser.add_argument('--ignore_file', type=str, required=False, help='Text file name with paths to ignore.')

# Parse the arguments
args = parser.parse_args()

catalog_path = args.catalog_path
search_path = args.search_path
start_year = args.start_year
end_year = args.end_year

# Function to get the unique device ID

def get_device_id(json_file_path):
    try:
        # Read the JSON file and load the data
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)

        # Extract the "device_id" field from the data dictionary
        device_id = data.get("device_id")

        if device_id is None:
            print("Error: 'device_id' not found in the JSON file.")
            return None

        return device_id

    except Exception as e:
        print("Error loading JSON file:", str(e))
        return None


ignore_list = []
device_id = get_device_id("device_id.json")  # Get the device id
print("device_id",device_id)


if args.ignore_file:
    ignore_filename = args.ignore_file
    if os.path.exists(ignore_filename):
        with open(ignore_filename, 'r') as ignore_file:
            ignore_list = [line.rstrip() for line in ignore_file]


print("ignore_list =", ignore_list)
print("Getting catalog items...")
print("start_year=", start_year, "end_year=", end_year,  "catalog_path=", catalog_path, "search_path=", search_path )

# Call the function to search for images within the date range of start_year and end_year
image_files = find_images(start_year, end_year, search_path, ignore_list)

# Create a list of dictionaries for each image file with metadata fields
image_list = []
total_size = 0  # Initialize total size to 0
for file_path in image_files:
    # Get the current datetime as a string
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Get the date modified of the file and convert it to a string representation
    mod_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
    # Create a dictionary with metadata fields, including date modified
    image_dict = {       
        "source": file_path,
        "device_id": device_id,
        "load_date": current_date,
        "date_modified": mod_date,
        "artist": "",
        "title": "",
        "media": "",
        "category": "",
        "location": "",
        "description": "",
        "year_of_work": "",
        "for_sale": "",
        "price": ""
    }
    # Append the dictionary to the list of image objects
    image_list.append(image_dict)
    # Add the file size to the total size
    total_size += os.path.getsize(file_path)
    print("image_dict", image_dict)


# Create a dictionary with the list of image objects
if end_year == start_year:
    base_name = f"detail_{start_year}"
else:
    base_name = f"detail_{start_year}_{end_year}"
output_dict = {
    base_name: image_list
}

# Write the dictionary to a JSON file
output_filename = f"{base_name}.json"
output_file_path = os.path.join(catalog_path, output_filename)
print("output_file_path = ", output_file_path)

if os.path.exists(output_file_path):
    while True:
        choice = messagebox.askquestion("File Exists", f"File '{output_filename}' already exists. Do you want to replace it?")
        if choice == 'yes':
            os.remove(output_file_path)
            break
        elif choice == 'no':
            messagebox.showinfo("Exiting Program", "Exiting program...")
            exit(0)
        else:
            messagebox.showwarning("Invalid Choice", "Invalid choice. Please select 'Yes' or 'No'.")

with open(output_file_path, "w") as json_file:
    json.dump(output_dict, json_file)

# Convert total size to megabytes and gigabytes
total_size_mb = total_size / (1024 * 1024)
total_size_gb = total_size_mb / 1024

# Print a message indicating that the output has been written to the JSON file, along with the total number of files and total size
print(f"Image file paths written to {catalog_path}{output_filename}")
print(f"Total number of images: {len(image_files)}")
print(f"Total size: {total_size} bytes, {total_size_mb:.2f} MB, {total_size_gb:.2f} GB")
messagebox.showinfo("Catalog Created", output_filename)


    
# End of script

