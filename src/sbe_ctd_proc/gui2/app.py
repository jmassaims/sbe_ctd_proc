import plotly.graph_objects as go
from nicegui import ui

from ..config import CONFIG
from ..manager import Manager
from ..ctd_file import CTDFile
from ..viz_cnv import plot_for_cnv_file

def select_row(*args, **kwargs):
    print(args, kwargs)

def build_ui():
    build_ctdfiles_table()


def ctdfile_to_row(ctdfile: CTDFile):
    ctdfile.parse_hex()
    ctdfile.refresh_dirs()

    return {
        'base_file_name': ctdfile.base_file_name,
        'serial_number': ctdfile.serial_number,
        'cast_date': ctdfile.cast_date,
        'processed_cnv_count': len(ctdfile.destination_cnvs),
        'processing_cnv_count': len(ctdfile.processing_cnvs)
    }

def build_ctdfiles_table():
    mgr = Manager()
    mgr.scan_dirs()


    columns = [
        {'name': 'base_file_name', 'label': 'Base Name', 'field': 'base_file_name' },
        {'name': 'serial_number', 'label': 'Serial#', 'field': 'serial_number', 'sortable': True },
        {'name': 'cast_date', 'label': 'Cast Date', 'field': 'cast_date', 'sortable': True},
        # TODO badge, click to open dir
        {'name': 'processed_cnv_count', 'label': 'Processed CNVs', 'field': 'processed_cnv_count', 'sortable': True},
        {'name': 'processing_cnv_count', 'label': 'Processing CNVs', 'field': 'processing_cnv_count', 'sortable': True}
    ]

    rows = [ctdfile_to_row(row) for row in mgr.ctdfiles]

    # TODO autosort cast_date desc
    table = ui.table(columns=columns, rows=rows, row_key='base_file_name')

    # TODO nicer date format
#     table.add_slot('body-cell-cast_date', '''
#     <q-td key="cast_date" :props="props">
#         <q-badge>
#             {{ props.value }}
#         </q-badge>
#     </q-td>
# ''')

    def click_handler(row):
        name = row['base_file_name']
        ui.navigate.to(f'/ctd_file/{name}')

    # https://nicegui.io/documentation/generic_events
    table.on('rowClick', lambda e: click_handler(e.args[1]), [[], ['base_file_name'], None])
