"""
This code is for proofing the bin_down file by checking for negative values introduced by the interpolation step.
"""

from seabirdscientific.instrument_data import cnv_to_instrument_data, MeasurementSeries

from pathlib import Path

def check_for_negatives(cnv_file: str | Path) -> list[MeasurementSeries]:
    """
    Check for negative values in the bin-down CNV file.
    @returns list of columns (seabirdscientific MeasurementSeries) with negative values
    """
    instr_data = cnv_to_instrument_data(Path(cnv_file))

    negative_columns = []

    for id, m in instr_data.measurements.items():
        if any(float(value) < 0 for value in m.values):
            negative_columns.append(m)

    if negative_columns:
        return negative_columns
    else:
        return []
