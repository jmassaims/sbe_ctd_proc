import logging
import os
from pathlib import Path
from typing import Callable
from nicegui import ui

from .dialogs import setup_file_error_dialog, setup_processing_error_dialog, setup_latitude_dialog
from ..manager import Manager
from ..ctd_file import CTDFile, FileStatus
from .processing_state import PROC_STATE

default_proc_button_label = 'Process All Raw'

def select_row(*args, **kwargs):
    print(args, kwargs)

@ui.page('/')
def overview_page():
    mgr = PROC_STATE.mgr

    async def start():
        await PROC_STATE.start_processing(table.get_selected())

    def go_approve():
        first_processing = next(iter(table.mgr.processing))
        ui.navigate.to(f'/ctd_file/{first_processing}')

    def explore(path: Path):
        os.startfile(path)

    running_row = ui.row().classes('items-center w-full')
    with running_row:
        with ui.button(icon='folder_open', color='white'):
            with ui.menu() as menu:
                ui.menu_item('Open raw directory', lambda: explore(mgr.raw_dir))
                ui.menu_item('Open processing directory', lambda: explore(mgr.processing_dir))
                ui.menu_item('Open approved directory', lambda: explore(mgr.approved_dir))

        proc_button = ui.button(default_proc_button_label, icon='play_arrow', on_click=start) \
            .bind_visibility_from(PROC_STATE, 'is_processing', value=False)

        # button visibility bound to if any files processing below.
        approve_button = ui.button('Start Approving', color='green', on_click=go_approve)

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
            'ALL': 'ALL',
            FileStatus.RAW: f'{len(mgr.raw)} Raw',
            FileStatus.PROCESSING: f'{len(mgr.processing)} Processing',
            FileStatus.APPROVED: f'{len(mgr.approved)} Approved'
        }, value='ALL')
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
    approve_button.bind_visibility_from(table, 'has_processing')

    setup_file_error_dialog()
    setup_processing_error_dialog()
    setup_latitude_dialog()

    # use ui.notify to show user messages from processing.
    # they overlay each other, so may need to change UI if more messages are added.
    def check_usermsgs():
        if PROC_STATE.user_messages:
            last_msg = PROC_STATE.user_messages.pop()
            ui.notify(last_msg)
    ui.timer(0.5, check_usermsgs)

    def refresh():
        """refresh UI to represent current Manager state"""
        create_filters.refresh()
        table.refresh()

    mgr.on_change = refresh

    def update_proc_button(selection):
        distinct_status = set(s['status'] for s in selection)
        one_status = len(distinct_status) == 1
        # TODO change status values soon. variables names chosen for future status
        is_raw = FileStatus.RAW in distinct_status
        # TODO processing/partial (future status values)
        is_processing = FileStatus.PROCESSING in distinct_status
        is_approved = FileStatus.APPROVED in distinct_status

        if one_status and is_processing:
            label = 'Reprocess Selected'
        elif one_status and is_raw:
            label = 'Process Selected'
        elif is_raw and is_processing:
            label = '[Re]Process Selected'
        elif is_approved:
            # TODO:P3 better UI when selected approved
            # file processing code skips approved files.
            # probably better to show message that selected Approved files are skipped.
            label = 'Reprocess Approved does nothing!'
        else:
            # button  action should default to process raw.
            label = default_proc_button_label

        proc_button.set_text(label)


    table.on_select = update_proc_button


def ctdfile_to_row(ctdfile: CTDFile) -> dict:
    """Extract dictionary of information for use in the table.
    Errors are caught to prevent crashing the app; in that case a dict with only
    base_file_name and status='error' is returned.
    """
    try:
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
    except Exception:
        logging.exception(f'Error extracting CTDFile info for table: "{ctdfile.base_file_name}"')

        return {
            'base_file_name': ctdfile.base_file_name,
            'status': 'error'
        }

class CTDFilesTable:
    filter_status: str | None = None

    # called when selection changes. given the selected objects created for table.
    on_select: Callable | None

    # if any files trocked by Manager are processing.
    # TODO maybe move to Manager
    has_processing: bool

    def __init__(self, mgr: Manager):
        self.mgr = mgr
        self.on_select = None
        self.has_processing = len(mgr.processing) > 0

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
        table = ui.table(columns=columns, rows=rows, row_key='base_file_name', selection='multiple',
                         on_select=lambda : self.__on_select())

        self.table = table

        table.add_slot('body-cell-status', '''
            <q-td key="status" :props="props">
                <q-badge :color="{raw:'grey',processing:'blue',approved:'green',ambiguous:'red'}[props.value]">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')

        # Nicer date format
        # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat
        # props.value null if Python None value.
        table.add_slot('body-cell-cast_date', '''
        <q-td key="cast_date" :props="props">
          {{ props.value ? new Date(props.value).toLocaleString(undefined, {dateStyle:'medium'}) : ''}}
        </q-td>
        ''')

        def click_handler(row):
            name = row['base_file_name']
            ui.navigate.to(f'/ctd_file/{name}')

        # https://nicegui.io/documentation/generic_events
        table.on('rowClick', lambda e: click_handler(e.args[1]), [[], ['base_file_name'], None])

    def filter(self, status: str | None):
        """Filter the tables rows matching the status.
        processing translates to (processing || processed)
        """
        # translate fake ALL status
        if status == 'ALL':
            status = None

        self.filter_status = status

        # always generate new row objects, otherwise table inconsistent about updating
        if status is None:
            all_rows = [ctdfile_to_row(row) for row in self.mgr.ctdfiles]
            self.table.update_rows(all_rows)
        else:
            # this will error if status string invalid
            s = FileStatus(status)

            def include(ctdfile: CTDFile):
                return ctdfile.status() == s

            filtered_rows = [ctdfile_to_row(f) for f in self.mgr.ctdfiles if include(f)]
            self.table.update_rows(filtered_rows)

        # above resets selection, but does not trigger on_select
        self.__on_select()

    def refresh(self):
        """refresh to represent current Manager state"""
        self.has_processing = len(self.mgr.processing) > 0
        self.filter(self.filter_status)

    def get_selected(self):
        """get selected base file names"""
        return [row['base_file_name'] for row in self.table.selected]

    def __on_select(self):
        """table selection changed"""
        if self.on_select:
            self.on_select(self.table.selected)
