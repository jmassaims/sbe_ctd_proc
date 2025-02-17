"""
This code is for proofing the bin_down file by checking for negative values introduced by the interpolation step.
"""

from pathlib import Path

def check_for_negatives(cnv_file: str | Path) -> list[str]:
    """
    Check for negative values in the bin-down CNV file.
    @returns list of columns with negative values
    """
    with open(cnv_file, 'r') as file:
        # Read lines, ignoring those starting with * or #
        lines = [line for line in file if not line.startswith('*') and not line.startswith('#')]

    # Remove leading and trailing whitespace, split each line by whitespace
    data = [line.strip().split() for line in lines]

    # Remove empty rows, otherwise zip fails
    def not_empty(row):
        return len(row) > 0
    data = filter(not_empty, data)

    # Transpose the data to iterate over columns
    columns = zip(*data)

    negative_columns = []
    for i, column in enumerate(columns):
        # Check if any value in the column is negative
        if any(float(value) < 0 for value in column):
            negative_columns.append(i)

    if negative_columns:
        return negative_columns
    else:
        return []
