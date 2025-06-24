from pathlib import Path
from nicegui import ui

from seabirdscientific.instrument_data import MeasurementSeries

from sbe_ctd_proc.analysis.data_checker import DataChecker
from ..widgets import error_message

def build_data_checker_view(data_checker: DataChecker):
    ui.label('Negative Values').classes('text-h5')
    ui.label(f'Scanned: {data_checker.scanned_bin_file}')

    if data_checker.check_for_negatives_error:
        error_message(str(data_checker.check_for_negatives_error))

    negative_cols = data_checker.negative_cols
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


    # if 2 database dates
    ui.label('Cast Dates sanity check').classes('text-h5')

    if data_checker.check_cast_dates_error:
        error_message(str(data_checker.check_cast_dates_error))
    else:
        ui.label(f'Cast Date from hex file: {data_checker.file_cast_date}')
        ui.label(f'Cast Date from database: {data_checker.db_cast_date}')
        hours_apart = data_checker.date_diff_seconds / 3600
        is_over_limit = data_checker.date_diff_limit and data_checker.date_diff_seconds > data_checker.date_diff_limit

        with ui.row():
            label = ui.label(f'Date difference: {hours_apart:.1f} hours')
            if is_over_limit:
                label.classes('text-bold')
                ui.icon('warning', color='red', size='1.5rem')
