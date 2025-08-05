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

def get_binavg_skipover(bin_file: str | Path) -> int:
    """Extracts the binavg_skipover value from a binned file."""
    with open(bin_file, 'r') as f:
        for line in f:
            if line.strip().startswith('# binavg_skipover'):
                try:
                    return int(line.strip().split('=')[1].strip())
                except (IndexError, ValueError):
                    raise ValueError(f"Invalid format for binavg_skipover in {bin_file}")
    return 0  # Default to 0 if not found

def create_scan_count_dataframe(input_file: str | Path, bin_file: str | Path) -> pd.DataFrame:
    """Create a DataFrame showing scan count spread for each depth bin, skipping rows from binavg_skipover."""

    # Initialize variables to store column numbers
    depSM_column = None
    flag_column = None
    scan_count_column = None

    # Open the .cnv file for reading
    with open(input_file, 'r') as file:
        lines = file.readlines()

        for line in lines:
            if "depSM" in line:
                depSM_column = int(line.split('=')[0].split()[-1]) + 1
            elif "flag: flag" in line:
                flag_column = int(line.split('=')[0].split()[-1]) + 1
            elif "scan: Scan Count" in line:
                scan_count_column = int(line.split('=')[0].split()[-1]) + 1

            if depSM_column and flag_column and scan_count_column:
                break

        depSM_data = []
        flag_data = []
        scan_count_data = []

        for line in lines:
            if line.startswith('*') or line.startswith('#'):
                continue

            columns = line.split()
            if len(columns) >= max(depSM_column, flag_column, scan_count_column):
                depSM_data.append(columns[depSM_column - 1])
                flag_data.append(columns[flag_column - 1])
                scan_count_data.append(columns[scan_count_column - 1])

    data = pd.DataFrame({
        'depSM': depSM_data,
        'flag': flag_data,
        'scan_count': scan_count_data
    })

    data['flag'] = pd.to_numeric(data['flag'], errors='coerce')
    data['scan_count'] = pd.to_numeric(data['scan_count'], errors='coerce')
    data['depSM'] = pd.to_numeric(data['depSM'], errors='coerce')

    #Get skipover count and apply
    skip_count = get_binavg_skipover(bin_file)
    if skip_count > 0:
        data = data.iloc[skip_count:].reset_index(drop=True)

    # Filter flagged data
    data = data[data['flag'] >= 0].reset_index(drop=True)

    # Add Depth_bin and aggregate
    data['Depth_bin'] = data['depSM'].round()
    aggregated_data = data.groupby('Depth_bin').agg(
        min_scan_count=('scan_count', 'min'),
        max_scan_count=('scan_count', 'max')
    ).reset_index()

    aggregated_data['difference'] = aggregated_data['max_scan_count'] - aggregated_data['min_scan_count']

    return aggregated_data
