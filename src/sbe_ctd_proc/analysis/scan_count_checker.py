"""
intention is to adapt this to either step through full range of derived files,
or to add this as a step to the CTD processing code

The funtion of this code is to scrape out all data being used for the bin down step (but prior to, ie in the derive step),
and return values for the scan counts.
the bin down step is interpolating values, and hence does not give an accurate representation of whether
soak data was included in the bin. by assesing the difference between min and max scan count for each bin we can
infer whether the cast data is close in time.

"""

from pathlib import Path
import pandas as pd

def create_scan_count_dataframe(input_file: str | Path) -> pd.DataFrame:
    """Create a new DataFrame with columns:
    Depth_bin, min_scan_count, max_scan_count, difference.

    File should typiically end in D (derive), but this is not checked.
    """

    # Initialize variables to store column numbers
    depSM_column = None
    flag_column = None
    scan_count_column = None

    # Open the .cnv file for reading
    with open(input_file, 'r') as file:
        # Read all lines from the file
        lines = file.readlines()

        # Iterate through each line in the file to find column numbers
        for line in lines:
            # Check if the line contains the desired phrases
            if "depSM" in line:
                depSM_column = int(line.split('=')[0].split()[-1]) + 1
            elif "flag: flag" in line:
                flag_column = int(line.split('=')[0].split()[-1]) + 1
            elif "scan: Scan Count" in line:
                scan_count_column = int(line.split('=')[0].split()[-1]) + 1

            # If all column numbers are found, break the loop
            if depSM_column is not None and flag_column is not None and scan_count_column is not None:
                break

        # Initialize lists to store the extracted columns
        depSM_data = []
        flag_data = []
        scan_count_data = []

        # Iterate through each line in the file to extract data columns
        for line in lines:
            # Skip lines that start with '*' or '#'
            if line.startswith('*') or line.startswith('#'):
                continue

            # Split the line into columns based on whitespace
            columns = line.split()

            # Extract the columns using the previously determined column numbers
            if len(columns) >= max(depSM_column, flag_column, scan_count_column):
                depSM_data.append(columns[depSM_column - 1])
                flag_data.append(columns[flag_column - 1])
                scan_count_data.append(columns[scan_count_column - 1])

    # Create a DataFrame from the extracted data
    data = pd.DataFrame({
        'depSM': depSM_data,
        'flag': flag_data,
        'scan_count': scan_count_data
    })

    # Convert flag column to numeric
    data['flag'] = pd.to_numeric(data['flag'], errors='coerce')
    data['scan_count'] = pd.to_numeric(data['scan_count'], errors='coerce')

    # Filter out rows where the value in the flag column is less than 0
    data = data[data['flag'] >= 0]

    # Add a new column rounding the depSM values to the nearest whole number
    data['Depth_bin'] = data['depSM'].astype(float).round()

    # Group by Depth_bin and aggregate to find the minimum and maximum scan_count values
    aggregated_data = data.groupby('Depth_bin').agg(min_scan_count=('scan_count', 'min'), max_scan_count=('scan_count', 'max'))

    # Reset index to make Depth_bin a column instead of an index
    aggregated_data.reset_index(inplace=True)

    # Calculate the difference between min_scan_count and max_scan_count
    aggregated_data['difference'] = aggregated_data['max_scan_count'] - aggregated_data['min_scan_count']

    return aggregated_data
