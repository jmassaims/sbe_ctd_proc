from nicegui import ui

from .dialogs import setup_file_error_dialog, setup_processing_error_dialog
from ..manager import Manager
from ..ctd_file import CTDFile
from .processing_state import PROC_STATE

def select_row(*args, **kwargs):
    print(args, kwargs)

@ui.page('/')
def overview_page():
    mgr = PROC_STATE.mgr

    running_row = ui.row().classes('items-center w-full')
    with running_row:
        ui.button('Start', icon='play_arrow', on_click=PROC_STATE.start_processing) \
            .bind_visibility_from(PROC_STATE, 'is_processing', value=False)
        ui.linear_progress(show_value=False).style('max-width: 400px;') \
            .bind_value_from(PROC_STATE, 'progress') \
            .bind_visibility_from(PROC_STATE, 'is_processing')
        ui.button(icon='stop', color='red', on_click=PROC_STATE.stop_processing) \
            .bind_visibility_from(PROC_STATE, 'is_processing')

    current_row = ui.row()
    current_row.bind_visibility_from(PROC_STATE, 'is_processing')
    with current_row:
        ui.label().bind_text_from(PROC_STATE, 'current_basename')
        ui.label().bind_text_from(PROC_STATE, 'current_serial_number')
        ui.label().bind_text_from(PROC_STATE, 'current_cast_date')
        ui.label().bind_text_from(PROC_STATE, 'current_step')

    @ui.refreshable
    def create_filters():
        toggle = ui.toggle({
            'pending': f'{len(mgr.pending)} Pending',
            'processing': f'{len(mgr.processing)} Processing',
            'done': f'{len(mgr.processed)} Done'
        }, clearable=True)
        toggle.on_value_change(lambda e: table.filter(e.value))

    with ui.row().classes('items-center'):
        # this could work if want multi-toggle, but more work
        #with ui.button_group():
            # ui.button(f'{len(mgr.pending)} Pending', on_click=lambda: foo()).props('outline')
            # ui.button(f'{len(mgr.processing)} Processing')
            # ui.button(f'{len(mgr.processed)} Done')

        create_filters()

        search_input = ui.input('Search')

    table = CTDFilesTable(mgr)
    search_input.bind_value(table.table, 'filter')

    setup_file_error_dialog()
    setup_processing_error_dialog()

    def refresh():
        create_filters.refresh()
        table.refresh()

    mgr.on_change = refresh


def ctdfile_to_row(ctdfile: CTDFile):
    ctdfile.parse_hex()
    ctdfile.refresh_dirs()

    return {
        'base_file_name': ctdfile.base_file_name,
        'serial_number': ctdfile.serial_number,
        'cast_date': ctdfile.cast_date,
        'processed_cnv_count': len(ctdfile.destination_cnvs),
        'processing_cnv_count': len(ctdfile.processing_cnvs),
        'status': ctdfile.status()
    }

class CTDFilesTable:
    filter_status: str | None = None

    def __init__(self, mgr: Manager):
        self.mgr = mgr

        columns = [
            {'name': 'base_file_name', 'label': 'Base Name', 'field': 'base_file_name', 'sortable': True },
            {'name': 'serial_number', 'label': 'Serial#', 'field': 'serial_number', 'sortable': True },
            {'name': 'cast_date', 'label': 'Cast Date', 'field': 'cast_date', 'sortable': True},
            # TODO badge, click to open dir
            # REVIEW what's useful? last step?
            # {'name': 'processed_cnv_count', 'label': 'Processed CNVs', 'field': 'processed_cnv_count', 'sortable': True},
            # {'name': 'processing_cnv_count', 'label': 'Processing CNVs', 'field': 'processing_cnv_count', 'sortable': True},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True}
        ]

        rows = [ctdfile_to_row(row) for row in mgr.ctdfiles]

        # TODO autosort cast_date desc
        table = ui.table(columns=columns, rows=rows, row_key='base_file_name')
        self.table = table

        table.add_slot('body-cell-status', '''
            <q-td key="status" :props="props">
                <q-badge :color="{pending:'blue',processing:'orange',done:'green',unknown:'red'}[props.value]">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')

        # Nicer date format
        # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat
        table.add_slot('body-cell-cast_date', '''
        <q-td key="cast_date" :props="props">
          {{ new Date(props.value).toLocaleString(undefined, {dateStyle:'medium'}) }}
        </q-td>
        ''')

        def click_handler(row):
            name = row['base_file_name']
            ui.navigate.to(f'/ctd_file/{name}')

        # https://nicegui.io/documentation/generic_events
        table.on('rowClick', lambda e: click_handler(e.args[1]), [[], ['base_file_name'], None])

    def filter(self, status: str | None):
        self.filter_status = status

        # always generate new row objects, otherwise table inconsistent about updating
        if status is None:
            all_rows = [ctdfile_to_row(row) for row in self.mgr.ctdfiles]
            self.table.update_rows(all_rows)
        else:
            filtered_rows = [ctdfile_to_row(row) for row in self.mgr.ctdfiles if row.status() == status]
            self.table.update_rows(filtered_rows)

    def refresh(self):
        self.filter(self.filter_status)
