from pathlib import Path
from nicegui import ui

from sbe_ctd_proc.analysis.scan_count_checker import create_scan_count_dataframe

def build_scan_counts_view(derive_file: Path):
    df = create_scan_count_dataframe(derive_file)

    ui.label(f'Scanned: {derive_file}')
    ui.table.from_pandas(df)