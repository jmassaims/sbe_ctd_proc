"""
This code is for proofing the bin_down file by checking for negative values introduced by the interpolation step.
"""

input_file = "C:\\Users\\jmassuge\\Documents\\wqq660_filter_align_celltm_loop_wild_derive_bin_down.cnv"

def check_for_negatives(input_file):
    with open(input_file, 'r') as file:
        # Read lines, ignoring those starting with * or #
        lines = [line for line in file if not line.startswith('*') and not line.startswith('#')]

    # Remove leading and trailing whitespace, split each line by whitespace
    data = [line.strip().split() for line in lines]

    # Transpose the data to iterate over columns
    columns = zip(*data)

    negative_columns = []
    for i, column in enumerate(columns):
        # Check if any value in the column is negative
        if any(float(value) < 0 for value in column):
            negative_columns.append(i)

    if negative_columns:
        print("Negative values found in columns:", negative_columns)
    else:
        print("No negative values found in any column.")


check_for_negatives(input_file)
