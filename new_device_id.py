import socket
import json
from datetime import datetime
import uuid

def create_workstation_info_json(file_path):
    # Get the hostname of the workstation
    hostname = socket.gethostname()

    # Generate a globally unique identifier (UUID)
    device_id = str(uuid.uuid4())

    # Get the current datetime as a string
    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create a dictionary with the workstation information
    workstation_info = {
        "hostname": hostname,
        "device_id": device_id,
        "create_date": create_date
    }

    # Write the dictionary to a JSON file
    with open(file_path, "w") as json_file:
        json.dump(workstation_info, json_file, indent=4)

if __name__ == "__main__":
    # Specify the file path for the JSON file
    json_file_path = "device_id.json"

    # Call the function to create the JSON file
    create_workstation_info_json(json_file_path)

    print(f"Workstation information has been saved to '{json_file_path}'.")
