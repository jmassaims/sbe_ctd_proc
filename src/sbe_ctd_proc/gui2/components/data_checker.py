from pathlib import Path
from nicegui import ui

from seabirdscientific.instrument_data import MeasurementSeries

def build_negative_cols_view(file: Path, negative_cols: list[MeasurementSeries]):
    ui.label(f'Scanned: {file}')
    ui.label(f'Negative values found in {len(negative_cols)} columns.')
    if negative_cols:
        # ui.label(f'Negative values found in columns: {negative_cols}')
        for col in negative_cols:
            ui.label(col.label).classes('text-h5')
            ui.label(f'{col.description} ({col.units})')
            neg_values = list(float(x) for x in col.values if float(x) < 0)
            ui.label(f'Negative values: {neg_values}')

    else:
        ui.label('No negative values found in any column.')
