import dataclasses
from nicegui import ui
from sbe_ctd_proc.config import CONFIG
from sbe_ctd_proc.ctd_file import CTDFile
from ..widgets import error_message

@ui.refreshable
def build_file_info_summary_view(ctdfile: CTDFile | None):
    if ctdfile is None:
        ui.label('Loading...')
        return

    # CTDFile info table
    cols = [
        {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True },
        {'name': 'value', 'label': 'Value', 'field': 'value', 'required': True }
    ]
    rows = [
        { 'name': 'Hex path', 'value': str(ctdfile.hex_path) },
        { 'name': 'Cast date', 'value': ctdfile.cast_date},
        { 'name': 'Cast date type', 'value': str(ctdfile.cast_date_type)},
        { 'name': 'Serial Number', 'value': str(ctdfile.serial_number)},
        { 'name': 'Status', 'value': str(ctdfile.status())},
    ]

    ui.table(columns=cols, rows=rows, row_key='name', title='CTDFile (used for processing)')\
        .props('hide-header')

    # HexInfo dates table
    hexinfo = ctdfile.info

    cast_line = hexinfo.find_unknown_line("* cast ")
    if cast_line:
        ui.label(f'cast line: {cast_line}')

    rows = []
    for val in hexinfo.get_all_dates().values():
        rows.append(val)

    cols = [
        {'name': 'name', 'label': 'Name', 'field': 'key', 'required': True },
        {'name': 'value', 'label': 'Value', 'field': 'datetime', 'required': True },
        {'name': 'value', 'label': 'RAW line', 'field': 'line', 'required': True }
    ]

    ui.table(columns=cols, rows=rows, row_key='name', title='Hex file Known Dates')

    # Database table
    db = CONFIG.get_db()
    if db:
        try:
            data = db.get_ctd_data(ctdfile.base_file_name)

            rows = []
            for f in dataclasses.fields(data):
                value = getattr(data, f.name)
                rows.append({'name': f.name, 'value': value})

            ui.table(rows=rows, row_key='name', title='Database').props('hide-header')
        except LookupError as e:
            ui.label('Database').classes('text-h5')
            error_message(str(e))
