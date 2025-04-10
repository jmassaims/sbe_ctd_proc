import dataclasses
from nicegui import ui
from sbe_ctd_proc.config import CONFIG
from sbe_ctd_proc.ctd_file import CTDFile

@ui.refreshable
def build_file_info_summary_view(ctdfile: CTDFile | None):
    if ctdfile is None:
        ui.label('Loading...')
        return

    cols = [
        {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True },
        {'name': 'value', 'label': 'Value', 'field': 'value', 'required': True }
    ]
    rows = [
        { 'name': 'Hex path', 'value': str(ctdfile.hex_path) },
        { 'name': 'Cast date', 'value': str(ctdfile.cast_date)},
        { 'name': 'Cast date type', 'value': str(ctdfile.cast_date_type)},
        { 'name': 'Serial Number', 'value': str(ctdfile.serial_number)},
        { 'name': 'Status', 'value': str(ctdfile.status())},
    ]

    ui.table(columns=cols, rows=rows, row_key='name', title='CTDFile (used during processing)')\
        .props('hide-header')

    db = CONFIG.get_db()
    if db:
        data = db.get_ctd_data(ctdfile.base_file_name)

        rows = []
        for f in dataclasses.fields(data):
            value = getattr(data, f.name)
            rows.append({'name': f.name, 'value': str(value)})

        ui.table(rows=rows, row_key='name', title='Database').props('hide-header')
