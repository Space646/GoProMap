import json
import subprocess
from pathlib import Path
import re

def dms_to_decimal(degrees, minutes, seconds, direction):
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if direction in ['S', 'W']:  # South or West should be negative
        decimal = -decimal
    return decimal

def parse_gps_coordinates(coord_str):
    pattern = r"(\d+)\s*deg\s*(\d+)'?\s*(\d+(\.\d+)?)\"?\s*([NSEW])"
    match = re.match(pattern, coord_str.strip())
    
    if match:
        degrees, minutes, seconds, _, direction = match.groups()
        return dms_to_decimal(degrees, minutes, seconds, direction)
    else:
        raise ValueError(f"Invalid coordinate format: {coord_str}")

def extract_gps_trace_with_exiftool(file_path):
    if not Path(file_path).is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        result = subprocess.run(
            ["exiftool", "-ee", "-gps*", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running ExifTool: {e.stderr.strip()}")

    raw_output = result.stdout
    gps_trace = []
    current_entry = {}
    for line in raw_output.splitlines():
        if line.startswith("GPS Date Time"):
            current_entry["datetime"] = line.split(":", 1)[1].strip()
        elif line.startswith("GPS Latitude"):
            latitude_str = line.split(":", 1)[1].strip()
            try:
                current_entry["latitude"] = parse_gps_coordinates(latitude_str)
            except ValueError as e:
                print(f"Error parsing latitude: {e}")
        elif line.startswith("GPS Longitude"):
            longitude_str = line.split(":", 1)[1].strip()
            try:
                current_entry["longitude"] = parse_gps_coordinates(longitude_str)
            except ValueError as e:
                print(f"Error parsing longitude: {e}")
        elif line.startswith("GPS Altitude"):
            altitude = line.split(":", 1)[1].strip()
            try:
                current_entry["altitude"] = float(altitude.split()[0])
            except ValueError:
                current_entry["altitude"] = None

        if {"datetime", "latitude", "longitude", "altitude"} <= current_entry.keys():
            gps_trace.append(current_entry)
            current_entry = {}

    if not gps_trace:
        print("No GPS data found in the file.")
    return gps_trace

def save_gps_trace_to_json(gps_trace, output_path):
    with open(output_path, 'w') as json_file:
        json.dump(gps_trace, json_file, indent=4)

def files_are_different(file1, gps_trace):
    """Compare an existing JSON file with the new GPS trace data."""
    with open(file1, 'r') as f1:
        existing_data = json.load(f1)

    # Compare existing data with the new GPS trace (serialize gps_trace)
    return existing_data != gps_trace

def process_multiple_files(input_folder):
    # Get the directory where the script is located
    script_dir = Path(__file__).parent

    # Define the output folder path in the same location as the script
    output_folder = script_dir / "gps_data"
    
    # Create output folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)

    # Iterate through all MP4 files in the input folder
    for file_path in Path(input_folder).glob("*.MP4"):
        print(f"Processing {file_path.name}...")
        
        try:
            gps_trace = extract_gps_trace_with_exiftool(file_path)
            if gps_trace:
                output_file = output_folder / f"{file_path.stem}.json"
                
                # If the JSON file exists, compare its contents with the new data
                if output_file.exists():
                    if files_are_different(output_file, gps_trace):
                        print(f"Data for {file_path.name} differs from the existing JSON file!")
                        print(f"Exiting the script because data has changed.")
                        return  # Exit the script
                    else:
                        print(f"The data for {file_path.name} is the same as the existing file.")
                else:
                    save_gps_trace_to_json(gps_trace, output_file)
                    print(f"GPS trace saved to {output_file}")
            else:
                print(f"No GPS data found for {file_path.name}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    input_folder = "Insert your GoPro footage folder path here"  # Folder containing GoPro files

    process_multiple_files(input_folder)
