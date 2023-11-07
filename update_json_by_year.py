import argparse
import os
import glob
import json
from datetime import datetime

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
    # Filter the files to only include those modified within the date range and not in the ignore_list
    filtered_files = []
    for file_path in files:

        ignore_file_check = False
        for ignore_path in ignore_list:
            if os.path.abspath(file_path) == os.path.abspath(ignore_path) or os.path.commonpath([os.path.abspath(file_path), os.path.abspath(ignore_path)]) == os.path.abspath(ignore_path):
                ignore_file_check = True
                break

        if ignore_file_check:
            continue       
       
       
        modified_date = datetime.fromtimestamp(os.path.getmtime(file_path))
        if start_year <= modified_date.year <= end_year and file_path not in ignore_list:
            file_path = file_path.replace("\\", "/")
            filtered_files.append(file_path)
            
    return filtered_files


# Create the argument parser
parser = argparse.ArgumentParser(description='Search for images within a date range and write metadata to a JSON file.')
parser.add_argument('--catalog_file_path', required=True, help='Full path to the JSON catalog file.')
parser.add_argument('--search_path', required=True, help='Path to the directory to search for image files.')
parser.add_argument('--ignore_file', type=str, required=False, help='Text file name with paths to ignore.')

# Parse the arguments
args = parser.parse_args()

catalog_file_path = args.catalog_file_path
search_path = args.search_path
ignore_file = args.ignore_file
print("ignore_file=", ignore_file)

# Extract start_year and end_year from the catalog_file_path
base_name = os.path.basename(catalog_file_path)
base_name = os.path.splitext(base_name)[0]
years = base_name.split('_')[1:]
if len(years) == 1:
    start_year = end_year = int(years[0])
else:
    start_year = int(years[0])
    end_year = int(years[1])


# Function to get the device_id

def get_device_id(catalog_file_path):
    try:
        # Read the JSON file and load the data
        with open(catalog_file_path, encoding='utf-8') as json_file:
            
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


device_id = get_device_id("device_id.json")  # Get the device id
print("device_id",device_id)
ignore_list = []

if args.ignore_file:
    ignore_filename = args.ignore_file
    if os.path.exists(ignore_filename):
        with open(ignore_filename, encoding='utf-8') as ignore_file:
            ignore_list = [line.rstrip() for line in ignore_file]
            print("ignore_list=", ignore_list)


print("Getting catalog items...")

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

# Create a dictionary with the list of image objects
if end_year == start_year:
    base_name = f"detail_{start_year}"
else:
    base_name = f"detail_{start_year}_{end_year}"
output_dict = {
    base_name: image_list
}
# Load the existing catalog file
existing_catalog_path = catalog_file_path
if os.path.exists(existing_catalog_path):
    with open(existing_catalog_path, encoding='utf-8') as json_file:
        existing_catalog = json.load(json_file)
else:
    existing_catalog = {}

# Loop through the image dictionaries in the temporary catalog and check if the file path already exists in the existing catalog
for image_dict in output_dict[base_name]:
    source_path = image_dict["source"]
    if source_path not in [existing_image_dict["source"] for existing_image_dict in existing_catalog.get(base_name, [])] and not any(ignore_path in source_path for ignore_path in ignore_list):
        print("source_path =", source_path)
        # If the file path does not exist and is not in the ignore_list, append the new dictionary to the existing catalog
        existing_catalog.setdefault(base_name, []).append(image_dict)


# Write the updated catalog to the file
with open(existing_catalog_path, "w") as json_file:
    json.dump(existing_catalog, json_file, indent=4)

# Convert total size to megabytes and gigabytes
total_size_mb = total_size / (1024 * 1024)
total_size_gb = total_size_mb / 1024
print(f"Total number of images: {len(image_files)}")
print(f"Total size: {total_size} bytes, {total_size_mb:.2f} MB, {total_size_gb:.2f} GB")

print("Done.")
